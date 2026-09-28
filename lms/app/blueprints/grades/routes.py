import csv
import io
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, Response, abort
)
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Course, Assessment, Grade, Enrollment, Student, Teacher, Notification
from app.utils.decorators import roles_required
from app.blueprints.analytics.services import get_grade_summary_for_student
from flask import current_app
import os
from werkzeug.utils import secure_filename
from app.models import AssignmentSubmission

grades_bp = Blueprint("grades", __name__)


def _letter_grade(percent):
    if percent is None:
        return "-"
    if percent >= 90: return "A+"
    if percent >= 80: return "A"
    if percent >= 70: return "B+"
    if percent >= 60: return "B"
    if percent >= 50: return "C"
    if percent >= 40: return "D"
    return "F"


# ---------------------------------------------------------------------------
# TEACHER: Create a new assessment for a course
# ---------------------------------------------------------------------------
@grades_bp.route("/assessments/new", methods=["GET", "POST"])
@login_required
@roles_required("teacher", "admin")
def new_assessment():
    teacher = Teacher.query.filter_by(user_id=current_user.user_id).first()
    courses = Course.query.filter_by(teacher_id=teacher.teacher_id).all() if teacher else Course.query.all()

    if request.method == "POST":
        assessment = Assessment(
            course_id=request.form.get("course_id", type=int),
            title=request.form.get("title"),
            assessment_type=request.form.get("assessment_type"),
            max_marks=request.form.get("max_marks", type=float),
            weight_percent=request.form.get("weight_percent", type=float),
            assessment_date=datetime.strptime(request.form.get("assessment_date"), "%Y-%m-%d").date()
            if request.form.get("assessment_date") else None,
            created_by=current_user.user_id,
        )
        db.session.add(assessment)
        db.session.commit()
        flash("Assessment created. You can now enter grades for it.", "success")
        return redirect(url_for("grades.entry", assessment_id=assessment.assessment_id))

    return render_template("assessment_new.html", courses=courses)


# ---------------------------------------------------------------------------
# TEACHER: Grade entry for an assessment
# ---------------------------------------------------------------------------
@grades_bp.route("/entry", methods=["GET", "POST"])
@login_required
@roles_required("teacher", "admin")
def entry():
    teacher = Teacher.query.filter_by(user_id=current_user.user_id).first()
    courses = Course.query.filter_by(teacher_id=teacher.teacher_id).all() if teacher else Course.query.all()

    assessment_id = request.values.get("assessment_id", type=int)
    course_id = request.values.get("course_id", type=int)

    assessments = Assessment.query.filter_by(course_id=course_id).all() if course_id else []
    roster = []
    assessment = None

    if assessment_id:
        assessment = Assessment.query.get_or_404(assessment_id)
        course_id = assessment.course_id
        enrollments = Enrollment.query.filter_by(course_id=course_id, status="Active").all()
        existing = {
            g.student_id: g for g in Grade.query.filter_by(assessment_id=assessment_id).all()
        }
        for e in enrollments:
            roster.append({
                "student": e.student,
                "grade": existing.get(e.student_id),
            })

    if request.method == "POST":
        assessment_id = request.form.get("assessment_id", type=int)
        assessment = Assessment.query.get_or_404(assessment_id)
        student_ids = request.form.getlist("student_id")

        for sid in student_ids:
            raw_marks = request.form.get(f"marks_{sid}")
            marks = float(raw_marks) if raw_marks not in (None, "") else None
            percent = (marks / float(assessment.max_marks) * 100) if marks is not None else None
            letter = _letter_grade(percent)

            record = Grade.query.filter_by(assessment_id=assessment_id, student_id=sid).first()
            if record:
                record.marks_obtained = marks
                record.grade_letter = letter
            else:
                record = Grade(
                    assessment_id=assessment_id,
                    student_id=sid,
                    marks_obtained=marks,
                    grade_letter=letter,
                    entered_by=current_user.user_id,
                )
                db.session.add(record)

            if marks is not None:
                db.session.add(Notification(
                    user_id=Student.query.get(int(sid)).user_id,
                    title=f"Grade posted: {assessment.title}",
                    body=f"You scored {marks}/{assessment.max_marks} ({letter}).",
                    notif_type="grade",
                ))

        db.session.commit()
        flash("Grades saved successfully.", "success")
        return redirect(url_for("grades.entry", assessment_id=assessment_id))

    return render_template(
        "grades_entry.html",
        courses=courses,
        assessments=assessments,
        selected_course_id=course_id,
        assessment=assessment,
        roster=roster,
    )


# ---------------------------------------------------------------------------
# STUDENT / PARENT: Report card / grade view
# ---------------------------------------------------------------------------
@grades_bp.route("/report/<int:student_id>")
@login_required
def report(student_id):
    student = Student.query.get_or_404(student_id)

    if current_user.role == "student" and student.user_id != current_user.user_id:
        abort(403)
    if current_user.role == "parent" and not student.has_parent(current_user.user_id):
        abort(403)

    summary = get_grade_summary_for_student(student_id)
    return render_template("grades_report.html", student=student, summary=summary)


@grades_bp.route("/report/<int:student_id>/download")
@login_required
def download_report(student_id):
    student = Student.query.get_or_404(student_id)
    if current_user.role == "student" and student.user_id != current_user.user_id:
        abort(403)
    if current_user.role == "parent" and not student.has_parent(current_user.user_id):
        abort(403)

    summary = get_grade_summary_for_student(student_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Course Code", "Course Name", "Assessment", "Type", "Marks Obtained", "Max Marks"])
    for course in summary:
        for a in course["assessments"]:
            writer.writerow([
                course["course_code"], course["course_name"], a["title"], a["type"],
                a["marks_obtained"], a["max_marks"],
            ])

    filename = f"grade_report_{student.registration_no}.csv"
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# STUDENT: Submit assignment (Assessment of type 'Assignment')
# ---------------------------------------------------------------------------
@grades_bp.route('/assignments/submit', methods=['GET', 'POST'])
@login_required
@roles_required('student')
def submit_assignment():
    assessment_id = request.values.get('assessment_id', type=int)
    assessment = Assessment.query.get_or_404(assessment_id) if assessment_id else None
    student = Student.query.filter_by(user_id=current_user.user_id).first()

    if request.method == 'POST':
        assessment_id = request.form.get('assessment_id', type=int)
        comment = request.form.get('comment')
        file = request.files.get('file')

        sub_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'assignments')
        os.makedirs(sub_folder, exist_ok=True)
        file_path = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            filename = f"assess_{assessment_id}_stu_{student.student_id}_{filename}"
            dest = os.path.join(sub_folder, filename)
            file.save(dest)
            # store relative path from static
            file_path = os.path.join('static', 'uploads', 'assignments', filename)

        submission = AssignmentSubmission(
            assessment_id=assessment_id,
            student_id=student.student_id,
            file_path=file_path,
            comment=comment,
            status='Submitted',
        )
        db.session.add(submission)
        db.session.commit()
        flash('Assignment submitted successfully.', 'success')
        return redirect(url_for('grades.entry', assessment_id=assessment_id))

    # GET
    # show student's enrollments and assessments
    courses = Course.query.all()
    assessments = Assessment.query.filter_by(assessment_type='Assignment').all()
    return render_template('assignment_submit.html', assessment=assessment, assessments=assessments)


# ---------------------------------------------------------------------------
# TEACHER: View submissions for an assessment and grade them
# ---------------------------------------------------------------------------
@grades_bp.route('/assignments/<int:assessment_id>/submissions', methods=['GET', 'POST'])
@login_required
@roles_required('teacher', 'admin')
def assignment_submissions(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)

    submissions = AssignmentSubmission.query.filter_by(assessment_id=assessment_id).all()

    if request.method == 'POST':
        submission_id = request.form.get('submission_id', type=int)
        marks = request.form.get('marks')
        remarks = request.form.get('remarks')
        sub = AssignmentSubmission.query.get_or_404(submission_id)
        sub.marks_awarded = float(marks) if marks not in (None, '') else None
        sub.status = 'Graded'
        sub.graded_by = current_user.user_id
        from datetime import datetime
        sub.graded_at = datetime.utcnow()
        db.session.commit()
        flash('Submission graded.', 'success')
        return redirect(url_for('grades.assignment_submissions', assessment_id=assessment_id))

    return render_template('assignment_submissions.html', assessment=assessment, submissions=submissions)
