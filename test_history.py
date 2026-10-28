from src.etl.data_synthesizer import DataSynthesizer

synth = DataSynthesizer("data/WA_Fn-UseC_-HR-Employee-Attrition.csv")
synth.scale(100_000)
hist = synth.generate_history()

print(hist.shape)
print("Employees with history:", hist["synthetic_employee_number"].nunique())
print(hist["change_reason"].value_counts())

# Check 1: exactly one current row per employee
cur = hist.groupby("synthetic_employee_number")["is_current"].sum()
print("One current row each:", (cur == 1).all())

# Check 2: no gaps or overlaps (each end date = next version's start date)
hist = hist.sort_values(["synthetic_employee_number", "effective_start_date"])
next_start = hist.groupby("synthetic_employee_number")["effective_start_date"].shift(-1)
closed = hist[hist["effective_end_date"].notna()]
print("No gaps/overlaps:", (closed["effective_end_date"] == next_start[closed.index]).all())

print(hist.head(8).to_string())