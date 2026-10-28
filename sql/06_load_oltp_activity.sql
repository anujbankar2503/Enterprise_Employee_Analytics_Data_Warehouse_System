USE hr_oltp;

DROP PROCEDURE IF EXISTS sp_load_projects_assignments_reviews;

DELIMITER $$

CREATE PROCEDURE sp_load_projects_assignments_reviews()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Projects
    INSERT INTO projects (project_code, project_name, project_status,
                          project_start_date, planned_end_date, actual_end_date)
    SELECT s.project_code, s.project_name, s.project_status,
           s.project_start_date, s.planned_end_date, s.actual_end_date
    FROM hr_staging.stg_project s
    WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_code = s.project_code);

    -- Assignments (only when the table is empty, so re-runs don't duplicate)
    IF (SELECT COUNT(*) FROM assignments) = 0 THEN
        INSERT INTO assignments (employee_id, project_id, start_date, end_date,
                                 billable_flag, allocation_percentage)
        SELECT e.employee_id, p.project_id, s.start_date, s.end_date,
               s.billable_flag, s.allocation_percentage
        FROM hr_staging.stg_assignment s
        JOIN employees e ON e.employee_number = s.synthetic_employee_number
        JOIN projects  p ON p.project_code    = s.project_code;
    END IF;

    -- Reviews (project is optional)
    IF (SELECT COUNT(*) FROM reviews) = 0 THEN
        INSERT INTO reviews (employee_id, project_id, review_date,
                             performance_rating, performance_score, review_status)
        SELECT e.employee_id, p.project_id, s.review_date,
               s.performance_rating, s.performance_score, s.review_status
        FROM hr_staging.stg_review s
        JOIN employees e ON e.employee_number = s.synthetic_employee_number
        LEFT JOIN projects p ON p.project_code = s.project_code;
    END IF;

    COMMIT;
END$$

DELIMITER ;

CALL sp_load_projects_assignments_reviews();

-- Verification: OLTP counts should match staging counts
SELECT 'projects' AS tbl,
       (SELECT COUNT(*) FROM projects) AS oltp,
       (SELECT COUNT(*) FROM hr_staging.stg_project) AS staging
UNION ALL SELECT 'assignments',
       (SELECT COUNT(*) FROM assignments),
       (SELECT COUNT(*) FROM hr_staging.stg_assignment)
UNION ALL SELECT 'reviews',
       (SELECT COUNT(*) FROM reviews),
       (SELECT COUNT(*) FROM hr_staging.stg_review);