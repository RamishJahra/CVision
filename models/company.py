
from models import db


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)

    company_name = db.Column(
        db.String(150),
        nullable=False
    )

    company_description = db.Column(db.Text, nullable=True)

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

    company_logo = db.Column(
        db.String(255),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # Multiple recruiters can belong to the same company.
    recruiters = db.relationship(
        "RecruiterProfile",
        back_populates="company"
    )

    # One shared location per company.
    location = db.relationship(
        "CompanyLocation",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Company {self.company_name}>"


class CompanyLocation(db.Model):
    __tablename__ = "company_locations"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        unique=True,
        nullable=False
    )

    address = db.Column(
        db.String(500),
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=True
    )

    longitude = db.Column(
        db.Float,
        nullable=True
    )

    google_maps_url = db.Column(
        db.String(1000),
        nullable=True
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    company = db.relationship(
        "Company",
        back_populates="location"
    )

    def __repr__(self):
        return f"<CompanyLocation {self.company_id}>"
