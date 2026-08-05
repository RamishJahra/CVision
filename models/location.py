from models import db


class District(db.Model):

    __tablename__ = "districts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    areas = db.relationship(
        "Area",
        backref="district",
        lazy=True
    )


class Area(db.Model):

    __tablename__ = "areas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    district_id = db.Column(
        db.Integer,
        db.ForeignKey("districts.id"),
        nullable=False
    )