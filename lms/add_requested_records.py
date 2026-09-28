from app import create_app
from app.extensions import db
from app.models import User, Department, Teacher, Student, ParentStudentLink


def create_user(username, role, full_name, email, password):
    user = User.query.filter_by(username=username).first()
    if user:
        return user, False
    user = User(username=username, role=role, full_name=full_name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user, True


def ensure_teacher(username, full_name, email, password, department):
    user, created = create_user(username, "teacher", full_name, email, password)
    teacher = Teacher.query.filter_by(user_id=user.user_id).first()
    if not teacher:
        teacher = Teacher(user_id=user.user_id, department_id=department.department_id, designation="Faculty")
        db.session.add(teacher)
    return user, teacher, created


def ensure_student(username, full_name, email, password, reg_no, department, parent_user=None):
    user, created = create_user(username, "student", full_name, email, password)
    student = Student.query.filter_by(user_id=user.user_id).first()
    if not student:
        student = Student(
            user_id=user.user_id,
            registration_no=reg_no,
            department_id=department.department_id,
            parent_id=parent_user.user_id if parent_user else None,
        )
        db.session.add(student)
    else:
        if parent_user is not None:
            student.parent_id = parent_user.user_id
    return user, student, created


def ensure_parent(username, full_name, email, password):
    return create_user(username, "parent", full_name, email, password)


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        dept = Department.query.filter_by(dept_code="CSE").first()
        if not dept:
            dept = Department(dept_code="CSE", dept_name="Computer Science")
            db.session.add(dept)
            db.session.flush()

        # Parents
        gopinath, _ = ensure_parent("gopinathn", "Gopinath N", "gopinathn@example.com", "Gopinath123")
        sivakami, _ = ensure_parent("sivakamig", "Sivakami G", "sivakamig@example.com", "Sivakami123")

        # Students
        sri_student = ensure_student(
            "srivatsag", "Sri vatsa G", "srivatsag@example.com", "SriVatsa123", "REG002", dept, parent_user=sivakami
        )
        shreya_student = ensure_student(
            "shreyars", "Shreya RS", "shreyars@example.com", "Shreya123", "REG003", dept
        )
        eswar_student = ensure_student(
            "esward", "Eswar D", "esward@example.com", "Eswar123", "REG004", dept
        )

        # Faculty
        ensure_teacher("nuzhat", "Nuzhat", "nuzhat@example.com", "Nuzhat123", dept)
        ensure_teacher("udhayad", "Udhaya", "udhayad@example.com", "Udhaya123", dept)

        db.session.commit()

        print("Added or updated the following records:")
        print("Students:")
        print(" - Sri vatsa G: username=srivatsag password=SriVatsa123 parent=Sivakami G")
        print(" - Shreya RS: username=shreyars password=Shreya123")
        print(" - Eswar D: username=esward password=Eswar123")
        print("Faculty:")
        print(" - Nuzhat: username=nuzhat password=Nuzhat123")
        print(" - Udhaya: username=udhayad password=Udhaya123")
        print("Parents:")
        print(" - Gopinath N: username=gopinathn password=Gopinath123")
        print(" - Sivakami G: username=sivakamig password=Sivakami123")
