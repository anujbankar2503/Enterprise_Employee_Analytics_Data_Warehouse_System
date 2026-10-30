from decimal import Decimal

import pandas as pd

from src.db_manager import DatabaseConnection, DatabaseError
from src.entities import Employee, Project, Review


def _to_df(rows):
    """List of dicts -> DataFrame, with Decimal columns converted to float."""
    df = pd.DataFrame(rows)
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df


class BaseManager(DatabaseConnection):
    """All managers inherit the singleton pool and the CRUD helpers."""

    def _warehouse_procedure(self):
        row = self.fetch_one(
            "SELECT ROUTINE_NAME FROM information_schema.routines "
            "WHERE ROUTINE_SCHEMA = 'hr_dw' AND ROUTINE_NAME IN "
            "('sp_run_full_etl', 'sp_etl_oltp_to_olap') "
            "ORDER BY FIELD(ROUTINE_NAME, 'sp_run_full_etl', 'sp_etl_oltp_to_olap') "
            "LIMIT 1")
        if row is None:
            raise DatabaseError("No compatible warehouse ETL procedure is installed")
        return f"hr_dw.{row['ROUTINE_NAME']}"

    def _sync_warehouse(self):
        self.call_procedure(self._warehouse_procedure())


class EmployeeManager(BaseManager):
    EDITABLE = {"department_id", "job_role", "job_level", "monthly_income", "work_location"}
    TRACKED = {"department_id", "job_role", "job_level", "monthly_income"}  # SCD Type 2

    def list_departments(self):
        return self.fetch_all(
            "SELECT department_id, department_name FROM hr_oltp.departments "
            "WHERE is_active = 1 ORDER BY department_name")

    def _next_employee_number(self):
        row = self.fetch_one(
            "SELECT COALESCE(MAX(CAST(SUBSTRING(employee_number, 4) AS UNSIGNED)), 0) + 1 AS n "
            "FROM hr_oltp.employees WHERE employee_number LIKE 'EMP%'")
        return f"EMP{int(row['n']):06d}"

    def add_employee(self, emp: Employee) -> int:
        """Insert into OLTP, then sync the warehouse (creates the first SCD2 row)."""
        emp.employee_number = self._next_employee_number()
        cols = ["department_id", "employee_number", "first_name", "last_name", "hire_date",
                "job_role", "job_level", "gender", "work_location", "monthly_income", "age",
                "marital_status", "education", "education_field", "business_travel",
                "distance_from_home", "overtime", "attrition_status",
                "total_working_years", "num_companies_worked"]
        values = (emp.department_id, emp.employee_number, emp.first_name, emp.last_name,
                  emp.hire_date, emp.job_role, emp.job_level, emp.gender, emp.work_location,
                  emp.monthly_income, emp.age, emp.marital_status, emp.education,
                  emp.education_field, emp.business_travel, emp.distance_from_home,
                  emp.overtime, "No", emp.total_working_years, emp.num_companies_worked)
        sql = (f"INSERT INTO hr_oltp.employees ({', '.join(cols)}) "
               f"VALUES ({', '.join(['%s'] * len(cols))})")
        emp.employee_id = self.execute(sql, values)
        self._sync_warehouse()
        return emp.employee_id

    def update_employee(self, employee_id, **changes):
        """Update OLTP; changes to tracked fields trigger an SCD Type 2 update."""
        bad = set(changes) - self.EDITABLE
        if bad or not changes:
            raise ValueError(f"Editable fields: {sorted(self.EDITABLE)}")
        if "monthly_income" in changes and changes["monthly_income"] < 0:
            raise ValueError("monthly_income must be >= 0")
        if self.get_employee(employee_id) is None:
            raise ValueError(f"Employee {employee_id} not found")
        sets = ", ".join(f"{k} = %s" for k in changes)
        self.execute(f"UPDATE hr_oltp.employees SET {sets} WHERE employee_id = %s",
                     (*changes.values(), employee_id))
        if self.TRACKED & set(changes):
            procedure = self._warehouse_procedure()
            if procedure.endswith("sp_run_full_etl"):
                self.call_procedure(procedure)
            else:
                current = self.get_employee(employee_id)
                self.call_procedure(
                    "hr_dw.sp_scd2_update_employee",
                    (employee_id, current["department_id"], current["job_role"],
                     current["job_level"], current["monthly_income"],
                     current["work_location"]),
                )
                self.call_procedure(procedure)

    def get_employee(self, employee_id):
        return self.fetch_one(
            "SELECT e.*, d.department_name FROM hr_oltp.employees e "
            "JOIN hr_oltp.departments d ON d.department_id = e.department_id "
            "WHERE e.employee_id = %s", (employee_id,))

    def search_employees(self, term, limit=50):
        like = f"{term}%"
        return self.fetch_all(
            "SELECT e.employee_id, e.employee_number, e.first_name, e.last_name, "
            "d.department_name, e.job_role, e.monthly_income "
            "FROM hr_oltp.employees e JOIN hr_oltp.departments d "
            "ON d.department_id = e.department_id "
            "WHERE e.employee_number = %s OR e.first_name LIKE %s OR e.last_name LIKE %s "
            "ORDER BY e.employee_id LIMIT %s", (term, like, like, limit))

    def get_history(self, employee_id):
        return self.fetch_all(
            "SELECT de.start_date, de.end_date, de.is_current, dep.department_name, "
            "de.job_role, de.job_level, de.monthly_income "
            "FROM hr_dw.dim_employee de "
            "JOIN hr_dw.dim_department dep ON dep.department_id = de.department_id "
            "WHERE de.employee_id = %s ORDER BY de.start_date", (employee_id,))


class ProjectManager(BaseManager):
    def create_project(self, project: Project) -> int:
        project.project_id = self.execute(
            "INSERT INTO hr_oltp.projects (project_code, project_name, project_status, "
            "project_start_date, planned_end_date) VALUES (%s, %s, %s, %s, %s)",
            (project.project_code, project.project_name, project.project_status,
             project.project_start_date, project.planned_end_date))
        self._sync_warehouse()
        return project.project_id

    def list_projects(self, status=None, limit=500):
        return self.fetch_all(
            "SELECT project_id, project_code, project_name, project_status, "
            "project_start_date, planned_end_date FROM hr_oltp.projects "
            "WHERE (%s IS NULL OR project_status = %s) ORDER BY project_id DESC LIMIT %s",
            (status, status, limit))

    def assign_employee(self, employee_id, project_id, start_date, end_date=None,
                        billable=False, allocation=50):
        if not (0 <= allocation <= 100):
            raise ValueError("allocation must be between 0 and 100")
        if end_date and end_date < start_date:
            raise ValueError("end_date cannot be before start_date")
        current = self.fetch_one(
            "SELECT COALESCE(SUM(allocation_percentage), 0) AS total "
            "FROM hr_oltp.assignments WHERE employee_id = %s "
            "AND (end_date IS NULL OR end_date >= CURDATE())", (employee_id,))
        assignment_id = self.execute(
            "INSERT INTO hr_oltp.assignments (employee_id, project_id, start_date, end_date, "
            "billable_flag, allocation_percentage) VALUES (%s, %s, %s, %s, %s, %s)",
            (employee_id, project_id, start_date, end_date, billable, allocation))
        total = float(current["total"]) + allocation
        return {"assignment_id": assignment_id, "total_allocation": total,
                "over_allocated": total > 100}


class ReviewManager(BaseManager):
    def submit_review(self, review: Review) -> int:
        review.review_id = self.execute(
            "INSERT INTO hr_oltp.reviews (reviewer_employee_id, employee_id, project_id, "
            "review_date, performance_rating, performance_score, review_status, comments) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (review.reviewer_employee_id, review.employee_id, review.project_id,
             review.review_date, review.performance_rating, review.performance_score,
             review.review_status, review.comments))
        self._sync_warehouse()
        return review.review_id

    def list_reviews(self, employee_id, limit=50):
        return self.fetch_all(
            "SELECT review_id, review_date, project_id, performance_rating, "
            "performance_score, review_status, comments FROM hr_oltp.reviews "
            "WHERE employee_id = %s ORDER BY review_date DESC LIMIT %s", (employee_id, limit))


class AnalyticsManager(BaseManager):
    """Runs analytical SQL against the star schema (hr_dw)."""

    ATTRITION_DIMENSIONS = {
        "Overtime": "overtime",
        "Job level": "job_level",
        "Business travel": "business_travel",
        "Marital status": "marital_status",
        "Job role": "job_role",
        "Experience band": (
            "CASE WHEN total_working_years < 5 THEN '0-4 yrs' "
            "WHEN total_working_years < 10 THEN '5-9 yrs' "
            "WHEN total_working_years < 20 THEN '10-19 yrs' ELSE '20+ yrs' END"),
    }

    def kpis(self):
        row = self.fetch_one(
            "SELECT "
            "(SELECT COUNT(*) FROM hr_dw.dim_employee WHERE is_current = 1) AS headcount, "
            "(SELECT ROUND(AVG(performance_score), 2) FROM hr_dw.fact_performance_reviews) AS avg_score, "
            "(SELECT ROUND(100 * AVG(attrition_status = 'Yes'), 2) FROM hr_dw.dim_employee "
            " WHERE is_current = 1) AS attrition_rate, "
            "(SELECT COUNT(*) FROM hr_dw.fact_performance_reviews) AS total_reviews")
        return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}

    def years(self):
        rows = self.fetch_all(
            "SELECT DISTINCT review_date_key DIV 10000 AS year "
            "FROM hr_dw.fact_performance_reviews ORDER BY year")
        return [r["year"] for r in rows]

    def yoy_trend(self, department=None):
        """Year-over-year average score, using LAG() for the change vs the previous year."""
        return _to_df(self.fetch_all(
            "WITH yearly AS ( "
            "  SELECT dd.year AS year, AVG(f.performance_score) AS avg_score, "
            "         AVG(f.performance_rating) AS avg_rating, COUNT(*) AS reviews "
            "  FROM hr_dw.fact_performance_reviews f "
            "  JOIN hr_dw.dim_date dd ON dd.date_key = f.review_date_key "
            "  JOIN hr_dw.dim_department dep ON dep.department_key = f.department_key "
            "  WHERE (%s IS NULL OR dep.department_name = %s) "
            "  GROUP BY dd.year) "
            "SELECT year, ROUND(avg_score, 2) AS avg_score, ROUND(avg_rating, 2) AS avg_rating, "
            "       reviews, ROUND(avg_score - LAG(avg_score) OVER (ORDER BY year), 2) AS change_vs_prev "
            "FROM yearly ORDER BY year", (department, department)))

    def top_performers(self, year=None, top_n=5, min_reviews=3):
        """Top employees per department using DENSE_RANK()."""
        return _to_df(self.fetch_all(
            "WITH emp_scores AS ( "
            "  SELECT de.employee_id, de.first_name, de.last_name, dep.department_name, "
            "         AVG(f.performance_score) AS avg_score, COUNT(*) AS reviews "
            "  FROM hr_dw.fact_performance_reviews f "
            "  JOIN hr_dw.dim_employee de ON de.employee_key = f.employee_key "
            "  JOIN hr_dw.dim_department dep ON dep.department_key = f.department_key "
            "  JOIN hr_dw.dim_date dd ON dd.date_key = f.review_date_key "
            "  WHERE (%s IS NULL OR dd.year = %s) "
            "  GROUP BY de.employee_id, de.first_name, de.last_name, dep.department_name "
            "  HAVING COUNT(*) >= %s), "
            "ranked AS ( "
            "  SELECT *, DENSE_RANK() OVER (PARTITION BY department_name "
            "                               ORDER BY avg_score DESC) AS dept_rank "
            "  FROM emp_scores) "
            "SELECT department_name, dept_rank, employee_id, "
            "       CONCAT(first_name, ' ', last_name) AS employee, "
            "       ROUND(avg_score, 2) AS avg_score, reviews "
            "FROM ranked WHERE dept_rank <= %s "
            "ORDER BY department_name, dept_rank, employee_id",
            (year, year, min_reviews, top_n)))

    def department_performance(self, year=None):
        return _to_df(self.fetch_all(
            "SELECT dep.department_name, ROUND(AVG(f.performance_score), 2) AS avg_score, "
            "       COUNT(*) AS reviews "
            "FROM hr_dw.fact_performance_reviews f "
            "JOIN hr_dw.dim_department dep ON dep.department_key = f.department_key "
            "JOIN hr_dw.dim_date dd ON dd.date_key = f.review_date_key "
            "WHERE (%s IS NULL OR dd.year = %s) "
            "GROUP BY dep.department_name ORDER BY avg_score DESC", (year, year)))

    def attrition_by(self, dimension="Overtime"):
        expr = self.ATTRITION_DIMENSIONS.get(dimension)
        if expr is None:
            raise ValueError(f"Unknown dimension: {dimension}")
        return _to_df(self.fetch_all(
            f"SELECT {expr} AS grp, COUNT(*) AS headcount, "
            f"SUM(attrition_status = 'Yes') AS attrited, "
            f"ROUND(100 * AVG(attrition_status = 'Yes'), 2) AS attrition_rate "
            f"FROM hr_dw.dim_employee WHERE is_current = 1 "
            f"GROUP BY grp ORDER BY attrition_rate DESC"))

    def project_bottlenecks(self, limit=20):
        """Returns (overdue active projects, over-allocated employees)."""
        overdue = _to_df(self.fetch_all(
            "SELECT project_code, project_name, planned_end_date, "
            "       DATEDIFF(CURDATE(), planned_end_date) AS days_overdue "
            "FROM hr_dw.dim_project "
            "WHERE project_key <> -1 AND project_status = 'Active' "
            "  AND planned_end_date < CURDATE() "
            "ORDER BY days_overdue DESC LIMIT %s", (limit,)))
        overloaded = _to_df(self.fetch_all(
            "SELECT e.employee_id, CONCAT(e.first_name, ' ', e.last_name) AS employee, "
            "       d.department_name, COUNT(*) AS active_assignments, "
            "       SUM(a.allocation_percentage) AS total_allocation "
            "FROM hr_oltp.assignments a "
            "JOIN hr_oltp.employees e ON e.employee_id = a.employee_id "
            "JOIN hr_oltp.departments d ON d.department_id = e.department_id "
            "WHERE a.end_date IS NULL OR a.end_date >= CURDATE() "
            "GROUP BY e.employee_id, e.first_name, e.last_name, d.department_name "
            "HAVING SUM(a.allocation_percentage) > 100 "
            "ORDER BY total_allocation DESC LIMIT %s", (limit,)))
        return overdue, overloaded