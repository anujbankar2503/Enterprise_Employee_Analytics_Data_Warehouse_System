from datetime import date

from src.db_manager import DatabaseConnection
from src.entities import Employee
from src.managers import AnalyticsManager, EmployeeManager

print("Singleton:", DatabaseConnection() is DatabaseConnection(),
      "| EmployeeManager:", EmployeeManager() is EmployeeManager())

em, an = EmployeeManager(), AnalyticsManager()
depts = em.list_departments()
print(depts)
print(an.kpis())
print(an.years())
print(an.yoy_trend())
print(an.top_performers(top_n=3))
print(an.department_performance())
print(an.attrition_by("Overtime"))
overdue, overloaded = an.project_bottlenecks()
print("Overdue projects:", len(overdue), "| Over-allocated employees:", len(overloaded))

# Write test: onboard an employee, change their department, check the SCD2 history
emp = Employee("Test", "Backend", depts[0]["department_id"], date.today(),
               "Sales Executive", 5000)
new_id = em.add_employee(emp)
print("New employee:", new_id, emp.employee_number)
print(em.get_history(new_id))          # expect 1 row
em.update_employee(new_id, department_id=depts[1]["department_id"])
print(em.get_history(new_id))          # expect 2 rows: old expired, new current