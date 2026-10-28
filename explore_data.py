import pandas as pd

df = pd.read_csv("data/WA_Fn-UseC_-HR-Employee-Attrition.csv")

print(df.shape)
print(df.columns.tolist())
print(df["Department"].value_counts())
print(df["Attrition"].value_counts())