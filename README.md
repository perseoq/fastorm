# Fastorm
fast-sqlite v2.366.1.aplha

# Manual de Uso del ORM para SQLite3

## Tabla de Contenidos
1. [Configuración Inicial](#configuración-inicial)
2. [Definición de Modelos](#definición-de-modelos)
3. [Operaciones CRUD](#operaciones-crud)
4. [Relaciones entre Modelos](#relaciones-entre-modelos)
5. [Consultas Avanzadas](#consultas-avanzadas)
6. [Transacciones](#transacciones)
7. [Ejemplos Complejos](#ejemplos-complejos)

---

## Configuración Inicial

### Requisitos
- Python 3.6+
- Módulo `sqlite3` (incluido en la librería estándar)

### Estructura básica
```python
from orm import Model, Column, ForeignKey
```

---

## Definición de Modelos

### Tipos de Columnas

| Tipo ORM     | Tipo SQLite | Descripción                          |
|--------------|------------|--------------------------------------|
| `Column`     | Varios     | Define una columna normal            |
| `ForeignKey` | INTEGER    | Define una relación con otro modelo  |

### Ejemplo de Modelo
```python
class User(Model):
    _table_name = 'users'
    
    id = Column('INTEGER', primary_key=True)
    name = Column('TEXT', nullable=False)
    email = Column('TEXT', unique=True)
    created_at = Column('TEXT')  # Fecha como string

class Post(Model):
    _table_name = 'posts'
    
    id = Column('INTEGER', primary_key=True)
    title = Column('TEXT', nullable=False)
    content = Column('TEXT')
    user_id = ForeignKey(User)  # Relación con User
    is_published = Column('INTEGER', default=0)
```

### Creación de Tablas
```python
User.create_table()
Post.create_table()
```

---

## Operaciones CRUD

### Operaciones Disponibles

| Método    | Descripción                           | Ejemplo                                      |
|-----------|---------------------------------------|----------------------------------------------|
| `save()`  | Crea o actualiza un registro         | `user.save()`                                |
| `delete()`| Elimina un registro                  | `user.delete()`                              |
| `query()` | Inicia una consulta                  | `User.query().where(...)`                    |

### Ejemplos CRUD

**Crear un registro:**
```python
new_user = User(name="Ana López", email="ana@example.com")
new_user.save()  # Asigna automáticamente el ID
```

**Actualizar un registro:**
```python
user = User.query().where("email = ?", "ana@example.com").first()
user.name = "Ana María López"
user.save()
```

**Eliminar un registro:**
```python
user = User.query().where("email = ?", "ana@example.com").first()
user.delete()
```

---

## Relaciones entre Modelos

### Tipos de Relaciones

| Método       | Tipo de Relación | Ejemplo                                      |
|--------------|------------------|----------------------------------------------|
| `belongs_to` | Muchos-a-uno     | `post.belongs_to(User)`                      |
| `has_many`   | Uno-a-muchos     | `user.has_many(Post)`                        |

### Ejemplo de Relaciones

**Relación belongs_to:**
```python
post = Post.query().first()
author = post.belongs_to(User)
print(f"El autor es: {author.name}")
```

**Relación has_many:**
```python
user = User.query().first()
posts = user.has_many(Post)
print(f"El usuario tiene {len(posts)} posts")
```

---

## Consultas Avanzadas

### Métodos del QueryBuilder

| Método       | Descripción                           | Ejemplo                                      |
|--------------|---------------------------------------|----------------------------------------------|
| `where()`    | Filtra resultados                    | `.where("age > ?", 18)`                      |
| `join()`     | Realiza JOINs                        | `.join("users", "posts.user_id = users.id")` |
| `order_by()` | Ordena resultados                    | `.order_by("name", "DESC")`                  |
| `limit()`    | Limita cantidad de resultados        | `.limit(10)`                                 |
| `count()`    | Cuenta registros                     | `.where("active = 1").count()`               |

### Ejemplos de Consultas

**Consulta con JOIN:**
```python
results = (Post.query()
          .select("posts.title", "users.name as author")
          .join("users", "posts.user_id = users.id")
          .all())

for post in results:
    print(f"{post.title} - {post.author}")
```

**Consulta con múltiples condiciones:**
```python
active_users = (User.query()
               .where("active = ?", 1)
               .where("email LIKE ?", "%@example.com")
               .order_by("created_at", "DESC")
               .limit(5)
               .all())
```

---

## Transacciones

### Manejo de Transacciones

```python
conn = Model.get_connection()
try:
    conn.execute("BEGIN TRANSACTION")
    
    # Operaciones múltiples
    user1 = User(name="User1", email="user1@example.com")
    user1.save()
    
    user2 = User(name="User2", email="user2@example.com")
    user2.save()
    
    conn.commit()
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
```

---

## Ejemplos Complejos

### Sistema de Blog con Comentarios

**Modelos:**
```python
class Comment(Model):
    _table_name = 'comments'
    
    id = Column('INTEGER', primary_key=True)
    content = Column('TEXT')
    post_id = ForeignKey(Post)
    user_id = ForeignKey(User)
    created_at = Column('TEXT')
```

**Consulta compleja:**
```python
# Obtener posts con sus comentarios y autores
posts_with_comments = (Post.query()
                      .select("posts.*", "users.name as author", 
                              "comments.content as comment", 
                              "comment_users.name as comment_author")
                      .join("users", "posts.user_id = users.id")
                      .left_join("comments", "posts.id = comments.post_id")
                      .left_join("users as comment_users", "comments.user_id = comment_users.id")
                      .order_by("posts.created_at", "DESC")
                      .all())

for post in posts_with_comments:
    print(f"\nPost: {post.title} (por {post.author})")
    if post.comment:
        print(f"- Comentario: {post.comment} (por {post.comment_author})")
```

### Cierre de Conexión
```python
Model.close_connection()
```

---

Este manual cubre todas las funcionalidades principales del ORM. Para casos más específicos, consulta los ejemplos proporcionados o extiende la funcionalidad según tus necesidades.
