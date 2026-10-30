USE hr_staging;

-- Extra columns on the employee staging table
SET @add_first_name = (
        SELECT IF(COUNT(*) = 0,
                            'ALTER TABLE stg_hr_employee ADD COLUMN first_name VARCHAR(30) NULL AFTER synthetic_employee_number',
                            'SELECT 1')
        FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'stg_hr_employee'
            AND column_name = 'first_name'
);
PREPARE add_first_name FROM @add_first_name;
EXECUTE add_first_name;
DEALLOCATE PREPARE add_first_name;

SET @add_last_name = (
        SELECT IF(COUNT(*) = 0,
                            'ALTER TABLE stg_hr_employee ADD COLUMN last_name VARCHAR(30) NULL AFTER first_name',
                            'SELECT 1')
        FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'stg_hr_employee'
            AND column_name = 'last_name'
);
PREPARE add_last_name FROM @add_last_name;
EXECUTE add_last_name;
DEALLOCATE PREPARE add_last_name;

SET @add_hire_date = (
        SELECT IF(COUNT(*) = 0,
                            'ALTER TABLE stg_hr_employee ADD COLUMN hire_date DATE NULL AFTER last_name',
                            'SELECT 1')
        FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'stg_hr_employee'
            AND column_name = 'hire_date'
);
PREPARE add_hire_date FROM @add_hire_date;
EXECUTE add_hire_date;
DEALLOCATE PREPARE add_hire_date;

SET @add_review_comments = (
        SELECT IF(COUNT(*) = 0,
                            'ALTER TABLE stg_review ADD COLUMN comments TEXT NULL AFTER review_status',
                            'SELECT 1')
        FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'stg_review'
            AND column_name = 'comments'
);

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
    comments                 TEXT NULL,
    loaded_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stg_rev_batch FOREIGN KEY (batch_id)
        REFERENCES etl_batch_log (batch_id)
);

PREPARE add_review_comments FROM @add_review_comments;
EXECUTE add_review_comments;
DEALLOCATE PREPARE add_review_comments;

SHOW TABLES;
DESCRIBE stg_hr_employee;