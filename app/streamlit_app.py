import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px
import streamlit as st

from src.db_manager import DatabaseError
from src.managers import AnalyticsManager

st.set_page_config(page_title="HR Analytics Warehouse", layout="wide")


@st.cache_data(ttl=300)
def load_home():
    an = AnalyticsManager()
    return an.kpis(), an.department_performance(), an.yoy_trend()


st.title("Enterprise Employee Analytics")
st.caption("OLTP data entry  |  Star-schema data warehouse  |  SCD Type 2 history")

try:
    kpis, dept_df, trend_df = load_home()
except DatabaseError as e:
    st.error(f"Database connection problem: {e}")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Current headcount", f"{kpis['headcount']:,}")
c2.metric("Average review score", f"{(kpis['avg_score'] or 0):.2f}")
c3.metric("Attrition rate", f"{(kpis['attrition_rate'] or 0):.1f}%")
c4.metric("Total reviews", f"{kpis['total_reviews']:,}")

left, right = st.columns(2)
with left:
    fig = px.line(trend_df, x="year", y="avg_score", markers=True,
                  title="Average review score by year")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig)
with right:
    fig = px.bar(dept_df, x="department_name", y="avg_score", text="avg_score",
                 title="Average review score by department")
    st.plotly_chart(fig)

st.markdown(
    "Use the pages in the sidebar:\n"
    "- **Employees**: onboard, edit (department changes create SCD Type 2 history)\n"
    "- **Projects**: create projects and assign employees\n"
    "- **Reviews**: submit performance reviews\n"
    "- **Dashboard**: trends, top performers, attrition risk, bottlenecks"
)