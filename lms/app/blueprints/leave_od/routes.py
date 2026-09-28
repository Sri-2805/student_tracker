from datetime import date, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import Course, Enrollment, LeaveODRequest, Student, Teacher
from app.utils.decorators import roles_required


leave_od_bp = Blueprint("leave_od", __name__)


def _student_for_current_user():
    return Student.query.filter_by(user_id=current_user.user_id).first()


def _teacher_can_review(teacher, student_id):
    """A teacher validates requests for their department or active courses."""
    if not teacher:
        return False
    return (
        db.session.query(Student.student_id)
        .outerjoin(Enrollment, Enrollment.student_id == Student.student_id)
        .outerjoin(Course, Course.course_id == Enrollment.course_id)
        .filter(Student.student_id == student_id)
        .filter(
            or_(
                Student.department_id == teacher.department_id,
                (Enrollment.status == "Active") & (Course.teacher_id == teacher.teacher_id),
            )
        )
        .first()
        is not None
    )


def _parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


@leave_od_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required("student")
def student_portal():
    student = _student_for_current_user()
    if not student:
        abort(404)

    if request.method == "POST":
        request_type = request.form.get("request_type", "").strip()
        from_date = _parse_date(request.form.get("from_date"))
        to_date = _parse_date(request.form.get("to_date"))
        reason = request.form.get("reason", "").strip()

        errors = []
        if request_type not in {"Leave", "OD"}:
            errors.append("Choose either Leave or On Duty (OD).")
        if not from_date or not to_date:
            errors.append("Enter a valid start and end date.")
        elif to_date < from_date:
            errors.append("The end date cannot be before the start date.")
        if len(reason) < 10:
            errors.append("Add a reason of at least 10 characters.")

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            db.session.add(
                LeaveODRequest(
                    student_id=student.student_id,
                    request_type=request_type,
                    from_date=from_date,
                    to_date=to_date,
                    reason=reason,
                )
            )
            db.session.commit()
            flash("Request submitted for faculty validation.", "success")
            return redirect(url_for("leave_od.student_portal"))

    requests = (
        LeaveODRequest.query.filter_by(student_id=student.student_id)
        .order_by(LeaveODRequest.submitted_at.desc())
        .all()
    )
    return render_template("leave_od_student.html", student=student, requests=requests)


@leave_od_bp.route("/review", methods=["GET", "POST"])
@login_required
@roles_required("teacher", "admin")
def review():
    teacher = Teacher.query.filter_by(user_id=current_user.user_id).first()

    if request.method == "POST":
        request_id = request.form.get("request_id", type=int)
        decision = request.form.get("decision")
        faculty_remarks = request.form.get("faculty_remarks", "").strip()
        leave_request = db.session.get(LeaveODRequest, request_id)

        if not leave_request:
            abort(404)
        if current_user.role != "admin" and not _teacher_can_review(teacher, leave_request.student_id):
            abort(403)
        if decision not in {"Approved", "Rejected"}:
            flash("Choose Approve or Reject.", "danger")
        elif leave_request.status != "Pending":
            flash("This request has already been validated.", "warning")
        elif decision == "Rejected" and len(faculty_remarks) < 3:
            flash("Add a short reason when rejecting a request.", "danger")
        else:
            leave_request.status = decision
            leave_request.faculty_remarks = faculty_remarks or None
            leave_request.reviewed_by = current_user.user_id
            leave_request.reviewed_at = datetime.utcnow()
            db.session.commit()
            flash(f"Request {decision.lower()} successfully.", "success")
        return redirect(url_for("leave_od.review"))

    if current_user.role == "admin":
        requests = LeaveODRequest.query.order_by(LeaveODRequest.submitted_at.desc()).all()
    elif teacher:
        requests = (
            LeaveODRequest.query.join(Student, LeaveODRequest.student_id == Student.student_id)
            .outerjoin(Enrollment, Enrollment.student_id == Student.student_id)
            .outerjoin(Course, Course.course_id == Enrollment.course_id)
            .filter(
                or_(
                    Student.department_id == teacher.department_id,
                    (Enrollment.status == "Active") & (Course.teacher_id == teacher.teacher_id),
                )
            )
            .distinct()
            .order_by(LeaveODRequest.submitted_at.desc())
            .all()
        )
    else:
        requests = []

    pending_count = sum(1 for leave_request in requests if leave_request.status == "Pending")
    return render_template(
        "leave_od_review.html",
        requests=requests,
        pending_count=pending_count,
    )
