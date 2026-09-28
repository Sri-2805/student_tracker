from app import create_app
from app.extensions import db
from app.models import User, Student, Course, Enrollment

app = create_app()
with app.app_context():
    course = Course.query.filter_by(course_code="34121P11").first()
    if not course:
        print("Mini Project course not found (34121P11).")
        raise SystemExit(1)

    student_usernames = ["srivatsag", "shreyars", "esward"]
    for username in student_usernames:
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Student user {username} not found.")
            continue
        student = Student.query.filter_by(user_id=user.user_id).first()
        if not student:
            print(f"Student record for {username} not found.")
            continue

        enrollment = Enrollment.query.filter_by(student_id=student.student_id, course_id=course.course_id).first()
        if enrollment:
            print(f"{user.full_name} is already enrolled in {course.course_name}.")
            continue

        enrollment = Enrollment(
            student_id=student.student_id,
            course_id=course.course_id,
            status="Active",
        )
        db.session.add(enrollment)
        print(f"Enrolled {user.full_name} in {course.course_name}.")

    db.session.commit()
    print("Enrollment update complete.")
