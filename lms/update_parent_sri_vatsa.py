from app import create_app
from app.extensions import db
from app.models import User, Student

app = create_app()
with app.app_context():
    parent = User.query.filter_by(username="gopinathn").first()
    student_user = User.query.filter_by(username="srivatsag").first()
    student = None
    if student_user:
        student = Student.query.filter_by(user_id=student_user.user_id).first()

    if not parent:
        print("Parent user gopinathn not found.")
    elif not student_user:
        print("Student user srivatsag not found.")
    elif not student:
        print("Student record for srivatsag not found.")
    else:
        student.parent_id = parent.user_id
        db.session.commit()
        print(
            "Updated parent relationship:",
            student.user.full_name,
            "-> parent:",
            parent.full_name,
        )
