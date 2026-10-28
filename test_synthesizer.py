from src.etl.data_synthesizer import DataSynthesizer

synth = DataSynthesizer("data/WA_Fn-UseC_-HR-Employee-Attrition.csv")
df = synth.scale(100_000)

print(df.shape)
print("Unique IDs:", df["synthetic_employee_number"].is_unique)
print(df["Attrition"].value_counts(normalize=True))
print(df[["Age", "MonthlyIncome", "TotalWorkingYears", "YearsAtCompany"]].describe())
print(df[["synthetic_employee_number", "first_name", "last_name", "Gender", "Department"]].head())