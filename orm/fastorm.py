import sqlite3
from typing import List, Dict, Union, Optional, Type, TypeVar, Any, Tuple

T = TypeVar('T', bound='Model')

class ForeignKey:
    def __init__(self, model: Type['Model'], nullable: bool = False):
        self.model = model
        self.nullable = nullable

    @property
    def sql_type(self):
        return "INTEGER"

class Column:
    def __init__(self, sql_type: str, primary_key: bool = False, nullable: bool = True, unique: bool = False):
        self.sql_type = sql_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.unique = unique

class Model:
    _table_name = None
    
    def __init__(self, **kwargs):
        self._data = kwargs
        self._modified = set()
        self._relations = {}
        
    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        elif name in self._relations:
            return self._relations[name]
        raise AttributeError(f"'{self.__class__.__name__}' no tiene el atributo '{name}'")
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in self._relations:
            self._relations[name] = value
        else:
            self._data[name] = value
            self._modified.add(name)
    
    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        if not hasattr(cls, '_conn'):
            cls._conn = sqlite3.connect('database.db', detect_types=sqlite3.PARSE_DECLTYPES)
            cls._conn.row_factory = sqlite3.Row
            cls._conn.execute("PRAGMA foreign_keys = ON")
        return cls._conn
    
    @classmethod
    def close_connection(cls):
        if hasattr(cls, '_conn'):
            cls._conn.close()
            delattr(cls, '_conn')
    
    @classmethod
    def create_table(cls):
        if not cls._table_name:
            raise ValueError("Nombre de tabla no definido")
            
        columns = []
        primary_keys = []
        foreign_keys = []
        unique_constraints = []
        
        for name, field in cls.__dict__.items():
            if isinstance(field, Column):
                nullable = " NULL" if field.nullable else " NOT NULL"
                unique = " UNIQUE" if field.unique else ""
                columns.append(f"{name} {field.sql_type}{nullable}{unique}")
                if field.primary_key:
                    primary_keys.append(name)
                if field.unique and not field.primary_key:
                    unique_constraints.append(name)
            elif isinstance(field, ForeignKey):
                nullable = " NULL" if field.nullable else " NOT NULL"
                columns.append(f"{name} {field.sql_type}{nullable}")
                foreign_keys.append((name, field.model))
        
        pk_clause = f", PRIMARY KEY ({', '.join(primary_keys)})" if primary_keys else ""
        
        fk_clauses = []
        for fk_name, model in foreign_keys:
            fk_clauses.append(
                f", FOREIGN KEY({fk_name}) REFERENCES {model._table_name}({model.get_primary_key()}) "
                f"ON DELETE {'SET NULL' if field.nullable else 'CASCADE'}"
            )
        
        unique_clauses = [
            f", UNIQUE({col})" for col in unique_constraints
        ]
        
        sql = f"CREATE TABLE IF NOT EXISTS {cls._table_name} ({', '.join(columns)}{pk_clause}{''.join(fk_clauses)}{''.join(unique_clauses)})"
        
        conn = cls.get_connection()
        conn.execute(sql)
        conn.commit()
    
    @classmethod
    def get_primary_key(cls) -> str:
        for name, field in cls.__dict__.items():
            if isinstance(field, Column) and field.primary_key:
                return name
        return 'id'
    
    def save(self):
        if not self._table_name:
            raise ValueError("Nombre de tabla no definido")
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        pk = self.__class__.get_primary_key()
        pk_value = self._data.get(pk)
        
        if pk_value is not None:
            # Actualización
            set_clause = ', '.join([f"{col} = ?" for col in self._modified])
            values = [self._data[col] for col in self._modified]
            values.append(pk_value)
            
            sql = f"UPDATE {self._table_name} SET {set_clause} WHERE {pk} = ?"
            cursor.execute(sql, values)
        else:
            # Inserción
            columns = [col for col in self._data.keys()]
            placeholders = ', '.join(['?'] * len(columns))
            values = [self._data[col] for col in columns]
            
            sql = f"INSERT INTO {self._table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(sql, values)
            
            if pk:
                self._data[pk] = cursor.lastrowid
        
        conn.commit()
        self._modified.clear()
    
    def delete(self):
        if not self._table_name:
            raise ValueError("Nombre de tabla no definido")
            
        pk = self.__class__.get_primary_key()
        pk_value = self._data.get(pk)
        
        if pk_value is None:
            raise ValueError("No se puede eliminar un registro sin clave primaria")
            
        conn = self.get_connection()
        sql = f"DELETE FROM {self._table_name} WHERE {pk} = ?"
        conn.execute(sql, (pk_value,))
        conn.commit()
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> T:
        instance = cls()
        instance._data = dict(row)
        instance._modified.clear()
        return instance
    
    def belongs_to(self, model_class: Type[T], foreign_key: str = None) -> Optional[T]:
        if foreign_key is None:
            model_name = model_class._table_name.lower()
            foreign_key = f"{model_name}_id"
        
        if foreign_key not in self._data:
            return None
            
        return model_class.query().where(f"{model_class.get_primary_key()} = ?", self._data[foreign_key]).first()
    
    def has_many(self, model_class: Type[T], foreign_key: str = None) -> List[T]:
        if foreign_key is None:
            my_name = self._table_name.lower()
            foreign_key = f"{my_name}_id"
        
        return model_class.query().where(f"{foreign_key} = ?", self._data[self.get_primary_key()]).all()
    
    @classmethod
    def query(cls) -> 'QueryBuilder':
        return QueryBuilder(cls)

class QueryBuilder:
    def __init__(self, model_class: Type[Model]):
        self.model_class = model_class
        self._select = '*'
        self._where = []
        self._params = []
        self._joins = []
        self._limit = None
        self._offset = None
        self._order_by = None
        self._group_by = None
        self._having = None
    
    def select(self, *columns: str) -> 'QueryBuilder':
        self._select = ', '.join(columns) if columns else '*'
        return self
    
    def where(self, condition: str, *params) -> 'QueryBuilder':
        self._where.append(condition)
        self._params.extend(params)
        return self
    
    def join(self, table: str, on: str, join_type: str = 'INNER') -> 'QueryBuilder':
        self._joins.append(f"{join_type} JOIN {table} ON {on}")
        return self
    
    def left_join(self, table: str, on: str) -> 'QueryBuilder':
        return self.join(table, on, 'LEFT')
    
    def right_join(self, table: str, on: str) -> 'QueryBuilder':
        return self.join(table, on, 'RIGHT')
    
    def limit(self, limit: int) -> 'QueryBuilder':
        self._limit = limit
        return self
    
    def offset(self, offset: int) -> 'QueryBuilder':
        self._offset = offset
        return self
    
    def order_by(self, column: str, direction: str = 'ASC') -> 'QueryBuilder':
        self._order_by = f"{column} {direction}"
        return self
    
    def group_by(self, column: str) -> 'QueryBuilder':
        self._group_by = column
        return self
    
    def having(self, condition: str, *params) -> 'QueryBuilder':
        self._having = condition
        self._params.extend(params)
        return self
    
    def _build_query(self) -> Tuple[str, List[Any]]:
        sql = f"SELECT {self._select} FROM {self.model_class._table_name}"
        
        if self._joins:
            sql += " " + " ".join(self._joins)
        
        if self._where:
            sql += " WHERE " + " AND ".join(self._where)
        
        if self._group_by:
            sql += f" GROUP BY {self._group_by}"
        
        if self._having:
            sql += f" HAVING {self._having}"
        
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        
        if self._offset is not None:
            sql += f" OFFSET {self._offset}"
        
        return sql, self._params
    
    def all(self) -> List[Model]:
        sql, params = self._build_query()
        conn = self.model_class.get_connection()
        cursor = conn.execute(sql, params)
        
        return [self.model_class.from_row(row) for row in cursor]
    
    def first(self) -> Optional[Model]:
        self._limit = 1
        results = self.all()
        return results[0] if results else None
    
    def count(self) -> int:
        sql = f"SELECT COUNT(*) FROM {self.model_class._table_name}"
        params = []
        
        if self._where:
            sql += " WHERE " + " AND ".join(self._where)
            params = self._params[:len(self._where)]
        
        conn = self.model_class.get_connection()
        cursor = conn.execute(sql, params)
        return cursor.fetchone()[0]
    
    def exists(self) -> bool:
        return self.count() > 0
