# Enterprise Employee Analytics Data Warehouse System

## Setup

This project requires Python 3.10+, MySQL 8+, and the IBM HR CSV at:

`data/WA_Fn-UseC_-HR-Employee-Attrition.csv`

Install the Python dependencies:

```powershell
py -3 -m pip install -r requirements.txt
```

Configure `app/.env` with `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD`.
The configured MySQL user must access all three schemas: `hr_staging`, `hr_oltp`, and `hr_dw`.

Run the SQL files in this order:

1. `sql/00_create_schemas.sql`
2. `sql/01_staging_ddl.sql`
3. `sql/04_staging_extra_ddl.sql`
4. `sql/02_oltp_ddl.sql`
5. `sql/03_olap_ddl.sql`
6. `sql/05_load_oltp_employees.sql`
7. `sql/06_load_oltp_activity.sql`
8. `sql/07_etl_olap.sql`

Then load synthetic data and populate the warehouse:

```powershell
py -3 run_staging_load.py
mysql -h localhost -u root -p hr_oltp < sql/05_load_oltp_employees.sql
mysql -h localhost -u root -p hr_oltp < sql/06_load_oltp_activity.sql
mysql -h localhost -u root -p hr_dw < sql/07_etl_olap.sql
mysql -h localhost -u root -p hr_dw -e "CALL sp_run_full_etl();"
```

Start the application from the project root:

```powershell
py -3 -m streamlit run app/streamlit_app.py
```
