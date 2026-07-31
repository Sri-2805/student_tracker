from datetime import date, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import (
    Student, Course, Enrollment, Task, Announcement, Message, db
)
from app.blueprints.analytics.services import (
    get_attendance_summary_for_student, get_grade_summary_for_student
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    role = current_user.role

    if role == "student":
        student = Student.query.filter_by(user_id=current_user.user_id).first()
        courses = (
            Enrollment.query.filter_by(student_id=student.student_id, status="Active").all()
            if student else []
        )
        upcoming_tasks = (
            Task.query.filter_by(student_id=student.student_id)
            .filter(Task.due_date >= date.today())
            .order_by(Task.due_date.asc())
            .limit(5)
            .all()
            if student else []
        )
        attendance_summary = get_attendance_summary_for_student(student.student_id) if student else []
        grade_summary = get_grade_summary_for_student(student.student_id) if student else []
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()

        return render_template(
            "dashboard_student.html",
            student=student,
            courses=courses,
            upcoming_tasks=upcoming_tasks,
            attendance_summary=attendance_summary,
            grade_summary=grade_summary,
            announcements=announcements,
        )

    elif role == "parent":
        children = Student.query.filter_by(parent_id=current_user.user_id).all()
        child_data = []
        for child in children:
            child_data.append({
                "student": child,
                "attendance": get_attendance_summary_for_student(child.student_id),
                "grades": get_grade_summary_for_student(child.student_id),
            })
        unread_messages = Message.query.filter_by(
            receiver_id=current_user.user_id, is_read=False
        ).count()
        return render_template("dashboard_parent.html", child_data=child_data, unread_messages=unread_messages)

    elif role == "teacher":
        from app.models import Teacher
        teacher = Teacher.query.filter_by(user_id=current_user.user_id).first()
        courses = Course.query.filter_by(teacher_id=teacher.teacher_id).all() if teacher else []
        return render_template("dashboard_teacher.html", teacher=teacher, courses=courses)

    else:  # admin
        total_students = Student.query.count()
        total_courses = Course.query.count()
        recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
        return render_template(
            "dashboard_admin.html",
            total_students=total_students,
            total_courses=total_courses,
            recent_announcements=recent_announcements,
        )
