import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import date

import pandas as pd
import streamlit as st

from app.helpers import display_columns, employee_picker
from src.db_manager import DatabaseError
from src.entities import Review
from src.managers import ProjectManager, ReviewManager

st.set_page_config(page_title="Reviews", layout="wide")
st.title("Performance reviews")

rm, pm = ReviewManager(), ProjectManager()
try:
    projects = pm.list_projects()
except DatabaseError as error:
    st.error(f"Database connection problem: {error}")
    st.stop()
options = {None: "No project"}
options.update({p["project_id"]: f"{p['project_code']} - {p['project_name']}" for p in projects})

emp_id = employee_picker("review")
if emp_id:
    with st.form("review_form", clear_on_submit=True):
        project_id = st.selectbox("Project (optional)", list(options), format_func=options.get)
        c1, c2 = st.columns(2)
        review_date = c1.date_input("Review date", value=date.today())
        status = c2.selectbox("Status", ["Completed", "Pending"])
        rating = c1.slider("Performance rating (1-5)", 1, 5, 3)
        score = c2.number_input("Performance score (0-100)", 0.0, 100.0, 75.0, step=0.5)
        comments = st.text_area("Comments (optional)")
        submitted = st.form_submit_button("Submit review")

    if submitted:
        try:
            review = Review(employee_id=emp_id, review_date=review_date,
                            performance_rating=rating, performance_score=score,
                            project_id=project_id, review_status=status,
                            comments=comments.strip() or None)
            with st.spinner("Saving performance review..."):
                rid = rm.submit_review(review)
            st.cache_data.clear()
            st.success(f"Review {rid} saved successfully.")
        except (ValueError, DatabaseError) as e:
            st.error(f"Could not save: {e}")

    st.markdown("#### Recent reviews for this employee")
    recent = pd.DataFrame(rm.list_reviews(emp_id))
    if recent.empty:
        st.caption("No reviews yet.")
    else:
        recent["performance_score"] = recent["performance_score"].astype(float)
        st.dataframe(
            display_columns(recent),
            column_config={
                "Comments": st.column_config.TextColumn("Comments", width="large"),
            },
            hide_index=True,
        )