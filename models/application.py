from models import db


class Application(db.Model):

    __tablename__ = "applications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================================
    # Job
    # ==========================================

    job_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "jobs.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # ==========================================
    # Applicant
    # ==========================================

    applicant_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # ==========================================
    # Application Information
    # ==========================================

    cover_letter = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Pending"
    )

    applied_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # ==========================================
    # Relationships
    # ==========================================

    job = db.relationship(
        "Job",
        backref=db.backref(
            "applications",
            lazy=True,
            passive_deletes=True
        )
    )

    applicant = db.relationship(
        "User",
        backref=db.backref(
            "applications",
            lazy=True,
            passive_deletes=True
        )
    )

    # ==========================================
    # Prevent Duplicate Applications
    # ==========================================

    __table_args__ = (
        db.UniqueConstraint(
            "job_id",
            "applicant_id",
            name="unique_job_applicant"
        ),
    )

    def __repr__(self):

        return (
            f"<Application "
            f"job={self.job_id} "
            f"applicant={self.applicant_id}>"
        )