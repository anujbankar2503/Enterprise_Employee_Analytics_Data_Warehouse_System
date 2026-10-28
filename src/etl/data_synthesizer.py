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
        self.project_df = None
        self.assignments_df = None
        self.reviews_df = None

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

    def generate_projects(self, n_projects=300, as_of=datetime(2026, 10, 1)):
        """Create synthetic projects with statuses and dates."""
        rng = self.rng
        n = n_projects
        as_of_ts = pd.Timestamp(as_of)

        status = rng.choice(
            ["Completed", "Active", "Cancelled", "Planned"],
            size=n, p=[0.45, 0.35, 0.10, 0.10],
        )
        offset = np.where(
            status == "Completed", rng.integers(0, 900, n),
            np.where(status == "Cancelled", rng.integers(0, 1400, n),
                     rng.integers(800, 1700, n)),
        )

        df = pd.DataFrame({
            "project_code": [f"PRJ{i:04d}" for i in range(1, n + 1)],
            "project_name": [self.fake.catch_phrase() for _ in range(n)],
            "project_status": status,
        })
        df["project_start_date"] = pd.Timestamp("2022-01-01") + pd.to_timedelta(offset, unit="D")
        df["planned_end_date"] = df["project_start_date"] + pd.to_timedelta(
            rng.integers(120, 720, n), unit="D")
        df["actual_end_date"] = pd.NaT

        done = (df["project_status"] == "Completed").to_numpy()
        df.loc[done, "actual_end_date"] = (
            df.loc[done, "planned_end_date"]
            + rng.integers(-15, 90, done.sum()).astype("timedelta64[D]")
        )
        canc = (df["project_status"] == "Cancelled").to_numpy()
        df.loc[canc, "actual_end_date"] = (
            df.loc[canc, "project_start_date"]
            + rng.integers(30, 300, canc.sum()).astype("timedelta64[D]")
        )
        plan = (df["project_status"] == "Planned").to_numpy()
        df.loc[plan, "project_start_date"] = (
            as_of_ts + rng.integers(30, 270, plan.sum()).astype("timedelta64[D]")
        )
        df.loc[plan, "planned_end_date"] = (
            df.loc[plan, "project_start_date"]
            + rng.integers(120, 540, plan.sum()).astype("timedelta64[D]")
        )

        self.projects_df = df
        return df

    def generate_assignments(self, as_of=datetime(2026, 10, 1)):
        """Assign each employee to 1-3 projects, respecting hire and project dates."""
        if self.employees_df is None:
            self.scale()
        if "hire_date" not in self.employees_df.columns:
            self.assign_hire_dates(as_of)
        if self.projects_df is None:
            self.generate_projects(as_of=as_of)

        rng = self.rng
        as_of_ts = np.datetime64(pd.Timestamp(as_of))
        emp = self.employees_df[["synthetic_employee_number", "hire_date"]]
        k = rng.choice([1, 2, 3], size=len(emp), p=[0.4, 0.4, 0.2])
        a = emp.loc[emp.index.repeat(k)].reset_index(drop=True)

        proj = self.projects_df[self.projects_df["project_status"] != "Planned"].reset_index(drop=True)
        pick = rng.integers(0, len(proj), len(a))
        codes = proj["project_code"].to_numpy()[pick]
        p_start = proj["project_start_date"].to_numpy()[pick]
        p_actual_end = proj["actual_end_date"].to_numpy()[pick]
        p_end = np.where(np.isnat(p_actual_end), as_of_ts, p_actual_end)

        lo = np.maximum(a["hire_date"].to_numpy(), p_start)
        hi = p_end - np.timedelta64(30, "D")
        span = (hi - lo) / np.timedelta64(1, "D")
        valid = span > 0

        a = a[valid].copy()
        a["project_code"] = codes[valid]
        m = len(a)
        offset = (rng.random(m) * span[valid]).astype("int64").astype("timedelta64[D]")
        a["start_date"] = lo[valid] + offset
        a["end_date"] = p_actual_end[valid]           # NaT = ongoing
        a["billable_flag"] = rng.random(m) < 0.7
        a["allocation_percentage"] = rng.choice([20, 25, 30, 40, 50, 60, 80], size=m)

        self.assignments_df = a.drop(columns=["hire_date"]).reset_index(drop=True)
        return self.assignments_df

    def generate_reviews(self, as_of=datetime(2026, 10, 1)):
        """Create 1-3 performance reviews per assignment."""
        if self.assignments_df is None:
            self.generate_assignments(as_of)

        rng = self.rng
        as_of_ts = np.datetime64(pd.Timestamp(as_of))
        a = self.assignments_df
        n_rev = rng.choice([1, 2, 3], size=len(a), p=[0.5, 0.35, 0.15])
        r = a.loc[a.index.repeat(n_rev),
                  ["synthetic_employee_number", "project_code", "start_date", "end_date"]
                  ].reset_index(drop=True)
        m = len(r)

        lo = r["start_date"].to_numpy() + np.timedelta64(30, "D")
        end = r["end_date"].to_numpy()
        hi = np.where(np.isnat(end), as_of_ts, end)
        span = np.clip((hi - lo) / np.timedelta64(1, "D"), 0, None)
        r["review_date"] = lo + (rng.random(m) * span).astype("int64").astype("timedelta64[D]")

        base = self.employees_df.set_index("synthetic_employee_number")["PerformanceRating"]
        rating = (r["synthetic_employee_number"].map(base).to_numpy()
                  + rng.choice([-1, 0, 0, 1], size=m)).clip(1, 5)
        year = r["review_date"].dt.year.to_numpy()
        score = (rating * 20 - rng.uniform(0, 15, m) + 0.8 * (year - 2022)).clip(0, 100)

        r["performance_rating"] = rating
        r["performance_score"] = score.round(2)
        r["review_status"] = np.where(rng.random(m) < 0.95, "Completed", "Pending")

        # About 10% of reviews are not tied to a project
        r.loc[rng.random(m) < 0.10, "project_code"] = None

        self.reviews_df = r.drop(columns=["start_date", "end_date"])
        return self.reviews_df