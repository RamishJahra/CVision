
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
from models.resume import Resume
from models.application import Application
from models.notification import Notification
from models.company import Company, CompanyLocation
from models.social import SocialPost, SocialComment, SocialReaction
from models.interview import Interview
from models.feedback import Feedback

from routes.notifications import notifications
from routes.public import public
from routes.auth import auth
from routes.dashboard import dashboard
from routes.applicant import applicant
from routes.recruiter import recruiter
from routes.admin import admin
from routes.social import social
from routes.interviews import interviews
from routes.feedback import feedback
from services.cloudinary_service import get_image_url


app = Flask(__name__)

@app.context_processor
def inject_image_helpers():
    return {
        "cloudinary_image": get_image_url
    }
# Load configuration first.
app.config.from_object(Config)

# Upload directories.
app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path, "static", "uploads", "profile"
)

app.config["RESUME_UPLOAD_FOLDER"] = os.path.join(
    app.root_path, "static", "uploads", "resumes"
)

app.config["SOCIAL_UPLOAD_FOLDER"] = os.path.join(
    app.root_path, "static", "uploads", "social"
)

for folder in (
    app.config["UPLOAD_FOLDER"],
    app.config["RESUME_UPLOAD_FOLDER"],
    app.config["SOCIAL_UPLOAD_FOLDER"]
):
    os.makedirs(folder, exist_ok=True)


# Initialize extensions.
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)


# Flask-Login configuration.
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Register blueprints.
app.register_blueprint(public)
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(applicant)
app.register_blueprint(recruiter)
app.register_blueprint(admin)
app.register_blueprint(notifications)
app.register_blueprint(social)
app.register_blueprint(interviews)
app.register_blueprint(feedback)


# Database initialization and profile repair.
with app.app_context():

    db.create_all()

    applicants = User.query.filter_by(role="Applicant").all()

    for user in applicants:
        profile = ApplicantProfile.query.filter_by(
            user_id=user.id
        ).first()

        if not profile:
            db.session.add(ApplicantProfile(user_id=user.id))

    recruiters = User.query.filter_by(role="Recruiter").all()

    for user in recruiters:
        profile = RecruiterProfile.query.filter_by(
            user_id=user.id
        ).first()

        if not profile:
            db.session.add(RecruiterProfile(user_id=user.id))

    db.session.commit()


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
