from models import db


class ApplicantProfile(db.Model):
    __tablename__ = "applicant_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    bio = db.Column(
        db.Text,
        nullable=True
    )

    address = db.Column(
        db.String(255),
        nullable=True
    )

    linkedin_url = db.Column(
        db.String(255),
        nullable=True
    )

    github_url = db.Column(
        db.String(255),
        nullable=True
    )

    portfolio_url = db.Column(
        db.String(255),
        nullable=True
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "applicant_profile",
            uselist=False
        )
    )

    def __repr__(self):
        return f"<ApplicantProfile {self.user_id}>"

class Education(db.Model):

    __tablename__ = "educations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    degree = db.Column(
        db.String(150),
        nullable=False
    )

    institution = db.Column(
        db.String(200),
        nullable=False
    )

    field_of_study = db.Column(
        db.String(150),
        nullable=True
    )

    start_year = db.Column(
        db.Integer,
        nullable=True
    )

    end_year = db.Column(
        db.Integer,
        nullable=True
    )
    is_current = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    cgpa = db.Column(
        db.String(20),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


    user = db.relationship(
        "User",
        backref=db.backref(
            "educations",
            lazy=True
        )
    )


    def __repr__(self):

        return f"<Education {self.degree}>"

class WorkExperience(db.Model):

    __tablename__ = "work_experiences"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    job_title = db.Column(
        db.String(150),
        nullable=False
    )

    company_name = db.Column(
        db.String(200),
        nullable=False
    )

    employment_type = db.Column(
        db.String(50),
        nullable=True
    )

    location = db.Column(
        db.String(200),
        nullable=True
    )

    start_date = db.Column(
        db.Date,
        nullable=True
    )

    end_date = db.Column(
        db.Date,
        nullable=True
    )

    currently_working = db.Column(
        db.Boolean,
        default=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "work_experiences",
            lazy=True
        )
    )

    def __repr__(self):

        return f"<WorkExperience {self.job_title}>"

class Skill(db.Model):

    __tablename__ = "skills"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    skill_name = db.Column(
        db.String(100),
        nullable=False
    )

    proficiency = db.Column(
        db.String(50),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "skills",
            lazy=True
        )
    )

    def __repr__(self):

        return f"<Skill {self.skill_name}>"

class Certification(db.Model):

    __tablename__ = "certifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    certification_name = db.Column(
        db.String(200),
        nullable=False
    )

    issuing_organization = db.Column(
        db.String(200),
        nullable=False
    )

    issue_date = db.Column(
        db.Date,
        nullable=True
    )

    expiry_date = db.Column(
        db.Date,
        nullable=True
    )

    credential_id = db.Column(
        db.String(150),
        nullable=True
    )

    credential_url = db.Column(
        db.String(500),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "certifications",
            lazy=True
        )
    )

    def __repr__(self):

        return f"<Certification {self.certification_name}>"


class Project(db.Model):

    __tablename__ = "projects"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    project_title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    technologies = db.Column(
        db.String(500),
        nullable=True
    )

    project_url = db.Column(
        db.String(500),
        nullable=True
    )

    github_url = db.Column(
        db.String(500),
        nullable=True
    )

    start_date = db.Column(
        db.Date,
        nullable=True
    )

    end_date = db.Column(
        db.Date,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "projects",
            lazy=True
        )
    )

    def __repr__(self):

        return f"<Project {self.project_title}>"

    
class RecruiterProfile(db.Model):

    __tablename__ = "recruiter_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    # ==========================
    # Recruiter Information
    # ==========================

    job_title = db.Column(
        db.String(100),
        nullable=True
    )

    linkedin_url = db.Column(
        db.String(255),
        nullable=True
    )

    bio = db.Column(
        db.Text,
        nullable=True
    )

    # ==========================
    # Company Information
    # ==========================

    company_name = db.Column(
        db.String(150),
        nullable=True
    )

    company_description = db.Column(
        db.Text,
        nullable=True
    )

    company_website = db.Column(
        db.String(255),
        nullable=True
    )

    industry = db.Column(
        db.String(100),
        nullable=True
    )

    company_size = db.Column(
        db.String(50),
        nullable=True
    )

    company_location = db.Column(
        db.String(255),
        nullable=True
    )

    company_logo = db.Column(
        db.String(255),
        nullable=True
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "recruiter_profile",
            uselist=False
        )
    )

    def __repr__(self):

        return f"<RecruiterProfile {self.user_id}>"