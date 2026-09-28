from app import create_app
from app.extensions import db
from app.models import User, Student, ParentStudentLink

app = create_app()
with app.app_context():
    parent = User.query.filter_by(username="sivakamig").first()
    student_user = User.query.filter_by(username="srivatsag").first()
    if not parent:
        print("Parent user sivakamig not found.")
        raise SystemExit(1)
    if not student_user:
        print("Student user srivatsag not found.")
        raise SystemExit(1)

    student = Student.query.filter_by(user_id=student_user.user_id).first()
    if not student:
        print("Student record for srivatsag not found.")
        raise SystemExit(1)

    existing = ParentStudentLink.query.filter_by(parent_user_id=parent.user_id, student_id=student.student_id).first()
    if existing:
        print("Sivakami G is already linked as a parent for Sri vatsa G.")
    else:
        link = ParentStudentLink(parent_user_id=parent.user_id, student_id=student.student_id, relationship_type="Guardian")
        db.session.add(link)
        db.session.commit()
        print("Added Sivakami G as an additional parent for Sri vatsa G.")
