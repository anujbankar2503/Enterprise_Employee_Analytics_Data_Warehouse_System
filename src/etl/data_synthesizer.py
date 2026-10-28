import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime


class DataSynthesizer:
    """Scales the IBM HR dataset into a large, realistic synthetic dataset."""

    def __init__(self, csv_path, seed=42):
        self.csv_path = csv_path
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.fake = Faker()
        Faker.seed(seed)
        self.base_df = None
        self.employees_df = None
        self.history_df = None

    def load_base(self):
        """Read the IBM CSV and drop columns that are constant in every row."""
        df = pd.read_csv(self.csv_path)
        df = df.drop(columns=["EmployeeCount", "Over18", "StandardHours"])
        self.base_df = df
        return df

    def scale(self, n=100_000):
        """Sample the base data up to n rows and add realistic variation."""
        if self.base_df is None:
            self.load_base()

        rng = self.rng
        df = self.base_df.sample(n=n, replace=True, random_state=self.seed)
        df = df.reset_index(drop=True)
        df = df.rename(columns={"EmployeeNumber": "source_employee_number"})

        # Add small random variation so rows are not exact copies
        df["Age"] = (df["Age"] + rng.integers(-3, 4, n)).clip(18, 60)
        df["MonthlyIncome"] = (
            df["MonthlyIncome"] * rng.uniform(0.9, 1.1, n)
        ).round().astype(int)
        df["TotalWorkingYears"] = (
            df["TotalWorkingYears"] + rng.integers(-2, 3, n)
        ).clip(lower=0)

        # Keep the numbers logically consistent
        df["TotalWorkingYears"] = np.minimum(df["TotalWorkingYears"], df["Age"] - 18)
        df["YearsAtCompany"] = np.minimum(df["YearsAtCompany"], df["TotalWorkingYears"])
        for col in ["YearsInCurrentRole", "YearsSinceLastPromotion", "YearsWithCurrManager"]:
            df[col] = np.minimum(df[col], df["YearsAtCompany"])

        # Unique ID and Faker names (matching gender)
        df["synthetic_employee_number"] = [f"EMP{i:06d}" for i in range(1, n + 1)]
        df["first_name"] = [
            self.fake.first_name_male() if g == "Male" else self.fake.first_name_female()
            for g in df["Gender"]
        ]
        df["last_name"] = [self.fake.last_name() for _ in range(n)]

        self.employees_df = df
        return df

    def assign_hire_dates(self, as_of=datetime(2026, 10, 1)):
        """Derive a hire_date from YearsAtCompany."""
        df = self.employees_df
        days = df["YearsAtCompany"] * 365 + self.rng.integers(0, 365, len(df))
        df["hire_date"] = (
            pd.Timestamp(as_of) - pd.to_timedelta(days, unit="D")
        ).dt.normalize()

    def generate_history(self, change_fraction=0.25, as_of=datetime(2026, 10, 1)):
        """Create SCD Type 2 history rows for a subset of employees."""
        if self.employees_df is None:
            self.scale()
        self.assign_hire_dates(as_of)

        df = self.employees_df
        rng = self.rng
        as_of_ts = pd.Timestamp(as_of)

        roles_by_dept = self.base_df.groupby("Department")["JobRole"].unique().to_dict()
        departments = list(roles_by_dept.keys())

        eligible = df[df["YearsAtCompany"] >= 2]
        chosen = eligible.sample(frac=change_fraction, random_state=self.seed)

        rows = []
        for emp in chosen.itertuples():
            k = int(rng.choice([1, 2, 3], p=[0.6, 0.3, 0.1]))
            tenure_days = (as_of_ts - emp.hire_date).days

            # k distinct change dates between hire+90 days and as_of-30 days
            offsets = np.sort(
                rng.choice(np.arange(90, tenure_days - 30), size=k, replace=False)
            )
            change_dates = [emp.hire_date + pd.Timedelta(days=int(o)) for o in offsets]
            starts = [emp.hire_date] + change_dates
            ends = change_dates + [pd.NaT]

            # Start from the CURRENT version and walk backwards in time
            dept, role = emp.Department, emp.JobRole
            level, income = int(emp.JobLevel), float(emp.MonthlyIncome)
            versions = [None] * (k + 1)
            reasons = ["Initial hire"] + [None] * k
            versions[k] = (dept, role, level, income)

            for i in range(k, 0, -1):
                change = rng.choice(
                    ["Promotion", "Salary bump", "Department transfer"],
                    p=[0.4, 0.4, 0.2],
                )
                if change == "Promotion" and level > 1:
                    level -= 1
                    income *= rng.uniform(0.80, 0.92)
                elif change == "Department transfer":
                    dept = rng.choice([d for d in departments if d != dept])
                    role = rng.choice(roles_by_dept[dept])
                    income *= rng.uniform(0.95, 1.05)
                else:
                    change = "Salary bump"
                    income *= rng.uniform(0.88, 0.95)
                reasons[i] = change
                versions[i - 1] = (dept, role, level, round(income, 2))

            for i in range(k + 1):
                d, r, lv, inc = versions[i]
                rows.append({
                    "source_employee_number": emp.source_employee_number,
                    "synthetic_employee_number": emp.synthetic_employee_number,
                    "department": d,
                    "job_role": r,
                    "job_level": lv,
                    "monthly_income": round(inc, 2),
                    "effective_start_date": starts[i],
                    "effective_end_date": ends[i],
                    "is_current": i == k,
                    "change_reason": reasons[i],
                })

        self.history_df = pd.DataFrame(rows)
        return self.history_df