import os
from flask import Flask

from config import Config

from models import db, login_manager, mail
from models.user import User
from models.profile import (
    ApplicantProfile,
    RecruiterProfile,
    Education,
    WorkExperience,
    Skill,
    Certification,
    Project 
)
from models.location import District, Area

from routes.public import public
from routes.auth import auth
from routes.dashboard import dashboard
from routes.applicant import applicant
from routes.recruiter import recruiter

from werkzeug.security import generate_password_hash


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "uploads",
    "profile"
)

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)
# ==========================
# Load Configuration
# ==========================

app.config.from_object(Config)


# ==========================
# Initialize Extensions
# ==========================

db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)


# ==========================
# Flask-Login Configuration
# ==========================

login_manager.login_view = "auth.login"

login_manager.login_message = "Please log in to continue."

login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# ==========================
# Register Blueprints
# ==========================

app.register_blueprint(public)

app.register_blueprint(auth)

app.register_blueprint(dashboard)

app.register_blueprint(applicant)

app.register_blueprint(recruiter)


# ==========================
# Create Database Tables
# ==========================

with app.app_context():

    db.create_all()


    # ==========================
    # Create Default Admin
    # ==========================

    admin = User.query.filter_by(
        role="Admin"
    ).first()


    if not admin:

        admin = User(

            full_name="CVision Admin",

            username="admin",

            email="cvision190@gmail.com",

            phone="01813683227",

            date_of_birth="2005-03-20",

            password=generate_password_hash(
                "Admin@123"
            ),

            role="Admin",

            is_verified=True

        )


        db.session.add(admin)

        db.session.commit()


    # ==========================
    # Create Missing Applicant Profiles
    # ==========================

    applicants = User.query.filter_by(
        role="Applicant"
    ).all()


    for user in applicants:

        profile = ApplicantProfile.query.filter_by(
            user_id=user.id
        ).first()


        if not profile:

            profile = ApplicantProfile(
                user_id=user.id
            )

            db.session.add(profile)


    # ==========================
    # Create Missing Recruiter Profiles
    # ==========================

    recruiters = User.query.filter_by(
        role="Recruiter"
    ).all()


    for user in recruiters:

        profile = RecruiterProfile.query.filter_by(
            user_id=user.id
        ).first()


        if not profile:

            profile = RecruiterProfile(
                user_id=user.id
            )

            db.session.add(profile)


    # Save Profile Changes

    db.session.commit()


# ==========================
# Run Application
# ==========================

if __name__ == "__main__":

    app.run(
        debug=True
    )