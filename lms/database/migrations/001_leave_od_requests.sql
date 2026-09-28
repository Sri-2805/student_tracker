-- Apply this migration to an existing LMS database.
-- Fresh installations already receive this table from database/schema.sql.

CREATE TABLE IF NOT EXISTS leave_od_requests (
    request_id       INT AUTO_INCREMENT PRIMARY KEY,
    student_id       INT NOT NULL,
    request_type     ENUM('Leave','OD') NOT NULL,
    from_date        DATE NOT NULL,
    to_date          DATE NOT NULL,
    reason           TEXT NOT NULL,
    status           ENUM('Pending','Approved','Rejected') NOT NULL DEFAULT 'Pending',
    faculty_remarks  VARCHAR(500),
    reviewed_by      INT NULL,
    reviewed_at      DATETIME NULL,
    submitted_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL,
    CONSTRAINT chk_leave_od_dates CHECK (to_date >= from_date)
) ENGINE=InnoDB;

CREATE INDEX idx_leave_od_student ON leave_od_requests (student_id, submitted_at);
CREATE INDEX idx_leave_od_status ON leave_od_requests (status);
