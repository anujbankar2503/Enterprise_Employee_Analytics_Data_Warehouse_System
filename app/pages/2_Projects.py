import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from app.helpers import display_columns, employee_picker
from app.styles import apply_styles, page_header
from src.db_manager import DatabaseError
from src.entities import Project
from src.managers import ProjectManager

st.set_page_config(page_title="Projects", layout="wide")
apply_styles()
page_header("Delivery workspace", "Projects and assignments", "Plan active work and keep team capacity visible.")

pm = ProjectManager()
tab_create, tab_assign, tab_list = st.tabs(["Create project", "Assign employee", "All projects"])

with tab_create:
    with st.form("project_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        code = c1.text_input("Project code (e.g. PRJ0999)")
        name = c2.text_input("Project name")
        start = c1.date_input("Start date", value=date.today())
        end = c2.date_input("Planned end date", value=date.today() + timedelta(days=180))
        status = c1.selectbox("Status", ["Planned", "Active"])
        submitted = st.form_submit_button("Create project")
    if submitted:
        try:
            project = Project(project_code=code, project_name=name, project_start_date=start,
                              planned_end_date=end, project_status=status)
            with st.spinner("Saving project details..."):
                pid = pm.create_project(project)
            st.cache_data.clear()
            st.success(f"Project {project.project_code} created (record {pid}).")
        except (ValueError, DatabaseError) as e:
            st.error(f"Could not save: {e}")

with tab_assign:
    try:
        open_projects = [p for p in pm.list_projects()
                         if p["project_status"] in ("Planned", "Active")]
    except DatabaseError as error:
        st.error(f"Database connection problem: {error}")
        st.stop()
    options = {p["project_id"]: f"{p['project_code']} - {p['project_name']} ({p['project_status']})"
               for p in open_projects}
    emp_id = employee_picker("assign")
    if emp_id and options:
        with st.form("assign_form"):
            project_id = st.selectbox("Project", list(options), format_func=options.get)
            c1, c2 = st.columns(2)
            start = c1.date_input("Assignment start", value=date.today())
            end = c2.date_input("Assignment end (optional)", value=None)
            billable = c1.checkbox("Billable")
            allocation = c2.slider("Allocation %", 5, 100, 50, step=5)
            submitted = st.form_submit_button("Assign employee")
        if submitted:
            try:
                result = pm.assign_employee(emp_id, project_id, start, end, billable, allocation)
                st.success(f"Assignment {result['assignment_id']} created.")
                if result["over_allocated"]:
                    st.warning(f"This employee is now allocated {result['total_allocation']:.0f}% "
                               "across active projects (over 100%).")
            except (ValueError, DatabaseError) as e:
                st.error(f"Could not save: {e}")

with tab_list:
    status_filter = st.selectbox("Status", ["All", "Planned", "Active", "Completed", "Cancelled"])
    try:
        rows = pm.list_projects(None if status_filter == "All" else status_filter)
    except DatabaseError as error:
        st.error(f"Database connection problem: {error}")
        st.stop()
    st.dataframe(display_columns(pd.DataFrame(rows)), hide_index=True)