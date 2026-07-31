"""Bulk seeding script for students, teachers, and courses.

Usage examples:
  # generate 50 students, 10 teachers, 8 courses
  python seed_bulk.py --students 50 --teachers 10 --courses 8

  # import from CSV (CSV columns: type,username,full_name,email,role_specific)
  python seed_bulk.py --from-csv data.csv

This script is safe to run multiple times; it skips users with existing usernames.
"""
import argparse
import os
from app import create_app
from app.extensions import db
from app.models import User, Department, Teacher, Course, Student, Enrollment, Attendance
from datetime import datetime, timedelta


def ensure_department():
    dept = Department.query.filter_by(dept_code="GEN").first()
    if not dept:
        dept = Department(dept_code="GEN", dept_name="General")
        db.session.add(dept)
        db.session.flush()
    return dept


def create_teachers(count, start_index=1):
    dept = ensure_department()
    created = 0
    for i in range(start_index, start_index + count):
        username = f"teacher{i}"
        if User.query.filter_by(username=username).first():
            continue
        u = User(username=username, role="teacher", full_name=f"Teacher {i}", email=f"teacher{i}@example.com")
        u.set_password("password123")
        db.session.add(u)
        db.session.flush()
        t = Teacher(user_id=u.user_id, department_id=dept.department_id, designation="Lecturer")
        db.session.add(t)
        created += 1
    return created


def create_students(count, start_index=1):
    dept = ensure_department()
    created = 0
    for i in range(start_index, start_index + count):
        username = f"student{i}"
        if User.query.filter_by(username=username).first():
            continue
        u = User(username=username, role="student", full_name=f"Student {i}", email=f"student{i}@example.com")
        u.set_password("password123")
        db.session.add(u)
        db.session.flush()
        student = Student(user_id=u.user_id, registration_no=f"REG{i:04d}", department_id=dept.department_id)
        db.session.add(student)
        created += 1
    return created


def create_courses(count, start_index=1):
    dept = ensure_department()
    teachers = Teacher.query.all()
    created = 0
    for i in range(start_index, start_index + count):
        code = f"CSE{100 + i}"
        if Course.query.filter_by(course_code=code).first():
            continue
        teacher_id = teachers[(i - start_index) % len(teachers)].teacher_id if teachers else None
        course = Course(course_code=code, course_name=f"Course {code}", department_id=dept.department_id, teacher_id=teacher_id)
        db.session.add(course)
        created += 1
    return created


def create_enrollments(max_courses_per_student=3):
    students = Student.query.all()
    courses = Course.query.all()
    created = 0
    if not courses:
        return created

    for student in students:
        existing_course_ids = {en.course_id for en in Enrollment.query.filter_by(student_id=student.student_id).all()}
        available_courses = [c for c in courses if c.course_id not in existing_course_ids]
        course_count = min(max_courses_per_student, len(available_courses))
        for course in available_courses[:course_count]:
            enrollment = Enrollment(student_id=student.student_id, course_id=course.course_id, status="Active")
            db.session.add(enrollment)
            created += 1
    return created


def create_attendance(days=10, periods_per_day=2):
    students = Student.query.all()
    courses = Course.query.all()
    created = 0
    teachers = User.query.filter_by(role="teacher").all()
    if not courses or not teachers:
        return created

    start_date = datetime.utcnow().date() - timedelta(days=days)
    student_by_id = {s.student_id: s for s in students}
    for day_offset in range(days):
        attendance_date = start_date + timedelta(days=day_offset)
        for course in courses:
            enrolled_students = [en.student for en in Enrollment.query.filter_by(course_id=course.course_id).all()]
            teacher = User.query.filter_by(user_id=course.teacher_id).first() if course.teacher_id else teachers[0]
            for period in range(1, periods_per_day + 1):
                for student in enrolled_students:
                    status = "Present" if (student.student_id + day_offset + period) % 5 != 0 else "Absent"
                    record = Attendance(
                        student_id=student.student_id,
                        course_id=course.course_id,
                        attendance_date=attendance_date,
                        status=status,
                        period_no=period,
                        marked_by=teacher.user_id if teacher else 1,
                        remarks="Auto-generated"
                    )
                    db.session.add(record)
                    created += 1
    return created


def import_from_csv(path):
    import csv

    created = {"users": 0, "students": 0, "teachers": 0, "courses": 0}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rtype = row.get('type', '').strip().lower()
            username = row.get('username') or row.get('email')
            if not username:
                continue
            if User.query.filter_by(username=username).first():
                continue
            full_name = row.get('full_name') or username
            email = row.get('email') or f"{username}@example.com"
            if rtype == 'teacher':
                u = User(username=username, role='teacher', full_name=full_name, email=email)
                u.set_password(row.get('password') or 'password123')
                db.session.add(u)
                db.session.flush()
                t = Teacher(user_id=u.user_id, department_id=ensure_department().department_id, designation=row.get('designation','Lecturer'))
                db.session.add(t)
                created['teachers'] += 1
            elif rtype == 'student':
                u = User(username=username, role='student', full_name=full_name, email=email)
                u.set_password(row.get('password') or 'password123')
                db.session.add(u)
                db.session.flush()
                s = Student(user_id=u.user_id, registration_no=row.get('registration_no') or f"REGX", department_id=ensure_department().department_id)
                db.session.add(s)
                created['students'] += 1
            elif rtype == 'course':
                code = row.get('course_code') or row.get('code') or f"CSE{row.get('id','') }"
                if not Course.query.filter_by(course_code=code).first():
                    c = Course(course_code=code, course_name=row.get('course_name') or code, department_id=ensure_department().department_id)
                    db.session.add(c)
                    created['courses'] += 1
            else:
                # generic user
                u = User(username=username, role=row.get('role') or 'student', full_name=full_name, email=email)
                u.set_password(row.get('password') or 'password123')
                db.session.add(u)
                created['users'] += 1
    return created


def main():
    parser = argparse.ArgumentParser(description='Bulk seed students, teachers, and courses')
    parser.add_argument('--students', type=int, default=0, help='Number of students to create')
    parser.add_argument('--teachers', type=int, default=0, help='Number of teachers to create')
    parser.add_argument('--courses', type=int, default=0, help='Number of courses to create')
    parser.add_argument('--enrollments', action='store_true', help='Create enrollments for students')
    parser.add_argument('--attendance', action='store_true', help='Create attendance records for enrollments')
    parser.add_argument('--from-csv', dest='csv', help='Path to CSV file to import')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.csv:
            print(f"Importing from CSV: {args.csv}")
            res = import_from_csv(args.csv)
            db.session.commit()
            print("Import results:", res)
            return

        created = {"students": 0, "teachers": 0, "courses": 0, "enrollments": 0, "attendance": 0}
        if args.teachers:
            created['teachers'] = create_teachers(args.teachers)
        if args.students:
            created['students'] = create_students(args.students)
        if args.courses:
            # ensure we have teachers to assign
            if Teacher.query.count() == 0 and args.teachers == 0:
                print('No teachers exist; creating 3 default teachers to assign courses')
                create_teachers(3)
            created['courses'] = create_courses(args.courses)
        if args.enrollments:
            created['enrollments'] = create_enrollments()
        if args.attendance:
            if Enrollment.query.count() == 0:
                print('No enrollments found; creating enrollments before attendance')
                created['enrollments'] = create_enrollments()
            created['attendance'] = create_attendance()
        db.session.commit()
        print('Created:', created)


if __name__ == '__main__':
    main()
