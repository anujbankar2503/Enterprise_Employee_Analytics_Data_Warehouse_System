USE hr_dw;

DROP PROCEDURE IF EXISTS sp_load_dim_date;
DROP PROCEDURE IF EXISTS sp_load_dim_department;
DROP PROCEDURE IF EXISTS sp_load_dim_project;
DROP PROCEDURE IF EXISTS sp_load_dim_employee;
DROP PROCEDURE IF EXISTS sp_load_fact_performance;
DROP PROCEDURE IF EXISTS sp_run_full_etl;

DELIMITER $$

-- 1. Date dimension (2020-2030) using a recursive CTE
CREATE PROCEDURE sp_load_dim_date()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN ROLLBACK; RESIGNAL; END;

    SET SESSION cte_max_recursion_depth = 10000;
    START TRANSACTION;
    INSERT IGNORE INTO dim_date
        (date_key, full_date, day, month, month_name, quarter, year, day_of_week)
    WITH RECURSIVE d AS (
        SELECT DATE('2020-01-01') AS dt
        UNION ALL
        SELECT dt + INTERVAL 1 DAY FROM d WHERE dt < '2030-12-31'
    )
    SELECT YEAR(dt) * 10000 + MONTH(dt) * 100 + DAY(dt),
           dt, DAY(dt), MONTH(dt), MONTHNAME(dt), QUARTER(dt), YEAR(dt), DAYNAME(dt)
    FROM d;
    COMMIT;
END$$

-- 2. Department dimension (Type 1: overwrite)
CREATE PROCEDURE sp_load_dim_department()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN ROLLBACK; RESIGNAL; END;

    START TRANSACTION;
    INSERT INTO dim_department (department_id, department_name, department_code, is_active)
    SELECT department_id, department_name, department_code, is_active
    FROM hr_oltp.departments
    ON DUPLICATE KEY UPDATE
        department_name = VALUES(department_name),
        department_code = VALUES(department_code),
        is_active       = VALUES(is_active);
    COMMIT;
END$$

-- 3. Project dimension (Type 1: overwrite)
CREATE PROCEDURE sp_load_dim_project()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN ROLLBACK; RESIGNAL; END;

    START TRANSACTION;
    INSERT INTO dim_project (project_id, project_code, project_name, project_status,
                             project_start_date, planned_end_date, actual_end_date)
    SELECT project_id, project_code, project_name, project_status,
           project_start_date, planned_end_date, actual_end_date
    FROM hr_oltp.projects
    ON DUPLICATE KEY UPDATE
        project_name       = VALUES(project_name),
        project_status     = VALUES(project_status),
        project_start_date = VALUES(project_start_date),
        planned_end_date   = VALUES(planned_end_date),
        actual_end_date    = VALUES(actual_end_date);
    COMMIT;
END$$

-- 4. Employee dimension (SCD Type 2)
CREATE PROCEDURE sp_load_dim_employee()
BEGIN
    DECLARE v_now DATETIME;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN ROLLBACK; RESIGNAL; END;

    SET v_now = NOW();
    START TRANSACTION;

    -- A. Load the historical versions (synthesized) for employees not yet in the dimension
    INSERT INTO dim_employee
        (employee_id, employee_number, department_id, first_name, last_name, age,
         job_role, job_level, gender, monthly_income, start_date, end_date, is_current,
         marital_status, education, education_field, business_travel,
         distance_from_home, overtime, attrition_status,
         total_working_years, num_companies_worked)
    SELECT e.employee_id, e.employee_number, d.department_id, e.first_name, e.last_name, e.age,
           h.job_role, h.job_level, e.gender, h.monthly_income,
           h.effective_start_date, h.effective_end_date, h.is_current,
           e.marital_status, e.education, e.education_field, e.business_travel,
           e.distance_from_home, e.overtime, e.attrition_status,
           e.total_working_years, e.num_companies_worked
    FROM hr_staging.stg_employee_history h
    JOIN hr_oltp.employees   e ON e.employee_number = h.synthetic_employee_number
    JOIN hr_oltp.departments d ON d.department_name = h.department
    WHERE NOT EXISTS (SELECT 1 FROM dim_employee x WHERE x.employee_id = e.employee_id);

    -- B. Expire current rows whose tracked attributes changed in OLTP
    UPDATE dim_employee de
    JOIN hr_oltp.employees e ON e.employee_id = de.employee_id
    SET de.end_date = v_now, de.is_current = 0
    WHERE de.is_current = 1
      AND (   de.department_id <> e.department_id
           OR de.job_role      <> e.job_role
           OR NOT (de.job_level <=> e.job_level)
           OR de.monthly_income <> e.monthly_income);

    -- C. Insert a current row for every employee that has none
    --    (brand-new employees and the ones just expired)
    INSERT INTO dim_employee
        (employee_id, employee_number, department_id, first_name, last_name, age,
         job_role, job_level, gender, monthly_income, start_date, end_date, is_current,
         marital_status, education, education_field, business_travel,
         distance_from_home, overtime, attrition_status,
         total_working_years, num_companies_worked)
    SELECT e.employee_id, e.employee_number, e.department_id, e.first_name, e.last_name, e.age,
           e.job_role, e.job_level, e.gender, e.monthly_income,
           CASE WHEN EXISTS (SELECT 1 FROM dim_employee y WHERE y.employee_id = e.employee_id)
                THEN v_now ELSE e.hire_date END,
           NULL, 1,
           e.marital_status, e.education, e.education_field, e.business_travel,
           e.distance_from_home, e.overtime, e.attrition_status,
           e.total_working_years, e.num_companies_worked
    FROM hr_oltp.employees e
    WHERE NOT EXISTS (SELECT 1 FROM dim_employee x
                      WHERE x.employee_id = e.employee_id AND x.is_current = 1);

    COMMIT;
END$$

-- 5. Fact table: each review is linked to the employee version valid on the review date
CREATE PROCEDURE sp_load_fact_performance()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN ROLLBACK; RESIGNAL; END;

    START TRANSACTION;
    INSERT INTO fact_performance_reviews
        (review_id, employee_key, project_key, review_date_key, department_key,
         performance_rating, performance_score, review_count)
    SELECT r.review_id,
           de.employee_key,
           COALESCE(dp.project_key, -1),
           YEAR(r.review_date) * 10000 + MONTH(r.review_date) * 100 + DAY(r.review_date),
           dd.department_key,
           r.performance_rating,
           r.performance_score,
           1
    FROM hr_oltp.reviews r
    JOIN dim_employee de
         ON  de.employee_id = r.employee_id
         AND r.review_date >= de.start_date
         AND (de.end_date IS NULL OR r.review_date < de.end_date)
    JOIN dim_department dd ON dd.department_id = de.department_id
    LEFT JOIN dim_project dp ON dp.project_id = r.project_id
    WHERE NOT EXISTS (SELECT 1 FROM fact_performance_reviews f WHERE f.review_id = r.review_id);
    COMMIT;
END$$

-- Master procedure
CREATE PROCEDURE sp_run_full_etl()
BEGIN
    CALL sp_load_dim_date();
    CALL sp_load_dim_department();
    CALL sp_load_dim_project();
    CALL sp_load_dim_employee();
    CALL sp_load_fact_performance();
END$$

DELIMITER ;