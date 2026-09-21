from models import db


class Job(db.Model):

    __tablename__ = "jobs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    recruiter_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    job_title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    job_type = db.Column(
        db.String(50),
        nullable=False
    )

    experience_required = db.Column(
        db.String(100),
        nullable=True
    )

    education_required = db.Column(
        db.String(255),
        nullable=True
    )

    skills_required = db.Column(
        db.Text,
        nullable=True
    )

    location = db.Column(
        db.String(255),
        nullable=True
    )

    salary = db.Column(
        db.String(100),
        nullable=True
    )

    application_deadline = db.Column(
        db.Date,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="Published",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    recruiter = db.relationship(
        "User",
        backref=db.backref(
            "jobs",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<Job {self.job_title}>"