from flask_login import UserMixin
from models import db
from models.location import District, Area


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    username = db.Column(db.String(50), unique=True, nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    phone = db.Column(db.String(20), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(
    db.Date,
    nullable=False
)

    profile_image = db.Column(
        db.String(255),
        default="default.png"
    )

    is_verified = db.Column(
        db.Boolean,
        default=False
    )
    verification_code = db.Column(
        db.String(6)
    )

    verification_expiry = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
    district_id = db.Column(
        db.Integer,
        db.ForeignKey("districts.id")
    )


    area_id = db.Column(
        db.Integer,
        db.ForeignKey("areas.id")
    )


    district = db.relationship(
        "District"
    )


    area = db.relationship(
        "Area"
    )
    reset_code = db.Column(
    db.String(6),
    nullable=True
)


    reset_expiry = db.Column(
        db.DateTime,
        nullable=True
    )

    def __repr__(self):
        return f"<User {self.username}>"