from models import db


class Interview(db.Model):
    __tablename__ = "interviews"

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(
        db.Integer,
        db.ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    recruiter_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    scheduled_at = db.Column(db.DateTime, nullable=False, index=True)
    interview_type = db.Column(db.String(30), nullable=False, default="Online")
    meeting_link = db.Column(db.String(500), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="Scheduled", index=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    application = db.relationship(
        "Application",
        backref=db.backref("interviews", lazy=True, cascade="all, delete-orphan")
    )

    recruiter = db.relationship(
        "User",
        foreign_keys=[recruiter_id],
        backref=db.backref("scheduled_interviews", lazy=True)
    )

    def __repr__(self):
        return (
            f"<Interview id={self.id} "
            f"application_id={self.application_id} status={self.status}>"
        )
