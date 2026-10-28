USE hr_oltp;

-- 1. Departments
CREATE TABLE IF NOT EXISTS departments (
    department_id   INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(200) NOT NULL UNIQUE,
    department_code VARCHAR(20)  NOT NULL UNIQUE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Projects
CREATE TABLE IF NOT EXISTS projects (
    project_id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_code       VARCHAR(20)  NOT NULL UNIQUE,
    project_name       VARCHAR(150) NOT NULL,
    project_status     ENUM('Planned','Active','Completed','Cancelled')
                       NOT NULL DEFAULT 'Planned',
    project_start_date DATE NOT NULL,
    planned_end_date   DATE NULL,
    actual_end_date    DATE NULL
);

-- 3. Employees
CREATE TABLE IF NOT EXISTS employees (
    employee_id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    department_id       INT NOT NULL,
    employee_number     VARCHAR(30) NOT NULL UNIQUE,
    first_name          VARCHAR(30) NOT NULL,
    last_name           VARCHAR(30) NOT NULL,
    hire_date           DATE NOT NULL,
    job_role            VARCHAR(30) NOT NULL,
    job_level           TINYINT UNSIGNED NULL,
    gender              VARCHAR(30) NULL,
    work_location       VARCHAR(30) NOT NULL,
    monthly_income      DECIMAL(12,2) NOT NULL,
    created_date        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_date        DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    address             VARCHAR(100) NULL,
    city                VARCHAR(30) NULL,
    state               VARCHAR(30) NULL,
    age                 TINYINT UNSIGNED NULL,
    marital_status      VARCHAR(20) NULL,
    education           TINYINT UNSIGNED NULL,
    education_field     VARCHAR(50) NULL,
    business_travel     VARCHAR(30) NULL,
    distance_from_home  TINYINT UNSIGNED NULL,
    overtime            ENUM('Yes','No') NULL,
    attrition_status    ENUM('Yes','No') NULL,
    total_working_years SMALLINT UNSIGNED NULL,
    num_companies_worked SMALLINT UNSIGNED NULL,
    CONSTRAINT fk_emp_dept FOREIGN KEY (department_id)
        REFERENCES departments (department_id),
    CONSTRAINT chk_emp_income CHECK (monthly_income >= 0),
    CONSTRAINT chk_emp_age CHECK (age BETWEEN 18 AND 100),
    CONSTRAINT chk_emp_edu CHECK (education BETWEEN 1 AND 5),
    CONSTRAINT chk_emp_years CHECK (total_working_years >= 0),
    CONSTRAINT chk_emp_companies CHECK (num_companies_worked >= 0),
    INDEX idx_emp_dept (department_id)
);

-- 4. Assignments (employee <-> project)
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    employee_id           BIGINT NOT NULL,
    project_id            BIGINT NOT NULL,
    start_date            DATE NOT NULL,
    end_date              DATE NULL,
    billable_flag         BOOLEAN NOT NULL DEFAULT FALSE,
    allocation_percentage DECIMAL(5,2) NOT NULL,
    CONSTRAINT fk_asg_emp FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id),
    CONSTRAINT fk_asg_proj FOREIGN KEY (project_id)
        REFERENCES projects (project_id),
    CONSTRAINT chk_asg_alloc CHECK (allocation_percentage BETWEEN 0 AND 100),
    INDEX idx_asg_emp (employee_id),
    INDEX idx_asg_proj (project_id)
);

-- 5. Reviews
CREATE TABLE IF NOT EXISTS reviews (
    review_id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    reviewer_employee_id BIGINT NULL,
    employee_id          BIGINT NOT NULL,
    project_id           BIGINT NULL,
    review_date          DATE NOT NULL,
    performance_rating   TINYINT UNSIGNED NULL,
    performance_score    DECIMAL(5,2) NULL,
    review_status        VARCHAR(20) NOT NULL DEFAULT 'Pending',
    comments             TEXT NULL,
    CONSTRAINT fk_rev_reviewer FOREIGN KEY (reviewer_employee_id)
        REFERENCES employees (employee_id),
    CONSTRAINT fk_rev_emp FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id),
    CONSTRAINT fk_rev_proj FOREIGN KEY (project_id)
        REFERENCES projects (project_id),
    CONSTRAINT chk_rev_rating CHECK (performance_rating BETWEEN 1 AND 5),
    CONSTRAINT chk_rev_score CHECK (performance_score BETWEEN 0 AND 100),
    INDEX idx_rev_emp (employee_id),
    INDEX idx_rev_date (review_date)
);

SHOW TABLES;