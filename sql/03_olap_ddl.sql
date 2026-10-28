USE hr_dw;

-- 1. Dim_Department
CREATE TABLE IF NOT EXISTS dim_department (
    department_key  INT AUTO_INCREMENT PRIMARY KEY,
    department_id   INT UNIQUE,
    department_name VARCHAR(200) NOT NULL,
    department_code VARCHAR(20)  NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2. Dim_Project
CREATE TABLE IF NOT EXISTS dim_project (
    project_key        BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id         BIGINT NOT NULL UNIQUE,
    project_code       VARCHAR(30) NOT NULL,
    project_name       VARCHAR(150) NOT NULL,
    project_status     ENUM('Planned','Active','Completed','Cancelled')
                       NOT NULL DEFAULT 'Planned',
    project_start_date DATE NOT NULL,
    planned_end_date   DATE NULL,
    actual_end_date    DATE NULL
);

-- "Unknown" member for reviews that have no project
INSERT IGNORE INTO dim_project
    (project_key, project_id, project_code, project_name, project_status, project_start_date)
VALUES
    (-1, -1, 'UNKNOWN', 'Unknown Project', 'Planned', '1900-01-01');

-- 3. Dim_Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_key    INT PRIMARY KEY,              -- format YYYYMMDD
    full_date   DATE NOT NULL UNIQUE,
    day         TINYINT UNSIGNED NOT NULL,
    month       TINYINT UNSIGNED NOT NULL,
    month_name  VARCHAR(15) NOT NULL,
    quarter     TINYINT UNSIGNED NOT NULL,
    year        SMALLINT UNSIGNED NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    CONSTRAINT chk_dd_day     CHECK (day BETWEEN 1 AND 31),
    CONSTRAINT chk_dd_month   CHECK (month BETWEEN 1 AND 12),
    CONSTRAINT chk_dd_quarter CHECK (quarter BETWEEN 1 AND 4)
);

-- 4. Dim_Employee (SCD Type 2)
CREATE TABLE IF NOT EXISTS dim_employee (
    employee_key         BIGINT AUTO_INCREMENT PRIMARY KEY,
    employee_id          BIGINT NOT NULL,            -- business key from OLTP
    employee_number      VARCHAR(30) NOT NULL,
    department_id        BIGINT NOT NULL,
    first_name           VARCHAR(30) NOT NULL,
    last_name            VARCHAR(30) NOT NULL,
    age                  TINYINT UNSIGNED NULL,
    job_role             VARCHAR(30) NOT NULL,
    job_level            TINYINT NULL,
    gender               VARCHAR(30) NULL,
    monthly_income       DECIMAL(12,2) NOT NULL,
    start_date           DATETIME NOT NULL,          -- SCD2
    end_date             DATETIME NULL,              -- SCD2
    is_current           BOOLEAN NOT NULL DEFAULT TRUE,  -- SCD2
    marital_status       VARCHAR(20) NULL,
    education            TINYINT UNSIGNED NULL,
    education_field      VARCHAR(50) NULL,
    business_travel      VARCHAR(30) NULL,
    distance_from_home   TINYINT UNSIGNED NULL,
    overtime             ENUM('Yes','No') NULL,
    attrition_status     ENUM('Yes','No') NULL,
    total_working_years  SMALLINT UNSIGNED NULL,
    num_companies_worked SMALLINT UNSIGNED NULL,
    -- Only current rows get a value, and it must be unique,
    -- so each employee can have only ONE current row.
    current_employee_id  BIGINT GENERATED ALWAYS AS
        (CASE WHEN is_current = 1 THEN employee_id ELSE NULL END) STORED UNIQUE,
    CONSTRAINT chk_de_age    CHECK (age BETWEEN 18 AND 100),
    CONSTRAINT chk_de_income CHECK (monthly_income >= 0),
    CONSTRAINT chk_de_edu    CHECK (education BETWEEN 1 AND 5),
    CONSTRAINT chk_de_years  CHECK (total_working_years >= 0),
    CONSTRAINT chk_de_comp   CHECK (num_companies_worked >= 0),
    INDEX idx_de_emp_current (employee_id, is_current),
    INDEX idx_de_emp_dates (employee_id, start_date, end_date)
);

-- 5. Fact_PerformanceReviews
CREATE TABLE IF NOT EXISTS fact_performance_reviews (
    performance_review_fact_key BIGINT AUTO_INCREMENT PRIMARY KEY,
    review_id          BIGINT NOT NULL UNIQUE,       -- degenerate key
    employee_key       BIGINT NOT NULL,
    project_key        BIGINT NOT NULL DEFAULT -1,
    review_date_key    INT NOT NULL,
    department_key     INT NOT NULL,
    performance_rating TINYINT UNSIGNED NULL,
    performance_score  DECIMAL(5,2) NULL,
    review_count       TINYINT UNSIGNED NOT NULL DEFAULT 1,
    CONSTRAINT fk_fact_emp  FOREIGN KEY (employee_key)    REFERENCES dim_employee (employee_key),
    CONSTRAINT fk_fact_proj FOREIGN KEY (project_key)     REFERENCES dim_project (project_key),
    CONSTRAINT fk_fact_date FOREIGN KEY (review_date_key) REFERENCES dim_date (date_key),
    CONSTRAINT fk_fact_dept FOREIGN KEY (department_key)  REFERENCES dim_department (department_key),
    CONSTRAINT chk_f_rating CHECK (performance_rating BETWEEN 1 AND 5),
    CONSTRAINT chk_f_score  CHECK (performance_score BETWEEN 0 AND 100),
    INDEX idx_fact_emp  (employee_key),
    INDEX idx_fact_proj (project_key),
    INDEX idx_fact_date (review_date_key),
    INDEX idx_fact_dept (department_key)
);

SHOW TABLES;
SELECT * FROM dim_project;