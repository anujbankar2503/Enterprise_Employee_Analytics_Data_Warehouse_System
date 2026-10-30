from pathlib import Path

import pandas as pd
from src.etl.data_synthesizer import DataSynthesizer

CSV_PATH = Path(__file__).resolve().parent / "data" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
synth = DataSynthesizer(CSV_PATH)
synth.scale(100_000)
synth.generate_history()
prj = synth.generate_projects()
asg = synth.generate_assignments()
rev = synth.generate_reviews()

print("Projects:", prj.shape, "| Assignments:", asg.shape, "| Reviews:", rev.shape)
print(prj["project_status"].value_counts())

hire = synth.employees_df.set_index("synthetic_employee_number")["hire_date"]
print("Assignment start >= hire date:",
      (asg["start_date"] >= asg["synthetic_employee_number"].map(hire)).all())
print("Assignment end >= start:",
      (asg["end_date"].isna() | (asg["end_date"] >= asg["start_date"])).all())
print("Ratings in 1-5:", rev["performance_rating"].between(1, 5).all())
print("Scores in 0-100:", rev["performance_score"].between(0, 100).all())

print(rev.groupby(rev["review_date"].dt.year)["performance_score"].agg(["count", "mean"]).round(2))

alloc = asg.groupby("synthetic_employee_number")["allocation_percentage"].sum()
print("Employees over 100% allocation:", (alloc > 100).sum())
overdue = ((prj["project_status"] == "Active") &
           (prj["planned_end_date"] < pd.Timestamp("2026-10-01"))).sum()
print("Overdue active projects:", overdue)