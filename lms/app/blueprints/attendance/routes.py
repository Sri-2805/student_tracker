import csv
import io
from datetime import datetime, date

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, Response, abort
)
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Course, Enrollment, Attendance, Student, Teacher, Notification
from app.utils.decorators import roles_required
from app.blueprints.analytics.services import get_attendance_summary_for_student

attendance_bp = Blueprint("attendance", __name__)


# ---------------------------------------------------------------------------
# TEACHER: Mark attendance for a course on a given date
# ---------------------------------------------------------------------------
@attendance_bp.route("/mark", methods=["GET", "POST"])
@login_required
@roles_required("teacher", "admin")
def mark():
    teacher = Teacher.query.filter_by(user_id=current_user.user_id).first()
    courses = Course.query.filter_by(teacher_id=teacher.teacher_id).all() if teacher else Course.query.all()

    selected_course_id = request.values.get("course_id", type=int)
    selected_date = request.values.get("attendance_date") or date.today().isoformat()

    roster = []
    if selected_course_id:
        enrollments = Enrollment.query.filter_by(course_id=selected_course_id, status="Active").all()
        existing = {
            a.student_id: a.status
            for a in Attendance.query.filter_by(
                course_id=selected_course_id,
                attendance_date=datetime.strptime(selected_date, "%Y-%m-%d").date(),
            ).all()
        }
        for e in enrollments:
            roster.append({
                "student": e.student,
                "current_status": existing.get(e.student_id, "Present"),
            })

    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        att_date = datetime.strptime(request.form.get("attendance_date"), "%Y-%m-%d").date()
        student_ids = request.form.getlist("student_id")

        for sid in student_ids:
            status = request.form.get(f"status_{sid}", "Present")
            record = Attendance.query.filter_by(
                student_id=sid, course_id=course_id, attendance_date=att_date, period_no=1
            ).first()
            if record:
                record.status = status
            else:
                record = Attendance(
                    student_id=sid,
                    course_id=course_id,
                    attendance_date=att_date,
                    status=status,
                    marked_by=current_user.user_id,
                )
                db.session.add(record)

            # Notify student if marked Absent
            if status == "Absent":
                db.session.add(Notification(
                    user_id=Student.query.get(int(sid)).user_id,
                    title="Attendance: Marked Absent",
                    body=f"You were marked absent on {att_date} for a class.",
                    notif_type="attendance",
                ))

        db.session.commit()
        flash("Attendance saved successfully.", "success")
        return redirect(url_for("attendance.mark", course_id=course_id, attendance_date=att_date.isoformat()))

    return render_template(
        "attendance_mark.html",
        courses=courses,
        selected_course_id=selected_course_id,
        selected_date=selected_date,
        roster=roster,
    )


# ---------------------------------------------------------------------------
# STUDENT / PARENT: View attendance tracking for a given student
# ---------------------------------------------------------------------------
@attendance_bp.route("/view/<int:student_id>")
@login_required
def view(student_id):
    student = Student.query.get_or_404(student_id)

    # Access control: students see only themselves, parents only their children
    if current_user.role == "student" and student.user_id != current_user.user_id:
        abort(403)
    if current_user.role == "parent" and not student.has_parent(current_user.user_id):
        abort(403)

    summary = get_attendance_summary_for_student(student_id)

    course_id = request.args.get("course_id", type=int)
    records = []
    if course_id:
        records = (
            Attendance.query.filter_by(student_id=student_id, course_id=course_id)
            .order_by(Attendance.attendance_date.desc())
            .all()
        )

    return render_template(
        "attendance_view.html",
        student=student,
        summary=summary,
        records=records,
        selected_course_id=course_id,
    )


# ---------------------------------------------------------------------------
# DOWNLOAD: Export attendance as CSV (per student, optionally per course)
# ---------------------------------------------------------------------------
@attendance_bp.route("/download/<int:student_id>")
@login_required
def download(student_id):
    student = Student.query.get_or_404(student_id)

    if current_user.role == "student" and student.user_id != current_user.user_id:
        abort(403)
    if current_user.role == "parent" and not student.has_parent(current_user.user_id):
        abort(403)

    course_id = request.args.get("course_id", type=int)
    query = Attendance.query.filter_by(student_id=student_id)
    if course_id:
        query = query.filter_by(course_id=course_id)
    records = query.order_by(Attendance.attendance_date.asc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Course Code", "Course Name", "Status", "Remarks"])
    for r in records:
        writer.writerow([
            r.attendance_date.isoformat(),
            r.course.course_code,
            r.course.course_name,
            r.status,
            r.remarks or "",
        ])

    filename = f"attendance_{student.registration_no}.csv"
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
