USE hr_oltp;

DROP PROCEDURE IF EXISTS sp_load_departments_employees;

DELIMITER $$

CREATE PROCEDURE sp_load_departments_employees()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. Departments (distinct names found in staging)
    INSERT IGNORE INTO departments (department_name, department_code)
    SELECT DISTINCT
        department,
        CASE department
            WHEN 'Research & Development' THEN 'RND'
            WHEN 'Sales'                  THEN 'SAL'
            WHEN 'Human Resources'        THEN 'HR'
            ELSE UPPER(LEFT(REPLACE(department, ' ', ''), 3))
        END
    FROM hr_staging.stg_hr_employee;

    -- 2. Employees (CTE + window function removes duplicates)
    INSERT INTO employees (
        department_id, employee_number, first_name, last_name, hire_date,
        job_role, job_level, gender, work_location, monthly_income,
        age, marital_status, education, education_field, business_travel,
        distance_from_home, overtime, attrition_status,
        total_working_years, num_companies_worked
    )
    WITH ranked AS (
        SELECT s.*,
               ROW_NUMBER() OVER (
                   PARTITION BY s.synthetic_employee_number
                   ORDER BY s.loaded_at DESC, s.staging_row_id DESC
               ) AS rn
        FROM hr_staging.stg_hr_employee s
    )
    SELECT
        d.department_id,
        r.synthetic_employee_number,
        TRIM(r.first_name),
        TRIM(r.last_name),
        r.hire_date,
        r.jobrole,
        r.joblevel,
        r.gender,
        CASE MOD(r.staging_row_id, 4)
            WHEN 0 THEN 'Pune'
            WHEN 1 THEN 'Mumbai'
            WHEN 2 THEN 'Bengaluru'
            ELSE 'Hyderabad'
        END,
        r.monthlyincome,
        r.age,
        r.maritalstatus,
        r.education,
        r.educationfield,
        r.businesstravel,
        r.distancefromhome,
        r.overtime,
        r.attrition,
        r.totalworkingyears,
        r.numcompaniesworked
    FROM ranked r
    JOIN departments d ON d.department_name = r.department
    WHERE r.rn = 1
      AND NOT EXISTS (
          SELECT 1 FROM employees e
          WHERE e.employee_number = r.synthetic_employee_number
      );

    COMMIT;
END$$

DELIMITER ;

CALL sp_load_departments_employees();

-- Verification
SELECT VERSION();
SELECT * FROM departments;
SELECT COUNT(*) AS total_employees FROM employees;
SELECT d.department_name, COUNT(*) AS employees
FROM employees e JOIN departments d ON d.department_id = e.department_id
GROUP BY d.department_name;
SELECT * FROM employees LIMIT 5;