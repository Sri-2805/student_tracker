from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "teacher", "student", "parent"), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    profile_photo = db.Column(db.String(255))
    is_active_flag = db.Column("is_active", db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return str(self.user_id)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Department(db.Model):
    __tablename__ = "departments"
    department_id = db.Column(db.Integer, primary_key=True)
    dept_code = db.Column(db.String(20), unique=True, nullable=False)
    dept_name = db.Column(db.String(120), nullable=False)


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False)
    registration_no = db.Column(db.String(30), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
    program = db.Column(db.String(50), default="B.E")
    semester = db.Column(db.SmallInteger, default=1)
    academic_year = db.Column(db.String(20))
    batch = db.Column(db.String(20))
    total_credits = db.Column(db.Integer, default=0)
    earned_credits = db.Column(db.Integer, default=0)
    parent_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))

    user = db.relationship("User", foreign_keys=[user_id])
    parent_user = db.relationship("User", foreign_keys=[parent_id])
    department = db.relationship("Department")


class Teacher(db.Model):
    __tablename__ = "teachers"

    teacher_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
    designation = db.Column(db.String(80))

    user = db.relationship("User")


class ParentStudentLink(db.Model):
    __tablename__ = "parent_student_link"
    link_id = db.Column(db.Integer, primary_key=True)
    parent_user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"))
    relationship_type = db.Column("relationship", db.String(30), default="Guardian")


class Course(db.Model):
    __tablename__ = "courses"

    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(30), unique=True, nullable=False)
    course_name = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
    semester = db.Column(db.SmallInteger, default=1)
    credits = db.Column(db.SmallInteger, default=3)
    academic_year = db.Column(db.String(20))
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.teacher_id"))

    teacher = db.relationship("Teacher")


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id"), nullable=False)
    status = db.Column(db.Enum("Active", "Completed", "Dropped"), default="Active")
    enrolled_on = db.Column(db.Date, default=datetime.utcnow)

    student = db.relationship("Student")
    course = db.relationship("Course")


class Attendance(db.Model):
    __tablename__ = "attendance"

    attendance_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id"), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum("Present", "Absent", "Late", "Excused"), default="Present")
    period_no = db.Column(db.SmallInteger, default=1)
    marked_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    remarks = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student")
    course = db.relationship("Course")


class Assessment(db.Model):
    __tablename__ = "assessments"

    assessment_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    assessment_type = db.Column(
        db.Enum("Quiz", "Assignment", "Midterm", "Final", "Lab", "Project"), nullable=False
    )
    max_marks = db.Column(db.Numeric(6, 2), default=100)
    weight_percent = db.Column(db.Numeric(5, 2), default=0)
    assessment_date = db.Column(db.Date)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship("Course")


class Grade(db.Model):
    __tablename__ = "grades"

    grade_id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.assessment_id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), nullable=False)
    marks_obtained = db.Column(db.Numeric(6, 2))
    grade_letter = db.Column(db.String(4))
    remarks = db.Column(db.String(255))
    entered_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    entered_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessment = db.relationship("Assessment")
    student = db.relationship("Student")


class Message(db.Model):
    __tablename__ = "messages"

    message_id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"))
    subject = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])
    student = db.relationship("Student")


class Announcement(db.Model):
    __tablename__ = "announcements"

    announcement_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    target_role = db.Column(db.Enum("all", "student", "parent", "teacher"), default="all")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.String(255))
    notif_type = db.Column(
        db.Enum("attendance", "grade", "message", "deadline", "announcement"), nullable=False
    )
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Task(db.Model):
    __tablename__ = "tasks"

    task_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id"))
    title = db.Column(db.String(180), nullable=False)
    task_type = db.Column(db.Enum("Assignment", "Assessment", "Event", "Other"), default="Assignment")
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum("Pending", "Submitted", "Completed", "Overdue"), default="Pending")
