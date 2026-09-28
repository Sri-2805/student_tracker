# Student LMS Tracker

A complete Student LMS Tracker web application built with **Python (Flask)** and **MySQL**, covering:

- ✅ Attendance marking, tracking, and CSV download
- ✅ Grade entry and management (weighted assessments, auto letter-grades)
- ✅ Performance analytics & reporting (charts, at-risk student detection)
- ✅ Parent communication (secure messaging, notifications, announcements)
- ✅ Student Leave / On-Duty requests with faculty validation

Includes 4 roles: **Admin**, **Teacher**, **Student**, **Parent** — each with its own dashboard.

---

## 1. Requirements

- Python 3.10+
- MySQL 8.0+ (or MariaDB 10.6+)
- pip

## 2. Setup

### Step 1 — Create the database
```bash
mysql -u root -p < database/schema.sql
```
This creates the `lms_tracker` database, all tables, analytics views, and demo seed data
(matching the sample dashboard: Sri Vatsa G, Semester 7, CSE, B.E, Academic Year 2026-2027).

### Step 2 — Configure environment
```bash
cp .env.example .env
# edit .env and set DB_USER / DB_PASSWORD / SECRET_KEY
```

### Step 3 — Install dependencies
```bash
python -m venv venv
source venv/bin/activate       # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Step 4 — Fix demo user passwords
The SQL seed data can't compute Werkzeug password hashes, so run this once:
```bash
python seed_passwords.py
```
This sets every seeded demo account's password to **`password123`**.

### Step 5 — Run the app
```bash
python run.py
```
Visit **http://localhost:5000**

## Adding many users/courses

Use the `seed_bulk.py` script to generate or import a large number of users and courses.

Examples:

Generate 50 students, 10 teachers, and 8 courses:

```bash
python lms/seed_bulk.py --students 50 --teachers 10 --courses 8
```

Import from CSV (columns: `type,username,full_name,email,registration_no,course_code`):

```bash
python lms/seed_bulk.py --from-csv path/to/data.csv
```

Passwords default to `password123` unless provided in the CSV.

### Demo logins (password: `password123`)
| Username    | Role    |
|-------------|---------|
| admin1      | Admin   |
| t.suresh    | Teacher |
| t.anitha    | Teacher |
| sri.vatsa   | Student |
| p.ganesh    | Parent (linked to Sri Vatsa) |

---

## 3. Project Structure

```
lms/
├── app/
│   ├── blueprints/
│   │   ├── auth/            # login/logout
│   │   ├── attendance/      # mark, view, CSV export
│   │   ├── grades/          # assessments, grade entry, report cards
│   │   ├── analytics/       # charts, at-risk detection, services.py (shared queries)
│   │   ├── parents/         # messaging / inbox / compose
│   │   ├── leave_od/        # student leave/OD requests and faculty validation
│   │   ├── admin/           # user/course/announcement management
│   │   └── dashboard_routes.py
│   ├── templates/           # Jinja2 + Bootstrap 5 templates
│   ├── static/css/style.css
│   ├── models.py            # SQLAlchemy ORM models
│   ├── extensions.py        # db, login_manager
│   └── utils/decorators.py  # @roles_required
├── database/schema.sql       # full MySQL schema + views + seed data
├── config.py
├── run.py
├── seed_passwords.py
├── requirements.txt
└── .env.example
```

## 4. Key Design Notes

- **Attendance**: `attendance` table stores one row per student/course/date/period.
  `v_attendance_summary` view (and the equivalent Python service in
  `analytics/services.py`) computes per-course attendance %. Teachers mark a whole
  class roster in one form submit; students/parents can download a CSV of the full
  log or a single course's log.
- **Grades**: `assessments` (quiz/assignment/midterm/final/lab/project, each with a
  `weight_percent`) + `grades` (marks per student per assessment). Final course grade
  = weighted average of `(marks/max_marks) * weight`. Letter grades are computed
  automatically on save.
- **Analytics**: `v_at_risk_students` / `get_at_risk_students()` flags students below
  75% attendance or 50% grade average — surfaced to teachers/admins on the Analytics
  Overview page with a one-click "Notify Parent" shortcut into the messaging module.
- **Parent communication**: `messages` table (threaded by subject, optionally tagged
  to a specific `student_id`) + `notifications` (auto-created on absence, new grade,
  or new message) + `announcements` (broadcast, filterable by target role).
- **Leave / OD**: students submit dated Leave or On-Duty requests from the portal;
  faculty validate requests for their department or active courses, with optional remarks.
  The request history remains visible to the student with Pending, Approved, or Rejected status.
- Passwords are hashed with Werkzeug's `pbkdf2:sha256`. Sessions via Flask-Login.
  All student/parent/teacher data views are access-controlled by role and ownership
  (a parent can only see their own linked children, a student only themselves, etc).

## 5. Extending

- Swap CSV export for PDF via `reportlab` if needed (`pip install reportlab`).
- Add email notifications by wiring `Notification` creation to `Flask-Mail`.
- Add a REST API layer (Flask-RESTX) on top of the same models for a future mobile app.
