-- ============================================================================
-- Student LMS Tracker - MySQL Database Schema
-- Modules: Attendance | Grades | Performance Analytics | Parent Communication
-- ============================================================================

DROP DATABASE IF EXISTS lms_tracker;
CREATE DATABASE lms_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE lms_tracker;

-- ----------------------------------------------------------------------------
-- 1. CORE USER TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE users (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            ENUM('admin','teacher','student','parent') NOT NULL,
    full_name       VARCHAR(120) NOT NULL,
    email           VARCHAR(120) UNIQUE,
    phone           VARCHAR(20),
    profile_photo   VARCHAR(255) DEFAULT NULL,
    is_active       TINYINT(1)   DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE departments (
    department_id   INT AUTO_INCREMENT PRIMARY KEY,
    dept_code        VARCHAR(20) NOT NULL UNIQUE,
    dept_name        VARCHAR(120) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE students (
    student_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL UNIQUE,
    registration_no  VARCHAR(30) NOT NULL UNIQUE,
    department_id    INT,
    program          VARCHAR(50)  DEFAULT 'B.E',
    semester         TINYINT      DEFAULT 1,
    academic_year    VARCHAR(20),
    batch            VARCHAR(20),
    total_credits    INT DEFAULT 0,
    earned_credits   INT DEFAULT 0,
    parent_id        INT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (parent_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE teachers (
    teacher_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL UNIQUE,
    department_id    INT,
    designation      VARCHAR(80),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
) ENGINE=InnoDB;

-- Link table: a parent user can be linked to multiple children (siblings)
CREATE TABLE parent_student_link (
    link_id      INT AUTO_INCREMENT PRIMARY KEY,
    parent_user_id INT NOT NULL,
    student_id   INT NOT NULL,
    relationship VARCHAR(30) DEFAULT 'Guardian',
    FOREIGN KEY (parent_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE KEY uniq_parent_student (parent_user_id, student_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2. COURSES & ENROLLMENT
-- ----------------------------------------------------------------------------

CREATE TABLE courses (
    course_id       INT AUTO_INCREMENT PRIMARY KEY,
    course_code     VARCHAR(30) NOT NULL UNIQUE,
    course_name     VARCHAR(150) NOT NULL,
    department_id   INT,
    semester        TINYINT DEFAULT 1,
    credits         TINYINT DEFAULT 3,
    academic_year   VARCHAR(20),
    teacher_id      INT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE enrollments (
    enrollment_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT NOT NULL,
    course_id       INT NOT NULL,
    status          ENUM('Active','Completed','Dropped') DEFAULT 'Active',
    enrolled_on     DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE KEY uniq_student_course (student_id, course_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3. ATTENDANCE MODULE
-- ----------------------------------------------------------------------------

CREATE TABLE attendance (
    attendance_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT NOT NULL,
    course_id       INT NOT NULL,
    attendance_date DATE NOT NULL,
    status          ENUM('Present','Absent','Late','Excused') NOT NULL DEFAULT 'Present',
    period_no       TINYINT DEFAULT 1,
    marked_by       INT NOT NULL,          -- teacher user_id
    remarks         VARCHAR(255),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (marked_by) REFERENCES users(user_id),
    UNIQUE KEY uniq_attendance_slot (student_id, course_id, attendance_date, period_no)
) ENGINE=InnoDB;

CREATE INDEX idx_attendance_lookup ON attendance (course_id, attendance_date);
CREATE INDEX idx_attendance_student ON attendance (student_id, course_id);

-- ----------------------------------------------------------------------------
-- 4. GRADES / ASSESSMENT MODULE
-- ----------------------------------------------------------------------------

CREATE TABLE assessments (
    assessment_id   INT AUTO_INCREMENT PRIMARY KEY,
    course_id       INT NOT NULL,
    title           VARCHAR(150) NOT NULL,
    assessment_type ENUM('Quiz','Assignment','Midterm','Final','Lab','Project') NOT NULL,
    max_marks       DECIMAL(6,2) NOT NULL DEFAULT 100,
    weight_percent  DECIMAL(5,2) NOT NULL DEFAULT 0,   -- contribution to final grade
    assessment_date DATE,
    created_by      INT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE grades (
    grade_id         INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id    INT NOT NULL,
    student_id       INT NOT NULL,
    marks_obtained   DECIMAL(6,2),
    grade_letter     VARCHAR(4),
    remarks          VARCHAR(255),
    entered_by       INT NOT NULL,
    entered_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (entered_by) REFERENCES users(user_id),
    UNIQUE KEY uniq_grade_slot (assessment_id, student_id)
) ENGINE=InnoDB;

CREATE INDEX idx_grades_student ON grades (student_id);

-- ----------------------------------------------------------------------------
-- 5. PARENT COMMUNICATION MODULE
-- ----------------------------------------------------------------------------

CREATE TABLE messages (
    message_id      INT AUTO_INCREMENT PRIMARY KEY,
    sender_id        INT NOT NULL,
    receiver_id       INT NOT NULL,
    student_id       INT NULL,             -- which child the message concerns
    subject          VARCHAR(180) NOT NULL,
    body             TEXT NOT NULL,
    is_read          TINYINT(1) DEFAULT 0,
    sent_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE announcements (
    announcement_id  INT AUTO_INCREMENT PRIMARY KEY,
    title            VARCHAR(180) NOT NULL,
    message          TEXT NOT NULL,
    posted_by        INT NOT NULL,
    target_role      ENUM('all','student','parent','teacher') DEFAULT 'all',
    department_id    INT NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (posted_by) REFERENCES users(user_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
) ENGINE=InnoDB;

CREATE TABLE notifications (
    notification_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    title            VARCHAR(180) NOT NULL,
    body             VARCHAR(255),
    notif_type       ENUM('attendance','grade','message','deadline','announcement') NOT NULL,
    is_read          TINYINT(1) DEFAULT 0,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6. TASKS / DEADLINE TRACKER (supports "My Daily Task List" style widget)
-- ----------------------------------------------------------------------------

CREATE TABLE tasks (
    task_id         INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT NOT NULL,
    course_id       INT NULL,
    title           VARCHAR(180) NOT NULL,
    task_type       ENUM('Assignment','Assessment','Event','Other') DEFAULT 'Assignment',
    due_date        DATE NOT NULL,
    status          ENUM('Pending','Submitted','Completed','Overdue') DEFAULT 'Pending',
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 7. VIEWS FOR ANALYTICS / REPORTING
-- ----------------------------------------------------------------------------

-- Per-student, per-course attendance percentage
CREATE OR REPLACE VIEW v_attendance_summary AS
SELECT
    a.student_id,
    a.course_id,
    c.course_name,
    c.course_code,
    COUNT(*)                                                     AS total_classes,
    SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END) AS attended,
    ROUND(SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS attendance_percent
FROM attendance a
JOIN courses c ON c.course_id = a.course_id
GROUP BY a.student_id, a.course_id;

-- Per-student, per-course weighted grade (final score based on weight_percent)
CREATE OR REPLACE VIEW v_grade_summary AS
SELECT
    g.student_id,
    a.course_id,
    ROUND(SUM((g.marks_obtained / a.max_marks) * a.weight_percent) /
          NULLIF(SUM(a.weight_percent), 0) * 100, 2) AS weighted_score_percent
FROM grades g
JOIN assessments a ON a.assessment_id = g.assessment_id
WHERE g.marks_obtained IS NOT NULL
GROUP BY g.student_id, a.course_id;

-- At-risk students: low attendance OR low grade average
CREATE OR REPLACE VIEW v_at_risk_students AS
SELECT
    s.student_id,
    u.full_name,
    s.registration_no,
    COALESCE(AVG(vas.attendance_percent), 0) AS avg_attendance,
    COALESCE(AVG(vgs.weighted_score_percent), 0) AS avg_grade
FROM students s
JOIN users u ON u.user_id = s.user_id
LEFT JOIN v_attendance_summary vas ON vas.student_id = s.student_id
LEFT JOIN v_grade_summary vgs ON vgs.student_id = s.student_id
GROUP BY s.student_id, u.full_name, s.registration_no
HAVING avg_attendance < 75 OR avg_grade < 50;

-- ----------------------------------------------------------------------------
-- 8. SEED DATA
-- ----------------------------------------------------------------------------

INSERT INTO departments (dept_code, dept_name) VALUES
('CSE','Computer Science and Engineering'),
('ECE','Electronics and Communication Engineering'),
('MECH','Mechanical Engineering');

-- Passwords below are all the bcrypt/werkzeug hash for the plaintext "password123"
-- (generated at app runtime — replace via app/utils/create_users.py; placeholder shown)
INSERT INTO users (username, password_hash, role, full_name, email, phone) VALUES
('admin1',   'pbkdf2:sha256:placeholder', 'admin',   'Admin User',        'admin@vmrf.edu',    '9000000001'),
('t.suresh', 'pbkdf2:sha256:placeholder', 'teacher', 'Dr. Suresh Kumar',  'suresh@vmrf.edu',    '9000000002'),
('t.anitha', 'pbkdf2:sha256:placeholder', 'teacher', 'Prof. Anitha R',    'anitha@vmrf.edu',    '9000000003'),
('sri.vatsa','pbkdf2:sha256:placeholder', 'student', 'Sri Vatsa G',       'srivatsa@vmrf.edu',  '9000000004'),
('p.ganesh', 'pbkdf2:sha256:placeholder', 'parent',  'Ganesh (Parent)',   'ganesh@example.com', '9000000005');

INSERT INTO teachers (user_id, department_id, designation) VALUES
(2, 1, 'Associate Professor'),
(3, 1, 'Assistant Professor');

INSERT INTO students (user_id, registration_no, department_id, program, semester, academic_year, batch, total_credits, earned_credits, parent_id) VALUES
(4, '3502310571', 1, 'B.E', 7, '2026-2027', '2023-2027', 21, 0, 5);

INSERT INTO parent_student_link (parent_user_id, student_id, relationship) VALUES
(5, 1, 'Father');

INSERT INTO courses (course_code, course_name, department_id, semester, credits, academic_year, teacher_id) VALUES
('CS701','CRYPTOGRAPHY AND NETWORK SECURITY', 1, 7, 3, '2026-2027', 1),
('CS702','INDUSTRIAL ROBOTICS', 1, 7, 3, '2026-2027', 2),
('CS703','MACHINE LEARNING', 1, 7, 4, '2026-2027', 1);

INSERT INTO enrollments (student_id, course_id) VALUES (1,1),(1,2),(1,3);

INSERT INTO assessments (course_id, title, assessment_type, max_marks, weight_percent, assessment_date, created_by) VALUES
(1, 'Quiz 1', 'Quiz', 20, 10, '2026-07-10', 2),
(1, 'Midterm', 'Midterm', 50, 30, '2026-07-20', 2),
(2, 'Assignment 1', 'Assignment', 25, 20, '2026-07-15', 3),
(3, 'Lab Evaluation 1', 'Lab', 30, 20, '2026-07-18', 2);

INSERT INTO grades (assessment_id, student_id, marks_obtained, grade_letter, entered_by) VALUES
(1, 1, 17, 'A', 2),
(2, 1, 41, 'A', 2),
(3, 1, 22, 'A+', 3),
(4, 1, 24, 'A', 2);

INSERT INTO tasks (student_id, course_id, title, task_type, due_date, status) VALUES
(1, 1, 'Submit Assignment 2', 'Assignment', '2026-08-02', 'Pending'),
(1, 3, 'ML Project Proposal', 'Assignment', '2026-08-05', 'Pending');

INSERT INTO announcements (title, message, posted_by, target_role) VALUES
('Semester 7 Timetable Released', 'Please check the calendar module for the updated timetable.', 1, 'all');
