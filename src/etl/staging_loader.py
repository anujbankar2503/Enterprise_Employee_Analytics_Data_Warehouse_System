import mysql.connector
import pandas as pd

from src.config import database_config


class StagingLoader:
    """Bulk-loads synthesized DataFrames into the hr_staging schema."""

    # DataFrame columns (lower-cased) -> staging table columns
    TABLES = {
        "stg_hr_employee": [
            "source_employee_number", "synthetic_employee_number", "first_name",
            "last_name", "hire_date", "age", "attrition", "businesstravel",
            "dailyrate", "department", "distancefromhome", "education",
            "educationfield", "environmentsatisfaction", "gender", "hourlyrate",
            "jobinvolvement", "joblevel", "jobrole", "jobsatisfaction",
            "maritalstatus", "monthlyincome", "monthlyrate", "numcompaniesworked",
            "overtime", "percentsalaryhike", "performancerating",
            "relationshipsatisfaction", "stockoptionlevel", "totalworkingyears",
            "trainingtimeslastyear", "worklifebalance", "yearsatcompany",
            "yearsincurrentrole", "yearssincelastpromotion", "yearswithcurrmanager",
        ],
        "stg_employee_history": [
            "source_employee_number", "synthetic_employee_number", "department",
            "job_role", "job_level", "monthly_income", "effective_start_date",
            "effective_end_date", "is_current", "change_reason",
        ],
        "stg_project": [
            "project_code", "project_name", "project_status",
            "project_start_date", "planned_end_date", "actual_end_date",
        ],
        "stg_assignment": [
            "synthetic_employee_number", "project_code", "start_date",
            "end_date", "billable_flag", "allocation_percentage",
        ],
        "stg_review": [
            "synthetic_employee_number", "project_code", "review_date",
            "performance_rating", "performance_score", "review_status", "comments",
        ],
    }

    def __init__(self):
        self.conn = mysql.connector.connect(**database_config("hr_staging"))

    def close(self):
        self.conn.close()

    def truncate_all(self):
        """Empty all staging tables so the load can be re-run safely."""
        cur = self.conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in [*self.TABLES, "etl_batch_log"]:
            cur.execute(f"TRUNCATE TABLE {table}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        self.conn.commit()
        cur.close()

    def start_batch(self, source_name):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO etl_batch_log (source_name, load_started_at, load_status) "
            "VALUES (%s, NOW(), 'RUNNING')",
            (source_name,),
        )
        self.conn.commit()
        batch_id = cur.lastrowid
        cur.close()
        return batch_id

    def finish_batch(self, batch_id, status, rows_read, rows_loaded,
                     rows_rejected=0, error=None):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE etl_batch_log SET load_completed_at = NOW(), load_status = %s, "
            "rows_read = %s, rows_loaded = %s, rows_rejected = %s, error_message = %s "
            "WHERE batch_id = %s",
            (status, rows_read, rows_loaded, rows_rejected, error, batch_id),
        )
        self.conn.commit()
        cur.close()

    @staticmethod
    def _prepare(df, columns):
        """Select columns, format dates as text, and turn NaN/NaT into None."""
        df = df.rename(columns=str.lower)[columns].copy()
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%Y-%m-%d")
        return df.astype(object).where(df.notna(), None)

    def load_table(self, table, df, batch_id, chunk_size=5000):
        columns = self.TABLES[table]
        data = self._prepare(df, columns)
        rows = [(batch_id, *r) for r in data.itertuples(index=False, name=None)]

        placeholders = ", ".join(["%s"] * (len(columns) + 1))
        sql = (f"INSERT INTO {table} (batch_id, {', '.join(columns)}) "
               f"VALUES ({placeholders})")

        cur = self.conn.cursor()
        try:
            for i in range(0, len(rows), chunk_size):
                cur.executemany(sql, rows[i:i + chunk_size])
                self.conn.commit()
        except mysql.connector.Error:
            self.conn.rollback()
            raise
        finally:
            cur.close()
        return len(rows)