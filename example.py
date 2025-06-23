# Definición de modelos con relaciones avanzadas
class Department(Model):
    _table_name = 'departments'
    
    id = Column('INTEGER', primary_key=True)
    name = Column('TEXT', nullable=False, unique=True)
    budget = Column('REAL')

class Employee(Model):
    _table_name = 'employees'
    
    id = Column('INTEGER', primary_key=True)
    name = Column('TEXT', nullable=False)
    email = Column('TEXT', unique=True)
    salary = Column('REAL')
    department_id = ForeignKey(Department)

class Project(Model):
    _table_name = 'projects'
    
    id = Column('INTEGER', primary_key=True)
    name = Column('TEXT', nullable=False)
    deadline = Column('TEXT')

class EmployeeProject(Model):
    _table_name = 'employee_projects'
    
    id = Column('INTEGER', primary_key=True)
    employee_id = ForeignKey(Employee)
    project_id = ForeignKey(Project)
    hours = Column('INTEGER')

# Crear todas las tablas
Department.create_table()
Employee.create_table()
Project.create_table()
EmployeeProject.create_table()

# Insertar datos de ejemplo
it = Department(name="IT", budget=100000)
it.save()

hr = Department(name="HR", budget=80000)
hr.save()

employees = [
    Employee(name="Carlos Ruiz", email="carlos@example.com", salary=45000, department_id=it.id),
    Employee(name="Ana López", email="ana@example.com", salary=42000, department_id=it.id),
    Employee(name="Pedro Martínez", email="pedro@example.com", salary=38000, department_id=hr.id)
]

for emp in employees:
    emp.save()

projects = [
    Project(name="Sistema de Gestión", deadline="2023-12-31"),
    Project(name="Portal Web", deadline="2023-10-15"),
    Project(name="App Móvil", deadline="2024-02-28")
]

for proj in projects:
    proj.save()

# Asignar empleados a proyectos
assignments = [
    EmployeeProject(employee_id=employees[0].id, project_id=projects[0].id, hours=20),
    EmployeeProject(employee_id=employees[0].id, project_id=projects[1].id, hours=15),
    EmployeeProject(employee_id=employees[1].id, project_id=projects[0].id, hours=30),
    EmployeeProject(employee_id=employees[2].id, project_id=projects[2].id, hours=25)
]

for assign in assignments:
    assign.save()

# Consultas avanzadas
print("\n=== Todos los empleados del departamento IT ===")
it_employees = Employee.query().where("department_id = ?", it.id).all()
for emp in it_employees:
    print(f"{emp.name} - {emp.email}")

print("\n=== Proyectos de Carlos ===")
carlos = Employee.query().where("email = ?", "carlos@example.com").first()
if carlos:
    carlos_projects = (Project.query()
                      .select("projects.name", "projects.deadline", "employee_projects.hours")
                      .join("employee_projects", "projects.id = employee_projects.project_id")
                      .where("employee_projects.employee_id = ?", carlos.id)
                      .all())
    
    for p in carlos_projects:
        print(f"{p.name} (hasta {p.deadline}) - {p.hours} horas")

print("\n=== Empleados con sus departamentos (JOIN) ===")
employees_with_dept = (Employee.query()
                      .select("employees.name", "departments.name as department", "employees.salary")
                      .join("departments", "employees.department_id = departments.id")
                      .order_by("employees.salary", "DESC")
                      .all())

for emp in employees_with_dept:
    print(f"{emp.name} - {emp.department} - ${emp.salary:,.2f}")

print("\n=== Relaciones muchos-a-muchos ===")
project = Project.query().where("name = ?", "Sistema de Gestión").first()
if project:
    project_employees = (Employee.query()
                        .select("employees.name", "employee_projects.hours")
                        .join("employee_projects", "employees.id = employee_projects.employee_id")
                        .where("employee_projects.project_id = ?", project.id)
                        .all())
    
    print(f"\nEmpleados trabajando en '{project.name}':")
    for emp in project_employees:
        print(f"- {emp.name} ({emp.hours} horas)")

# Cerrar conexión al finalizar
Model.close_connection()
