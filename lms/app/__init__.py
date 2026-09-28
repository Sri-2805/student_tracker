from flask import Flask
from config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.dashboard_routes import dashboard_bp
    from app.blueprints.attendance.routes import attendance_bp
    from app.blueprints.grades.routes import grades_bp
    from app.blueprints.analytics.routes import analytics_bp
    from app.blueprints.parents.routes import parents_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.leave_od.routes import leave_od_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(attendance_bp, url_prefix="/attendance")
    app.register_blueprint(grades_bp, url_prefix="/grades")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(parents_bp, url_prefix="/messages")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(leave_od_bp, url_prefix="/leave-od")

    # Make current_user available with role helpers in templates
    from flask_login import current_user
    from app.models import Student

    @app.context_processor
    def inject_globals():
        current_student_id = None
        if current_user.is_authenticated and current_user.role == "student":
            s = Student.query.filter_by(user_id=current_user.user_id).first()
            current_student_id = s.student_id if s else None
        return {"current_user": current_user, "current_student_id": current_student_id}

    return app
