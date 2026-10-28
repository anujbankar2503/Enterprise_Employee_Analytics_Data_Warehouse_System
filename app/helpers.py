import streamlit as st

from src.managers import EmployeeManager

ROLES = [
    "Sales Executive", "Research Scientist", "Laboratory Technician",
    "Manufacturing Director", "Healthcare Representative", "Manager",
    "Sales Representative", "Research Director", "Human Resources",
]


def employee_picker(key):
    """Search box + dropdown. Returns the selected employee_id or None."""
    term = st.text_input(
        "Find employee (employee number like EMP000123, or first/last name)",
        key=f"{key}_term")
    if not term.strip():
        st.info("Type an employee number or a name to search.")
        return None
    rows = EmployeeManager().search_employees(term.strip())
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