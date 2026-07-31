"""
Reusable data-access / aggregation helpers used by the dashboard, analytics,
and parent-communication blueprints. Keeping this logic in one place avoids
duplicating SQL across modules.
"""
from sqlalchemy import func, case
from app.extensions import db
from app.models import Attendance, Course, Grade, Assessment, Student, User


def get_attendance_summary_for_student(student_id):
    """Returns a list of dicts: course_name, total_classes, attended, percent."""
    rows = (
        db.session.query(
            Course.course_id,
            Course.course_code,
            Course.course_name,
            func.count(Attendance.attendance_id).label("total_classes"),
            func.sum(
                case((Attendance.status.in_(["Present", "Late"]), 1), else_=0)
            ).label("attended"),
        )
        .join(Attendance, Attendance.course_id == Course.course_id)
        .filter(Attendance.student_id == student_id)
        .group_by(Course.course_id, Course.course_code, Course.course_name)
        .all()
    )

    summary = []
    for r in rows:
        total = r.total_classes or 0
        attended = r.attended or 0
        percent = round((attended / total) * 100, 2) if total else 0.0
        summary.append({
            "course_id": r.course_id,
            "course_code": r.course_code,
            "course_name": r.course_name,
            "total_classes": total,
            "attended": attended,
            "percent": percent,
        })
    return summary


def get_grade_summary_for_student(student_id):
    """Returns weighted grade percentage per course for a student."""
    rows = (
        db.session.query(
            Course.course_id,
            Course.course_code,
            Course.course_name,
            Grade.marks_obtained,
            Assessment.max_marks,
            Assessment.weight_percent,
            Assessment.title,
            Assessment.assessment_type,
        )
        .join(Assessment, Assessment.course_id == Course.course_id)
        .join(Grade, (Grade.assessment_id == Assessment.assessment_id) & (Grade.student_id == student_id))
        .all()
    )

    course_map = {}
    for r in rows:
        cid = r.course_id
        if cid not in course_map:
            course_map[cid] = {
                "course_id": cid,
                "course_code": r.course_code,
                "course_name": r.course_name,
                "weighted_sum": 0.0,
                "weight_total": 0.0,
                "assessments": [],
            }
        if r.marks_obtained is not None and r.max_marks:
            pct_of_assessment = float(r.marks_obtained) / float(r.max_marks)
            course_map[cid]["weighted_sum"] += pct_of_assessment * float(r.weight_percent or 0)
            course_map[cid]["weight_total"] += float(r.weight_percent or 0)
        course_map[cid]["assessments"].append({
            "title": r.title,
            "type": r.assessment_type,
            "marks_obtained": r.marks_obtained,
            "max_marks": r.max_marks,
        })

    summary = []
    for cid, data in course_map.items():
        final_pct = (
            round((data["weighted_sum"] / data["weight_total"]) * 100, 2)
            if data["weight_total"] else 0.0
        )
        summary.append({
            "course_id": cid,
            "course_code": data["course_code"],
            "course_name": data["course_name"],
            "final_percent": final_pct,
            "assessments": data["assessments"],
        })
    return summary


def get_at_risk_students(attendance_threshold=75.0, grade_threshold=50.0):
    """Cross-course average attendance/grade per student; flags at-risk students."""
    students = Student.query.all()
    at_risk = []
    for s in students:
        att = get_attendance_summary_for_student(s.student_id)
        grd = get_grade_summary_for_student(s.student_id)
        avg_att = round(sum(a["percent"] for a in att) / len(att), 2) if att else 0.0
        avg_grd = round(sum(g["final_percent"] for g in grd) / len(grd), 2) if grd else 0.0
        if avg_att < attendance_threshold or avg_grd < grade_threshold:
            at_risk.append({
                "student": s,
                "avg_attendance": avg_att,
                "avg_grade": avg_grd,
            })
    return at_risk
