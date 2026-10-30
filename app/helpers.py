import pandas as pd
import streamlit as st

from src.db_manager import DatabaseError
from src.managers import EmployeeManager

ROLES = [
    "Sales Executive", "Research Scientist", "Laboratory Technician",
    "Manufacturing Director", "Healthcare Representative", "Manager",
    "Sales Representative", "Research Director", "Human Resources",
]


DISPLAY_COLUMN_NAMES = {
    "employee_key": "History record",
    "employee_id": "Employee ID",
    "employee_number": "Employee number",
    "department_id": "Department ID",
    "department_name": "Department",
    "first_name": "First name",
    "last_name": "Last name",
    "job_role": "Job role",
    "job_level": "Job level",
    "monthly_income": "Monthly income",
    "start_date": "Start time",
    "end_date": "End time",
    "is_current": "Current",
    "project_id": "Project ID",
    "project_code": "Project code",
    "project_name": "Project name",
    "project_status": "Status",
    "project_start_date": "Start date",
    "planned_end_date": "Planned end date",
    "actual_end_date": "Actual end date",
    "assignment_id": "Assignment ID",
    "billable_flag": "Billable",
    "allocation_percentage": "Allocation %",
    "review_id": "Review ID",
    "review_date": "Review date",
    "performance_rating": "Rating",
    "performance_score": "Score",
    "review_status": "Review status",
    "comments": "Comments",
    "year": "Year",
    "avg_score": "Average score",
    "change_vs_prev": "Change from previous year",
    "review_count": "Reviews",
    "dept_rank": "Department rank",
    "grp": "Group",
    "attrition_rate": "Attrition rate",
    "days_overdue": "Days overdue",
    "employee": "Employee",
    "total_allocation": "Total allocation %",
}


def display_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a display copy with plain labels for HR users."""
    return frame.rename(columns=DISPLAY_COLUMN_NAMES)


def employee_picker(key):
    """Search box + dropdown. Returns the selected employee_id or None."""
    term = st.text_input(
        "Find employee (employee number like EMP000123, or first/last name)",
        key=f"{key}_term")
    if not term.strip():
        st.info("Type an employee number or a name to search.")
        return None
    try:
        rows = EmployeeManager().search_employees(term.strip())
    except DatabaseError as error:
        st.error(f"Database connection problem: {error}")
        return None
    if not rows:
        st.warning("No employees found.")
        return None
    options = {
        r["employee_id"]: (f"{r['employee_number']} - {r['first_name']} {r['last_name']} "
                           f"({r['department_name']}, {r['job_role']})")
        for r in rows
    }
    return st.selectbox("Select employee", list(options),
                        format_func=options.get, key=f"{key}_select")