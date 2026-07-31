from app import create_app
from app.extensions import db
from app.models import User, Department, Teacher, Course, Student


def seed_db():
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        # Admin user
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", role="admin", full_name="Administrator", email="admin@example.com")
            admin.set_password("adminpass")
            db.session.add(admin)

        # Sample department, teacher, course, and student
        if not Department.query.filter_by(dept_code="CSE").first():
            dept = Department(dept_code="CSE", dept_name="Computer Science")
            db.session.add(dept)
            db.session.flush()

            t_user = User(username="teacher1", role="teacher", full_name="Teacher One", email="teacher1@example.com")
            t_user.set_password("password123")
            db.session.add(t_user)
            db.session.flush()

            teacher = Teacher(user_id=t_user.user_id, department_id=dept.department_id, designation="Lecturer")
            db.session.add(teacher)
            db.session.flush()

            course = Course(course_code="CSE101", course_name="Intro to CS", department_id=dept.department_id, teacher_id=teacher.teacher_id)
            db.session.add(course)

            s_user = User(username="student1", role="student", full_name="Student One", email="student1@example.com")
            s_user.set_password("password123")
            db.session.add(s_user)
            db.session.flush()

            student = Student(user_id=s_user.user_id, registration_no="REG001", department_id=dept.department_id)
            db.session.add(student)

        db.session.commit()
        print("Seeding complete. Users: admin/adminpass, teacher1/password123, student1/password123")


if __name__ == "__main__":
    seed_db()
