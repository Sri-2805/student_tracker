from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.models import User, Student, Teacher, Course, Department, Announcement
from app.utils.decorators import roles_required
from flask_login import current_user

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
@roles_required("admin")
def index():
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_courses = Course.query.count()
    total_announcements = Announcement.query.count()
    return render_template(
        "admin_index.html",
        total_students=total_students,
        total_teachers=total_teachers,
        total_courses=total_courses,
        total_announcements=total_announcements,
    )


@admin_bp.route("/users")
@login_required
@roles_required("admin")
def users():
    all_users = User.query.order_by(User.role).all()
    return render_template("admin_users.html", users=all_users)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def new_user():
    departments = Department.query.all()
    if request.method == "POST":
        user = User(
            username=request.form.get("username"),
            role=request.form.get("role"),
            full_name=request.form.get("full_name"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
        )
        user.set_password(request.form.get("password", "password123"))
        db.session.add(user)
        db.session.flush()  # get user.user_id before commit

        if user.role == "student":
            student = Student(
                user_id=user.user_id,
                registration_no=request.form.get("registration_no"),
                department_id=request.form.get("department_id", type=int),
                semester=request.form.get("semester", type=int),
                academic_year=request.form.get("academic_year"),
                total_credits=request.form.get("total_credits", type=int) or 0,
            )
            db.session.add(student)
        elif user.role == "teacher":
            teacher = Teacher(
                user_id=user.user_id,
                department_id=request.form.get("department_id", type=int),
                designation=request.form.get("designation"),
            )
            db.session.add(teacher)

        db.session.commit()
        flash(f"User '{user.username}' created.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin_user_new.html", departments=departments)


@admin_bp.route("/courses", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def courses():
    departments = Department.query.all()
    teachers = Teacher.query.all()

    if request.method == "POST":
        course = Course(
            course_code=request.form.get("course_code"),
            course_name=request.form.get("course_name"),
            department_id=request.form.get("department_id", type=int),
            semester=request.form.get("semester", type=int),
            credits=request.form.get("credits", type=int),
            academic_year=request.form.get("academic_year"),
            teacher_id=request.form.get("teacher_id", type=int),
        )
        db.session.add(course)
        db.session.commit()
        flash(f"Course '{course.course_name}' created.", "success")
        return redirect(url_for("admin.courses"))

    all_courses = Course.query.all()
    return render_template("admin_courses.html", courses=all_courses, departments=departments, teachers=teachers)


@admin_bp.route("/announcements", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def announcements():
    if request.method == "POST":
        ann = Announcement(
            title=request.form.get("title"),
            message=request.form.get("message"),
            posted_by=current_user.user_id,
            target_role=request.form.get("target_role", "all"),
        )
        db.session.add(ann)
        db.session.commit()
        flash("Announcement posted.", "success")
        return redirect(url_for("admin.announcements"))

    all_announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template("admin_announcements.html", announcements=all_announcements)
