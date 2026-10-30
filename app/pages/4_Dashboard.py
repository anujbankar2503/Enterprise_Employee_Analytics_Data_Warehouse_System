import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import plotly.express as px
import streamlit as st

from app.helpers import display_columns
from app.styles import apply_styles, page_header
from src.db_manager import DatabaseError
from src.managers import AnalyticsManager, EmployeeManager

st.set_page_config(page_title="Analytics Dashboard", layout="wide")
apply_styles()
page_header("Workforce intelligence", "Analytics dashboard", "Signals for performance, retention, and project health.")

an = AnalyticsManager()


@st.cache_data(ttl=300)
def c_kpis(): return an.kpis()
@st.cache_data(ttl=300)
def c_years(): return an.years()
@st.cache_data(ttl=300)
def c_departments(): return [d["department_name"] for d in EmployeeManager().list_departments()]
@st.cache_data(ttl=300)
def c_yoy(dept): return an.yoy_trend(dept)
@st.cache_data(ttl=300)
def c_dept_perf(year): return an.department_performance(year)
@st.cache_data(ttl=300)
def c_top(year, top_n, min_reviews): return an.top_performers(year, top_n, min_reviews)
@st.cache_data(ttl=300)
def c_attrition(dim): return an.attrition_by(dim)
@st.cache_data(ttl=300)
def c_bottlenecks(): return an.project_bottlenecks()


def db_call(function, *args):
    try:
        return function(*args)
    except DatabaseError as error:
        st.error(f"Database connection problem: {error}")
        return None


try:
    kpis, years, departments = c_kpis(), c_years(), c_departments()
except DatabaseError as e:
    st.error(f"Database connection problem: {e}")
    st.stop()

st.sidebar.header("Filters")
year_choice = st.sidebar.selectbox("Year", ["All", *years])
dept_choice = st.sidebar.selectbox("Department", ["All", *departments])
top_n = st.sidebar.slider("Top N per department", 3, 10, 5)
min_reviews = st.sidebar.slider("Minimum reviews to qualify", 1, 10, 3)
year = None if year_choice == "All" else int(year_choice)
dept = None if dept_choice == "All" else dept_choice

c1, c2, c3, c4 = st.columns(4)
c1.metric("Current headcount", f"{kpis['headcount']:,}")
c2.metric("Average review score", f"{(kpis['avg_score'] or 0):.2f}")
c3.metric("Attrition rate", f"{(kpis['attrition_rate'] or 0):.1f}%")
c4.metric("Total reviews", f"{kpis['total_reviews']:,}")

tab_trend, tab_top, tab_attr, tab_proj = st.tabs(
    ["Performance trends", "Top performers", "Attrition risk", "Project bottlenecks"])

with tab_trend:
    yoy = db_call(c_yoy, dept)
    if yoy is None:
        st.stop()
    if yoy.empty:
        st.info("No data for this selection.")
    else:
        left, right = st.columns(2)
        fig = px.line(yoy, x="year", y="avg_score", markers=True,
                      title="Year-over-year average score")
        fig.update_xaxes(dtick=1)
        left.plotly_chart(fig)
        fig = px.bar(yoy, x="year", y="change_vs_prev", text="change_vs_prev",
                 title="Change from previous year")
        fig.update_xaxes(dtick=1)
        right.plotly_chart(fig)
        st.dataframe(display_columns(yoy), hide_index=True)
    perf = db_call(c_dept_perf, year)
    if perf is None:
        st.stop()
    fig = px.bar(perf, x="department_name", y="avg_score", text="avg_score",
                 title="Average score by department")
    st.plotly_chart(fig)

with tab_top:
    top = db_call(c_top, year, top_n, min_reviews)
    if top is None:
        st.stop()
    if dept:
        top = top[top["department_name"] == dept]
    if top.empty:
        st.info("No employees meet the criteria. Try lowering the minimum reviews.")
    else:
        fig = px.bar(top, x="avg_score", y="employee", color="department_name",
                     orientation="h", text="dept_rank",
                     title="Top performers by department")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig)
        st.dataframe(display_columns(top), hide_index=True)

with tab_attr:
    dimension = st.selectbox("Break attrition down by", list(AnalyticsManager.ATTRITION_DIMENSIONS))
    attr = db_call(c_attrition, dimension)
    if attr is None:
        st.stop()
    attr["grp"] = attr["grp"].astype(str)
    fig = px.bar(attr, x="grp", y="attrition_rate", text="attrition_rate",
                 title=f"Attrition rate by {dimension.lower()} (%)",
                 labels={"grp": dimension, "attrition_rate": "Attrition rate %"})
    fig.add_hline(y=kpis["attrition_rate"], line_dash="dash", annotation_text="Overall")
    st.plotly_chart(fig)
    st.dataframe(display_columns(attr), hide_index=True)

with tab_proj:
    bottlenecks = db_call(c_bottlenecks)
    if bottlenecks is None:
        st.stop()
    overdue, overloaded = bottlenecks
    left, right = st.columns(2)
    with left:
        st.subheader("Overdue active projects")
        if overdue.empty:
            st.info("No overdue active projects.")
        else:
            fig = px.bar(overdue, x="project_code", y="days_overdue", title="Days past planned end")
            st.plotly_chart(fig)
            st.dataframe(display_columns(overdue), hide_index=True)
    with right:
        st.subheader("Over-allocated employees (>100%)")
        if overloaded.empty:
            st.info("No over-allocated employees.")
        else:
            fig = px.bar(overloaded.head(15), x="employee", y="total_allocation",
                         color="department_name", title="Top over-allocated employees")
            st.plotly_chart(fig)
            st.dataframe(display_columns(overloaded), hide_index=True)