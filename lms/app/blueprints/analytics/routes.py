from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from app.models import Student, Course, Teacher
from app.utils.decorators import roles_required
from app.blueprints.analytics.services import (
    get_attendance_summary_for_student,
    get_grade_summary_for_student,
    get_at_risk_students,
)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/student/<int:student_id>")
@login_required
def student_analytics(student_id):
    student = Student.query.get_or_404(student_id)

    if current_user.role == "student" and student.user_id != current_user.user_id:
        abort(403)
    if current_user.role == "parent" and student.parent_id != current_user.user_id:
        abort(403)

    attendance = get_attendance_summary_for_student(student_id)
    grades = get_grade_summary_for_student(student_id)

    return render_template(
        "analytics_student.html", student=student, attendance=attendance, grades=grades
    )


@analytics_bp.route("/overview")
@login_required
@roles_required("teacher", "admin")
def overview():
    at_risk = get_at_risk_students()
    total_courses = Course.query.count()
    total_students = Student.query.count()
    return render_template(
        "analytics_overview.html",
        at_risk=at_risk,
        total_courses=total_courses,
        total_students=total_students,
    )
