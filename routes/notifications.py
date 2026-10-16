from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import db
from models.notification import Notification

notifications = Blueprint(
    "notifications",
    __name__,
    url_prefix="/notifications"
)


@notifications.route("/api", methods=["GET"])
@login_required
def get_notifications():
    items = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).limit(30).all()

    return jsonify({
        "notifications": [
            {
                "id": item.id,
                "title": item.title,
                "message": item.message,
                "type": item.notification_type,
                "is_read": item.is_read,
                "created_at": (
                    item.created_at.strftime("%d %b %Y, %I:%M %p")
                    if item.created_at else ""
                )
            }
            for item in items
        ],
        "unread_count": Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
    })


@notifications.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    item = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()

    item.is_read = True
    db.session.commit()

    return jsonify({"success": True})


@notifications.route("/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({"is_read": True})

    db.session.commit()

    return jsonify({"success": True})