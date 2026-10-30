import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import date

import pandas as pd
import streamlit as st

from app.helpers import ROLES, display_columns, employee_picker
from app.styles import apply_styles, page_header
from src.db_manager import DatabaseError
from src.entities import Employee
from src.managers import EmployeeManager

st.set_page_config(page_title="Employees", layout="wide")
apply_styles()
page_header("People directory", "Employees", "Onboard people, keep records current, and review career history.")

em = EmployeeManager()
try:
    departments = em.list_departments()
except DatabaseError as e:
    st.error(f"Database connection problem: {e}")
    st.stop()
dept_names = {d["department_id"]: d["department_name"] for d in departments}
dept_ids = list(dept_names)

tab_add, tab_edit = st.tabs(["Onboard employee", "Search, edit and history"])

# ---------------------------------------------------------------- onboard
with tab_add:
    with st.form("onboard_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        first = c1.text_input("First name")
        last = c2.text_input("Last name")
        dept_id = c1.selectbox("Department", dept_ids, format_func=dept_names.get)
        role = c2.selectbox("Job role", ROLES)
        level = c1.number_input("Job level (1-5)", 1, 5, 1)
        income = c2.number_input("Monthly income", min_value=0.0, value=5000.0, step=500.0)
        hire = c1.date_input("Hire date", value=date.today())
        age = c2.number_input("Age", 18, 100, 30)
        gender = c1.selectbox("Gender", ["Male", "Female", "Other"])
        location = c2.selectbox("Work location", ["Pune", "Mumbai", "Bengaluru", "Hyderabad"])
        marital = c1.selectbox("Marital status", ["Single", "Married", "Divorced"])
        education = c2.number_input("Education level (1-5)", 1, 5, 3)
        edu_field = c1.selectbox("Education field", [
            "Life Sciences", "Medical", "Marketing", "Technical Degree",
            "Human Resources", "Other"])
        travel = c2.selectbox("Business travel",
                              ["Non-Travel", "Travel_Rarely", "Travel_Frequently"])
        distance = c1.number_input("Distance from home (km)", 0, 100, 5)
        overtime = c2.selectbox("Overtime", ["No", "Yes"])
        years = c1.number_input("Total working years", 0, 60, 0)
        companies = c2.number_input("Companies worked", 0, 30, 0)
        submitted = st.form_submit_button("Onboard employee")

    if submitted:
        try:
            emp = Employee(
                first_name=first, last_name=last, department_id=dept_id, hire_date=hire,
                job_role=role, monthly_income=income, job_level=level, gender=gender,
                work_location=location, age=age, marital_status=marital,
                education=education, education_field=edu_field, business_travel=travel,
                distance_from_home=distance, overtime=overtime,
                total_working_years=years, num_companies_worked=companies)
            with st.spinner("Saving employee details..."):
                new_id = em.add_employee(emp)
            st.cache_data.clear()
            st.success(f"Employee {emp.full_name} created: {emp.employee_number} "
                       f"(record {new_id}).")
        except (ValueError, DatabaseError) as e:
            st.error(f"Could not save: {e}")

# ------------------------------------------------------------ edit/history
with tab_edit:
    emp_id = employee_picker("edit")
    if emp_id:
        try:
            cur = em.get_employee(emp_id)
        except DatabaseError as error:
            st.error(f"Database connection problem: {error}")
            st.stop()
        st.subheader(f"{cur['first_name']} {cur['last_name']} - {cur['employee_number']}")

        roles = ROLES if cur["job_role"] in ROLES else [cur["job_role"], *ROLES]
        current_vals = {
            "department_id": cur["department_id"],
            "job_role": cur["job_role"],
            "job_level": int(cur["job_level"] or 1),
            "monthly_income": float(cur["monthly_income"]),
        }

        with st.form(f"edit_form_{emp_id}"):
            c1, c2 = st.columns(2)
            new_dept = c1.selectbox("Department", dept_ids,
                                    index=dept_ids.index(cur["department_id"]),
                                    format_func=dept_names.get)
            new_role = c2.selectbox("Job role", roles, index=roles.index(cur["job_role"]))
            new_level = c1.number_input("Job level (1-5)", 1, 5, current_vals["job_level"])
            new_income = c2.number_input("Monthly income", min_value=0.0,
                                         value=current_vals["monthly_income"], step=500.0)
            save = st.form_submit_button("Save changes")

        if save:
            candidate = {"department_id": new_dept, "job_role": new_role,
                         "job_level": int(new_level), "monthly_income": float(new_income)}
            changes = {k: v for k, v in candidate.items() if v != current_vals[k]}
            if not changes:
                st.info("Nothing changed.")
            else:
                try:
                    with st.spinner("Updating employee details..."):
                        em.update_employee(emp_id, **changes)
                    st.cache_data.clear()
                    st.success("Saved. Employment history has been updated.")
                except (ValueError, DatabaseError) as e:
                    st.error(f"Could not save: {e}")

        st.markdown("#### Employment history")
        try:
            hist = pd.DataFrame(em.get_history(emp_id))
        except DatabaseError as error:
            st.error(f"Database connection problem: {error}")
            st.stop()
        if not hist.empty:
            hist["monthly_income"] = hist["monthly_income"].astype(float)
            hist["is_current"] = hist["is_current"].astype(bool)
            st.dataframe(display_columns(hist), hide_index=True)