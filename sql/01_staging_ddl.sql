USE hr_staging;

-- 1. Batch log (created first because the other tables reference it)
CREATE TABLE IF NOT EXISTS etl_batch_log (
    batch_id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_name       VARCHAR(100) NOT NULL,
    load_started_at   DATETIME NOT NULL,
    load_completed_at DATETIME NULL,
    load_status       VARCHAR(20) NOT NULL,
    rows_read         INT NOT NULL DEFAULT 0,
    rows_loaded       INT NOT NULL DEFAULT 0,
    rows_rejected     INT NOT NULL DEFAULT 0,
    error_message     TEXT NULL
);

-- 2. Main employee staging table
CREATE TABLE IF NOT EXISTS stg_hr_employee (
    staging_row_id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id                  BIGINT NOT NULL,
    source_employee_number    INT NOT NULL,
    synthetic_employee_number VARCHAR(30) NULL,
    age                       TINYINT UNSIGNED NOT NULL,
    attrition                 VARCHAR(3) NOT NULL,
    businesstravel            VARCHAR(30) NOT NULL,
    dailyrate                 INT NOT NULL,
    department                VARCHAR(100) NOT NULL,
    distancefromhome          TINYINT UNSIGNED NOT NULL,
    education                 TINYINT UNSIGNED NOT NULL,
    educationfield            VARCHAR(50) NOT NULL,
    environmentsatisfaction   TINYINT UNSIGNED NOT NULL,
    gender                    VARCHAR(20) NOT NULL,
    hourlyrate                SMALLINT UNSIGNED NOT NULL,
    jobinvolvement            TINYINT UNSIGNED NOT NULL,
    joblevel                  TINYINT UNSIGNED NOT NULL,
    jobrole                   VARCHAR(50) NOT NULL,
    jobsatisfaction           TINYINT UNSIGNED NOT NULL,
    maritalstatus             VARCHAR(20) NOT NULL,
    monthlyincome             INT NOT NULL,
    monthlyrate               INT NOT NULL,
    numcompaniesworked        SMALLINT UNSIGNED NOT NULL,
    overtime                  VARCHAR(3) NOT NULL,
    percentsalaryhike         TINYINT UNSIGNED NOT NULL,
    performancerating         TINYINT UNSIGNED NOT NULL,
    relationshipsatisfaction  TINYINT UNSIGNED NOT NULL,
    stockoptionlevel          TINYINT UNSIGNED NOT NULL,
    totalworkingyears         SMALLINT UNSIGNED NOT NULL,
    trainingtimeslastyear     SMALLINT UNSIGNED NOT NULL,
    worklifebalance           TINYINT UNSIGNED NOT NULL,
    yearsatcompany            SMALLINT UNSIGNED NOT NULL,
    yearsincurrentrole        SMALLINT UNSIGNED NOT NULL,
    yearssincelastpromotion   SMALLINT UNSIGNED NOT NULL,
    yearswithcurrmanager      SMALLINT UNSIGNED NOT NULL,
    loaded_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stg_emp_batch FOREIGN KEY (batch_id)
        REFERENCES etl_batch_log (batch_id)
);

-- 3. Employee history staging table (for SCD Type 2)
CREATE TABLE IF NOT EXISTS stg_employee_history (
    history_row_id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id                  BIGINT NOT NULL,
    source_employee_number    INT NOT NULL,
    synthetic_employee_number VARCHAR(30) NULL,
    department                VARCHAR(100) NOT NULL,
    job_role                  VARCHAR(50) NOT NULL,
    job_level                 TINYINT NULL,
    monthly_income            DECIMAL(12,2) NULL,
    effective_start_date      DATETIME NOT NULL,
    effective_end_date        DATETIME NULL,
    is_current                BOOLEAN NOT NULL,
    change_reason             VARCHAR(100) NULL,
    loaded_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stg_hist_batch FOREIGN KEY (batch_id)
        REFERENCES etl_batch_log (batch_id)
);

SHOW TABLES;