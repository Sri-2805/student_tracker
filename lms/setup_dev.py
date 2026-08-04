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

        # Ensure department exists
        dept = Department.query.filter_by(dept_code="CSE").first()
        if not dept:
            dept = Department(dept_code="CSE", dept_name="Computer Science")
            db.session.add(dept)
            db.session.flush()

        # Ensure teacher exists
        t_user = User.query.filter_by(username="teacher1").first()
        if not t_user:
            t_user = User(username="teacher1", role="teacher", full_name="Teacher One", email="teacher1@example.com")
            t_user.set_password("password123")
            db.session.add(t_user)
            db.session.flush()

        teacher = Teacher.query.filter_by(user_id=t_user.user_id).first()
        if not teacher:
            teacher = Teacher(user_id=t_user.user_id, department_id=dept.department_id, designation="Lecturer")
            db.session.add(teacher)

        # Ensure course exists
        course = Course.query.filter_by(course_code="CSE101").first()
        if not course:
            course = Course(
                course_code="CSE101",
                course_name="Intro to CS",
                department_id=dept.department_id,
                teacher_id=teacher.teacher_id,
            )
            db.session.add(course)

        # Ensure parent exists
        parent_user = User.query.filter_by(username="parent1").first()
        if not parent_user:
            parent_user = User(username="parent1", role="parent", full_name="Parent One", email="parent1@example.com")
            parent_user.set_password("password123")
            db.session.add(parent_user)
            db.session.flush()

        # Ensure student exists and is linked to parent
        s_user = User.query.filter_by(username="student1").first()
        if not s_user:
            s_user = User(username="student1", role="student", full_name="Student One", email="student1@example.com")
            s_user.set_password("password123")
            db.session.add(s_user)
            db.session.flush()

        student = Student.query.filter_by(user_id=s_user.user_id).first()
        if not student:
            student = Student(
                user_id=s_user.user_id,
                registration_no="REG001",
                department_id=dept.department_id,
                parent_id=parent_user.user_id,
            )
            db.session.add(student)
        else:
            student.parent_id = parent_user.user_id

        db.session.commit()
        print(
            "Seeding complete. Users: admin/adminpass, teacher1/password123, student1/password123, parent1/password123"
        )


if __name__ == "__main__":
    seed_db()
