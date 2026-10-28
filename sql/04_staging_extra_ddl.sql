USE hr_staging;

-- Extra columns on the employee staging table
ALTER TABLE stg_hr_employee
    ADD COLUMN first_name VARCHAR(30) NULL AFTER synthetic_employee_number,
    ADD COLUMN last_name  VARCHAR(30) NULL AFTER first_name,
    ADD COLUMN hire_date  DATE NULL AFTER last_name;

-- Projects
CREATE TABLE IF NOT EXISTS stg_project (
    staging_row_id     BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id           BIGINT NOT NULL,
    project_code       VARCHAR(20)  NOT NULL,
    project_name       VARCHAR(150) NOT NULL,
    project_status     VARCHAR(20)  NOT NULL,
    project_start_date DATE NOT NULL,
    planned_end_date   DATE NULL,
    actual_end_date    DATE NULL,
    loaded_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stg_proj_batch FOREIGN KEY (batch_id)
        REFERENCES etl_batch_log (batch_id)
);

-- Assignments
CREATE TABLE IF NOT EXISTS stg_assignment (
    staging_row_id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id                  BIGINT NOT NULL,
    synthetic_employee_number VARCHAR(30) NOT NULL,
    project_code              VARCHAR(20) NOT NULL,
    start_date                DATE NOT NULL,
    end_date                  DATE NULL,
    billable_flag             BOOLEAN NOT NULL,
    allocation_percentage     DECIMAL(5,2) NOT NULL,
    loaded_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stg_asg_batch FOREIGN KEY (batch_id)
        REFERENCES etl_batch_log (batch_id)
);

-- Reviews
CREATE TABLE IF NOT EXISTS stg_review (
    staging_row_id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id                  BIGINT NOT NULL,
    synthetic_employee_number VARCHAR(30) NOT NULL,
    project_code              VARCHAR(20) NULL,
    review_date               DATE NOT NULL,
    performance_rating        TINYINT UNSIGNED NULL,
    performance_score         DECIMAL(5,2) NULL,
    review_status             VARCHAR(20) NOT NULL,
    loaded_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stg_rev_batch FOREIGN KEY (batch_id)
        REFERENCES etl_batch_log (batch_id)
);

SHOW TABLES;
DESCRIBE stg_hr_employee;