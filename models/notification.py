
from models import db


class Notification(db.Model):

    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # User who receives the notification
    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # Notification content
    title = db.Column(
        db.String(150),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False,
        default="general"
    )

    # Optional link to a related application
    application_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "applications.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # Read status
    is_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    # Relationships
    user = db.relationship(
        "User",
        backref=db.backref(
            "notifications",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    application = db.relationship(
        "Application",
        backref=db.backref(
            "notifications",
            lazy=True
        )
    )

    def __repr__(self):
        return (
            f"<Notification "
            f"id={self.id} "
            f"user_id={self.user_id} "
            f"is_read={self.is_read}>"
        )
