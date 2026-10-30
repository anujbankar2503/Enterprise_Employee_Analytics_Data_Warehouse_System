# Enterprise Employee Analytics Data Warehouse System

An employee analytics application for HR teams to manage employee records,
projects, performance reviews, and workforce insights. The system combines a
MySQL operational layer with a star-schema warehouse and a Streamlit interface.

## Features

- Employee onboarding, search, editing, and employment history.
- Project creation, employee assignments, billable status, and allocation tracking.
- Performance reviews with ratings, scores, and comments.
- Workforce dashboards for performance, attrition, project bottlenecks, and capacity.
- SCD Type 2 employment history in the warehouse.
- A modular data access layer with database, entity, and manager abstractions.

## Architecture

The application uses three MySQL schemas:

- `hr_staging`: landing tables and ETL batch logging.
- `hr_oltp`: normalized employee, department, project, assignment, and review data.
- `hr_dw`: date, department, project, employee-history dimensions, and review facts.

The Streamlit pages call managers in `src/managers.py`. Database connections are
centralized in `src/db_manager.py`, and application configuration is loaded from
`app/.env` through `src/config.py`.

## Requirements

This project requires Python 3.10+, MySQL 8+, and the IBM HR CSV at:

`data/WA_Fn-UseC_-HR-Employee-Attrition.csv`

Install the Python dependencies:

```powershell
py -3 -m pip install -r requirements.txt
```

Configure `app/.env` with `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD`.
Do not commit this file. The configured MySQL user must access all three schemas:
`hr_staging`, `hr_oltp`, and `hr_dw`.

## Database Setup

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

Run the application from the project root so imports and repository-relative
paths resolve correctly.

## Development Checks

Compile the Python source and application files with:

```powershell
py -3 -m compileall -q app src
```

The `test_*.py` files are diagnostic scripts that require the source CSV and,
for database checks, a reachable MySQL instance.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
Security reports should follow [SECURITY.md](SECURITY.md).

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
