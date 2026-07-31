from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, and_

from app.extensions import db
from app.models import Message, User, Student, Notification

parents_bp = Blueprint("parents", __name__)


@parents_bp.route("/")
@login_required
def inbox():
    messages = (
        Message.query.filter(
            or_(Message.sender_id == current_user.user_id, Message.receiver_id == current_user.user_id)
        )
        .order_by(Message.sent_at.desc())
        .all()
    )
    return render_template("messages_inbox.html", messages=messages)


@parents_bp.route("/compose", methods=["GET", "POST"])
@login_required
def compose():
    # Build list of valid recipients depending on role
    if current_user.role == "parent":
        children = Student.query.filter_by(parent_id=current_user.user_id).all()
        recipients = User.query.filter(User.role.in_(["teacher", "admin"])).all()
    elif current_user.role == "teacher":
        children = []
        recipients = User.query.filter(User.role == "parent").all()
    else:
        children = []
        recipients = User.query.filter(User.role.in_(["parent", "teacher"])).all()

    if request.method == "POST":
        msg = Message(
            sender_id=current_user.user_id,
            receiver_id=request.form.get("receiver_id", type=int),
            student_id=request.form.get("student_id", type=int) or None,
            subject=request.form.get("subject"),
            body=request.form.get("body"),
        )
        db.session.add(msg)
        db.session.add(Notification(
            user_id=msg.receiver_id,
            title=f"New message: {msg.subject}",
            body=f"From {current_user.full_name}",
            notif_type="message",
        ))
        db.session.commit()
        flash("Message sent.", "success")
        return redirect(url_for("parents.inbox"))

    return render_template("messages_compose.html", recipients=recipients, children=children)


@parents_bp.route("/thread/<int:message_id>")
@login_required
def thread(message_id):
    msg = Message.query.get_or_404(message_id)
    if current_user.user_id not in (msg.sender_id, msg.receiver_id):
        abort(403)
    if msg.receiver_id == current_user.user_id and not msg.is_read:
        msg.is_read = True
        db.session.commit()
    return render_template("messages_thread.html", msg=msg)
