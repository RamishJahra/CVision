
import os
import uuid
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_required, current_user
from flask_mail import Message
import random

from datetime import datetime, timedelta

from flask import session
from models import db, mail
from models.user import User
from models.location import District, Area
from models.profile import (
    ApplicantProfile,
    Education,
    WorkExperience,
    Skill,
    Certification,
    Project 
)

import re


applicant = Blueprint(
    "applicant",
    __name__,
    url_prefix="/applicant"
)


# ==========================
# Applicant Profile
# ==========================

@applicant.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    # Only Applicant can access
    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )


    # Find applicant profile
    profile = ApplicantProfile.query.filter_by(
        user_id=current_user.id
    ).first()


    # Safety check
    if not profile:

        profile = ApplicantProfile(
            user_id=current_user.id
        )

        db.session.add(profile)

        db.session.commit()


    # ==========================
    # Update Profile
    # ==========================

    if request.method == "POST":

        # ==========================
        # Personal Information
        # ==========================

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        date_of_birth = request.form.get(
            "date_of_birth"
        )

        district_id = request.form.get(
            "district_id"
        )

        area_id = request.form.get(
            "area_id"
        )


        # ==========================
        # Profile Information
        # ==========================

        profile.bio = request.form.get(
            "bio",
            ""
        ).strip()

        profile.address = request.form.get(
            "address",
            ""
        ).strip()

        profile.linkedin_url = request.form.get(
            "linkedin_url",
            ""
        ).strip()

        profile.github_url = request.form.get(
            "github_url",
            ""
        ).strip()

        profile.portfolio_url = request.form.get(
            "portfolio_url",
            ""
        ).strip()


        # ==========================
        # Username Duplicate Check
        # ==========================

        existing_username = User.query.filter(
            User.username == username,
            User.id != current_user.id
        ).first()


        if existing_username:

            flash(
                "Username already exists.",
                "danger"
            )

            return redirect(
                url_for("applicant.profile")
            )


        # ==========================
        # Phone Duplicate Check
        # ==========================

        existing_phone = User.query.filter(
            User.phone == phone,
            User.id != current_user.id
        ).first()


        if existing_phone:

            flash(
                "Phone number already exists.",
                "danger"
            )

            return redirect(
                url_for("applicant.profile")
            )


        # ==========================
        # Bangladesh Phone Validation
        # ==========================

        phone_pattern = r"^01[3-9]\d{8}$"


        if not re.match(
            phone_pattern,
            phone
        ):

            flash(
                "Invalid Bangladesh phone number.",
                "danger"
            )

            return redirect(
                url_for("applicant.profile")
            )


        # ==========================
        # Update User Information
        # ==========================

        current_user.full_name = full_name

        current_user.username = username

        current_user.phone = phone

        current_user.date_of_birth = date_of_birth

        current_user.district_id = district_id

        current_user.area_id = area_id


        # ==========================
        # Save Changes
        # ==========================

        db.session.commit()


        flash(
            "Profile updated successfully!",
            "success"
        )


        return redirect(
            url_for("applicant.profile")
        )


    # ==========================
    # Load Districts
    # ==========================

    districts = District.query.all()


    # ==========================
    # Load Areas
    # ==========================

    areas = []


    if current_user.district_id:

        areas = Area.query.filter_by(
            district_id=current_user.district_id
        ).all()


    # ==========================
    # Render Profile
    # ==========================

    return render_template(
        "applicant/profile.html",
        profile=profile,
        districts=districts,
        areas=areas
    )

# ==========================
# Add Education
# ==========================

@applicant.route("/education/add", methods=["POST"])
@login_required
def add_education():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )


    degree = request.form.get(
        "degree",
        ""
    ).strip()

    institution = request.form.get(
        "institution",
        ""
    ).strip()

    field_of_study = request.form.get(
        "field_of_study",
        ""
    ).strip()

    start_year = request.form.get(
        "start_year"
    )

    end_year = request.form.get(
        "end_year"
    )

    cgpa = request.form.get(
        "cgpa",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()


    if not degree or not institution:

        flash(
            "Degree and institution are required.",
            "danger"
        )

        return redirect(
            url_for("applicant.education")
        )


    education = Education(

        user_id=current_user.id,

        degree=degree,

        institution=institution,

        field_of_study=field_of_study,

        start_year=start_year,

        end_year=end_year,

        cgpa=cgpa,

        description=description
    )


    db.session.add(education)

    db.session.commit()


    flash(
        "Education added successfully!",
        "success"
    )


    return redirect(
        url_for("applicant.education")
    )


# ==========================
# Education Page
# ==========================

@applicant.route("/education")
@login_required
def education():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )


    educations = Education.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Education.start_year.desc()
    ).all()


    return render_template(
        "applicant/education.html",
        educations=educations
    )

# ==========================
# Work Experience Page
# ==========================

@applicant.route("/experience")
@login_required
def experience():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    experiences = WorkExperience.query.filter_by(
        user_id=current_user.id
    ).order_by(
        WorkExperience.start_date.desc()
    ).all()

    return render_template(
        "applicant/experience.html",
        experiences=experiences
    )


# ==========================
# Add Work Experience
# ==========================

@applicant.route("/experience/add", methods=["POST"])
@login_required
def add_experience():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    job_title = request.form.get(
        "job_title",
        ""
    ).strip()

    company_name = request.form.get(
        "company_name",
        ""
    ).strip()

    employment_type = request.form.get(
        "employment_type",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    start_date = request.form.get(
        "start_date"
    )

    end_date = request.form.get(
        "end_date"
    )

    currently_working = (
        request.form.get(
            "currently_working"
        ) == "on"
    )

    description = request.form.get(
        "description",
        ""
    ).strip()


    # Required fields

    if not job_title or not company_name:

        flash(
            "Job title and company name are required.",
            "danger"
        )

        return redirect(
            url_for("applicant.experience")
        )


    # Currently working means no end date

    if currently_working:

        end_date = None


    experience = WorkExperience(

        user_id=current_user.id,

        job_title=job_title,

        company_name=company_name,

        employment_type=employment_type,

        location=location,

        start_date=start_date,

        end_date=end_date,

        currently_working=currently_working,

        description=description
    )


    db.session.add(experience)

    db.session.commit()


    flash(
        "Work experience added successfully!",
        "success"
    )


    return redirect(
        url_for("applicant.experience")
    )

# ==========================
# Skills Page
# ==========================

@applicant.route("/skills")
@login_required
def skills():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    skills = Skill.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Skill.skill_name.asc()
    ).all()

    return render_template(
        "applicant/skills.html",
        skills=skills
    )


# ==========================
# Add Skill
# ==========================

@applicant.route("/skills/add", methods=["POST"])
@login_required
def add_skill():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    skill_name = request.form.get(
        "skill_name",
        ""
    ).strip()

    proficiency = request.form.get(
        "proficiency",
        ""
    ).strip()


    if not skill_name:

        flash(
            "Skill name is required.",
            "danger"
        )

        return redirect(
            url_for("applicant.skills")
        )


    # Prevent duplicate skill for same applicant

    existing_skill = Skill.query.filter(
        Skill.user_id == current_user.id,
        Skill.skill_name.ilike(skill_name)
    ).first()


    if existing_skill:

        flash(
            "This skill has already been added.",
            "warning"
        )

        return redirect(
            url_for("applicant.skills")
        )


    skill = Skill(

        user_id=current_user.id,

        skill_name=skill_name,

        proficiency=proficiency
    )


    db.session.add(skill)

    db.session.commit()


    flash(
        "Skill added successfully!",
        "success"
    )


    return redirect(
        url_for("applicant.skills")
    )

# ==========================
# Certifications Page
# ==========================

@applicant.route("/certifications")
@login_required
def certifications():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    certifications = Certification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Certification.issue_date.desc()
    ).all()

    return render_template(
        "applicant/certifications.html",
        certifications=certifications
    )


# ==========================
# Add Certification
# ==========================

@applicant.route(
    "/certifications/add",
    methods=["POST"]
)
@login_required
def add_certification():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    certification_name = request.form.get(
        "certification_name",
        ""
    ).strip()

    issuing_organization = request.form.get(
        "issuing_organization",
        ""
    ).strip()

    issue_date = request.form.get(
        "issue_date"
    )

    expiry_date = request.form.get(
        "expiry_date"
    )

    credential_id = request.form.get(
        "credential_id",
        ""
    ).strip()

    credential_url = request.form.get(
        "credential_url",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()


    if not certification_name or not issuing_organization:

        flash(
            "Certification name and issuing organization are required.",
            "danger"
        )

        return redirect(
            url_for("applicant.certifications")
        )


    certification = Certification(

        user_id=current_user.id,

        certification_name=certification_name,

        issuing_organization=issuing_organization,

        issue_date=issue_date,

        expiry_date=expiry_date,

        credential_id=credential_id,

        credential_url=credential_url,

        description=description
    )


    db.session.add(certification)

    db.session.commit()


    flash(
        "Certification added successfully!",
        "success"
    )


    return redirect(
        url_for("applicant.certifications")
    )

# ==========================
# Projects Page
# ==========================

@applicant.route("/projects")
@login_required
def projects():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    projects = Project.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Project.start_date.desc()
    ).all()

    return render_template(
        "applicant/projects.html",
        projects=projects
    )


# ==========================
# Add Project
# ==========================

@applicant.route(
    "/projects/add",
    methods=["POST"]
)
@login_required
def add_project():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    project_title = request.form.get(
        "project_title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    technologies = request.form.get(
        "technologies",
        ""
    ).strip()

    project_url = request.form.get(
        "project_url",
        ""
    ).strip()

    github_url = request.form.get(
        "github_url",
        ""
    ).strip()

    start_date = request.form.get(
        "start_date"
    )

    end_date = request.form.get(
        "end_date"
    )


    if not project_title:

        flash(
            "Project title is required.",
            "danger"
        )

        return redirect(
            url_for("applicant.projects")
        )


    project = Project(

        user_id=current_user.id,

        project_title=project_title,

        description=description,

        technologies=technologies,

        project_url=project_url,

        github_url=github_url,

        start_date=start_date,

        end_date=end_date
    )


    db.session.add(project)

    db.session.commit()


    flash(
        "Project added successfully!",
        "success"
    )


    return redirect(
        url_for("applicant.projects")
    )

# ==========================
# Profile Picture Upload
# ==========================

@applicant.route(
    "/profile-picture",
    methods=["POST"]
)
@login_required
def profile_picture():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    file = request.files.get(
        "profile_image"
    )

    if not file or file.filename == "":

        flash(
            "Please select an image.",
            "danger"
        )

        return redirect(
            url_for("applicant.profile")
        )


    # Allowed extensions

    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }


    filename = file.filename

    extension = filename.rsplit(
        ".",
        1
    )[-1].lower()


    if extension not in allowed_extensions:

        flash(
            "Only JPG, JPEG, PNG and WEBP images are allowed.",
            "danger"
        )

        return redirect(
            url_for("applicant.profile")
        )


    # Generate unique filename

    new_filename = (
        str(uuid.uuid4())
        + "."
        + extension
    )


    upload_folder = current_app.config[
        "UPLOAD_FOLDER"
    ]


    file_path = os.path.join(
        upload_folder,
        new_filename
    )


    # Save image

    file.save(file_path)


    # Delete old custom image

    old_image = current_user.profile_image

    if old_image and old_image != "default.png":

        old_path = os.path.join(
            upload_folder,
            old_image
        )

        if os.path.exists(old_path):

            os.remove(old_path)


    # Update database

    current_user.profile_image = new_filename

    db.session.commit()


    flash(
        "Profile picture updated successfully!",
        "success"
    )


    return redirect(
        url_for("applicant.profile")
    )

# ==========================
# Account Settings
# ==========================

@applicant.route("/settings")
@login_required
def settings():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    return render_template(
        "applicant/settings.html"
    )


# ==========================
# Change Password
# ==========================

@applicant.route(
    "/settings/change-password",
    methods=["POST"]
)
@login_required
def change_password():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    # Check current password

    if not check_password_hash(
        current_user.password,
        current_password
    ):

        flash(
            "Current password is incorrect.",
            "danger"
        )

        return redirect(
            url_for("applicant.settings")
        )


    # Check new password

    if len(new_password) < 8:

        flash(
            "New password must contain at least 8 characters.",
            "danger"
        )

        return redirect(
            url_for("applicant.settings")
        )


    # Confirm password

    if new_password != confirm_password:

        flash(
            "New passwords do not match.",
            "danger"
        )

        return redirect(
            url_for("applicant.settings")
        )


    # Prevent same password

    if check_password_hash(
        current_user.password,
        new_password
    ):

        flash(
            "New password must be different from your current password.",
            "warning"
        )

        return redirect(
            url_for("applicant.settings")
        )


    current_user.password = generate_password_hash(
        new_password
    )

    db.session.commit()


    flash(
        "Password changed successfully!",
        "success"
    )


    return redirect(
        url_for("applicant.settings")
    )


# ==========================
# Change Email
# ==========================

@applicant.route(
    "/settings/change-email",
    methods=["POST"]
)
@login_required
def change_email():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    new_email = request.form.get(
        "new_email",
        ""
    ).strip().lower()


    # Check empty email

    if not new_email:

        flash(
            "Please enter a new email address.",
            "danger"
        )

        return redirect(
            url_for("applicant.settings")
        )


    # Check duplicate email

    existing_email = User.query.filter(
        User.email == new_email,
        User.id != current_user.id
    ).first()


    if existing_email:

        flash(
            "This email address is already in use.",
            "danger"
        )

        return redirect(
            url_for("applicant.settings")
        )


    # Check same email

    if new_email == current_user.email.lower():

        flash(
            "This is already your current email address.",
            "warning"
        )

        return redirect(
            url_for("applicant.settings")
        )


    # ==========================
    # Generate Verification Code
    # ==========================

    verification_code = str(
        random.randint(100000, 999999)
    )

    current_user.verification_code = verification_code

    current_user.verification_expiry = (
        datetime.utcnow()
        + timedelta(minutes=10)
    )


    # Store pending email

    session["pending_email"] = new_email

    db.session.commit()


    # ==========================
    # Send Verification Email
    # ==========================

    try:

        msg = Message(
            subject="CVision - Verify Your New Email",
            sender=current_app.config["MAIL_USERNAME"],
            recipients=[new_email]
        )

        msg.body = f"""
Hello {current_user.full_name},

You requested to change your email address on CVision.

Your verification code is:

{verification_code}

This code will expire in 10 minutes.

If you did not request this change, please ignore this email.

Regards,
CVision Team
"""

        mail.send(msg)


    except Exception as e:

        print("=" * 60)
        print("EMAIL SENDING ERROR:")
        print(repr(e))
        print("=" * 60)


        current_user.verification_code = None

        current_user.verification_expiry = None

        session.pop(
            "pending_email",
            None
        )

        db.session.commit()


        flash(
            "Unable to send verification email. Please try again.",
            "danger"
        )

        return redirect(
            url_for("applicant.settings")
        )


    # ==========================
    # Email Sent Successfully
    # ==========================

    flash(
        "A verification code has been sent to your new email address.",
        "success"
    )


    return redirect(
        url_for("applicant.verify_new_email")
    )
# ==========================
# Verify New Email
# ==========================

@applicant.route(
    "/settings/verify-email",
    methods=["GET", "POST"]
)
@login_required
def verify_new_email():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )


    pending_email = session.get(
        "pending_email"
    )


    if not pending_email:

        flash(
            "No email change request found.",
            "warning"
        )

        return redirect(
            url_for("applicant.settings")
        )


    if request.method == "POST":

        code = request.form.get(
            "verification_code",
            ""
        ).strip()


        # Check expiry

        if (
            not current_user.verification_expiry
            or datetime.utcnow()
            > current_user.verification_expiry
        ):

            flash(
                "Verification code has expired.",
                "danger"
            )

            return redirect(
                url_for("applicant.settings")
            )


        # Check code

        if code != current_user.verification_code:

            flash(
                "Invalid verification code.",
                "danger"
            )

            return redirect(
                url_for("applicant.verify_new_email")
            )


        # Change email

        current_user.email = pending_email

        current_user.verification_code = None

        current_user.verification_expiry = None

        current_user.is_verified = True


        db.session.commit()


        session.pop(
            "pending_email",
            None
        )


        flash(
            "Email address updated successfully!",
            "success"
        )


        return redirect(
            url_for("applicant.settings")
        )


    return render_template(
        "applicant/verify_new_email.html",
        pending_email=pending_email
    )