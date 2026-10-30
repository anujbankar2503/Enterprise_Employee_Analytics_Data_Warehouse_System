from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).resolve().parent / "data" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
df = pd.read_csv(CSV_PATH)

print(df.shape)
print(df.columns.tolist())
print(df["Department"].value_counts())
print(df["Attrition"].value_counts())