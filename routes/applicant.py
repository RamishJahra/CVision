
import os
import uuid
import fitz
from docx import Document
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    current_app
)
from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from werkzeug.utils import secure_filename
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
from models.resume import Resume
from models.job import Job
from models.application import Application
from sqlalchemy import func
from services.resume_parser import parse_resume
from services.resume_scorer import calculate_resume_score
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
# ============================================================
# Resume Text Extraction
# ============================================================

def extract_text_from_pdf(file_path):

    text = ""

    try:

        document = fitz.open(file_path)

        for page in document:

            text += page.get_text()

            text += "\n"

        document.close()

    except Exception as e:

        print(
            "PDF text extraction error:",
            repr(e)
        )

        return None

    return text.strip()


def extract_text_from_docx(file_path):

    text = ""

    try:

        document = Document(file_path)

        for paragraph in document.paragraphs:

            if paragraph.text.strip():

                text += paragraph.text

                text += "\n"

        # Extract text from tables as well

        for table in document.tables:

            for row in table.rows:

                row_text = []

                for cell in row.cells:

                    cell_text = cell.text.strip()

                    if cell_text:

                        row_text.append(
                            cell_text
                        )

                if row_text:

                    text += " | ".join(
                        row_text
                    )

                    text += "\n"

    except Exception as e:

        print(
            "DOCX text extraction error:",
            repr(e)
        )

        return None

    return text.strip()


def extract_resume_text(
    file_path,
    file_type
):

    if file_type == "pdf":

        return extract_text_from_pdf(
            file_path
        )

    if file_type == "docx":

        return extract_text_from_docx(
            file_path
        )

    return None
# ============================================================
# Resume Management
# ============================================================

ALLOWED_RESUME_EXTENSIONS = {
    "pdf",
    "docx"
}

MAX_RESUME_SIZE = 5 * 1024 * 1024


def allowed_resume_file(filename):

    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_RESUME_EXTENSIONS


# ============================================================
# Resume Management Page
# ============================================================

@applicant.route("/resumes")
@login_required
def resumes():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    resumes = Resume.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Resume.uploaded_at.desc()
    ).all()

    return render_template(
        "applicant/resumes.html",
        resumes=resumes
    )


# ============================================================
# Upload Resume
# ============================================================

@applicant.route(
    "/resumes/upload",
    methods=["POST"]
)
@login_required
def upload_resume():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    file = request.files.get(
        "resume"
    )

    # --------------------------------------------
    # Check file
    # --------------------------------------------

    if not file or file.filename == "":

        flash(
            "Please select a resume to upload.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    # --------------------------------------------
    # Check extension
    # --------------------------------------------

    if not allowed_resume_file(
        file.filename
    ):

        flash(
            "Only PDF and DOCX resume files are allowed.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    # --------------------------------------------
    # Check file size
    # --------------------------------------------

    file.seek(
        0,
        os.SEEK_END
    )

    file_size = file.tell()

    file.seek(
        0
    )

    if file_size > MAX_RESUME_SIZE:

        flash(
            "Resume file size must not exceed 5 MB.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    # --------------------------------------------
    # Secure original filename
    # --------------------------------------------

    original_filename = secure_filename(
        file.filename
    )

    extension = original_filename.rsplit(
        ".",
        1
    )[1].lower()

    # --------------------------------------------
    # Generate unique filename
    # --------------------------------------------

    unique_filename = (
        str(uuid.uuid4())
        + "."
        + extension
    )

    # --------------------------------------------
    # Resume upload folder
    # --------------------------------------------

    upload_folder = current_app.config[
        "RESUME_UPLOAD_FOLDER"
    ]

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    file_path = os.path.join(
        upload_folder,
        unique_filename
    )

    # --------------------------------------------
    # Save file
    # --------------------------------------------

    try:

        file.save(
            file_path
        )

    except Exception as e:

        print(
            "Resume upload error:",
            repr(e)
        )

        flash(
            "Unable to upload the resume. Please try again.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    # --------------------------------------------
    # Check whether applicant already has
    # an active resume
    # --------------------------------------------

    active_resume = Resume.query.filter_by(
        user_id=current_user.id,
        status="active"
    ).first()

    # --------------------------------------------
    # First resume becomes active automatically
    # --------------------------------------------

    resume_status = "active"

    if active_resume:

        resume_status = "inactive"



   # --------------------------------------------
# Extract resume text
# --------------------------------------------

    extracted_text = extract_resume_text(
        file_path,
        extension
    )

    if extracted_text is None:

        # Remove uploaded file if extraction failed

        if os.path.exists(file_path):

            try:

                os.remove(file_path)

            except Exception as e:

                print(
                    "Uploaded resume cleanup error:",
                    repr(e)
                )

        flash(
            "Unable to read the resume. Please make sure the file is a valid PDF or DOCX.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )


    # --------------------------------------------
    # Create database record
    # --------------------------------------------

    resume = Resume(

        user_id=current_user.id,

        file_name=original_filename,

        file_path=unique_filename,

        file_type=extension,

        extracted_text=extracted_text,

        status=resume_status
    )

    db.session.add(
        resume
    )

    db.session.commit()

    flash(
        "Resume uploaded successfully!",
        "success"
    )

    return redirect(
        url_for("applicant.resumes")
    )


# ============================================================
# View / Download Resume
# ============================================================

@applicant.route(
    "/resumes/view/<int:resume_id>"
)
@login_required
def view_resume(resume_id):

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    resume = Resume.query.filter_by(
        id=resume_id,
        user_id=current_user.id
    ).first()

    if not resume:

        flash(
            "Resume not found.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    upload_folder = current_app.config[
        "RESUME_UPLOAD_FOLDER"
    ]

    file_path = os.path.join(
        upload_folder,
        resume.file_path
    )

    if not os.path.exists(file_path):

        flash(
            "Resume file could not be found.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    from flask import send_from_directory

    return send_from_directory(
        upload_folder,
        resume.file_path,
        as_attachment=False
    )


# ============================================================
# Set Active Resume
# ============================================================

@applicant.route(
    "/resumes/set-active/<int:resume_id>",
    methods=["POST"]
)
@login_required
def set_active_resume(resume_id):

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    resume = Resume.query.filter_by(
        id=resume_id,
        user_id=current_user.id
    ).first()

    if not resume:

        flash(
            "Resume not found.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    # --------------------------------------------
    # Make all applicant resumes inactive
    # --------------------------------------------

    Resume.query.filter_by(
        user_id=current_user.id
    ).update(
        {
            "status": "inactive"
        }
    )

    # --------------------------------------------
    # Make selected resume active
    # --------------------------------------------

    resume.status = "active"

    db.session.commit()

    flash(
        "Active resume updated successfully!",
        "success"
    )

    return redirect(
        url_for("applicant.resumes")
    )


# ============================================================
# Delete Resume
# ============================================================

@applicant.route(
    "/resumes/delete/<int:resume_id>",
    methods=["POST"]
)
@login_required
def delete_resume(resume_id):

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    resume = Resume.query.filter_by(
        id=resume_id,
        user_id=current_user.id
    ).first()

    if not resume:

        flash(
            "Resume not found.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    # --------------------------------------------
    # Store file path before deleting database row
    # --------------------------------------------

    upload_folder = current_app.config[
        "RESUME_UPLOAD_FOLDER"
    ]

    file_path = os.path.join(
        upload_folder,
        resume.file_path
    )

    was_active = (
        resume.status == "active"
    )

    # --------------------------------------------
    # Delete physical file
    # --------------------------------------------

    if os.path.exists(file_path):

        try:

            os.remove(
                file_path
            )

        except Exception as e:

            print(
                "Resume file deletion error:",
                repr(e)
            )

    # --------------------------------------------
    # Delete database record
    # --------------------------------------------

    db.session.delete(
        resume
    )

    db.session.commit()

    # --------------------------------------------
    # If active resume was deleted,
    # automatically activate the newest remaining one
    # --------------------------------------------

    if was_active:

        remaining_resume = Resume.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Resume.uploaded_at.desc()
        ).first()

        if remaining_resume:

            Resume.query.filter_by(
                user_id=current_user.id
            ).update(
                {
                    "status": "inactive"
                }
            )

            remaining_resume.status = "active"

            db.session.commit()

    flash(
        "Resume deleted successfully.",
        "success"
    )

    return redirect(
        url_for("applicant.resumes")
    )
# ============================================================
# Analyze Resume
# ============================================================

@applicant.route(
    "/resumes/analyze/<int:resume_id>"
)
@login_required
def analyze_resume(resume_id):

    if current_user.role != "Applicant":
        return redirect(
            url_for("dashboard.home")
        )

    resume = Resume.query.filter_by(
        id=resume_id,
        user_id=current_user.id
    ).first()

    if not resume:
        flash(
            "Resume not found.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    if not resume.extracted_text:
        flash(
            "No extracted text is available for this resume.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    # Parse resume
    parsed_data = parse_resume(
        resume.extracted_text
    )

    # Calculate ATS-readiness score
    score_data = calculate_resume_score(
        parsed_data
    )

    return render_template(
        "applicant/resume_analysis.html",
        resume=resume,
        parsed_data=parsed_data,
        score_data=score_data
    )

# ==========================================================
# RESUME REVIEW & PROFILE IMPORT
# ==========================================================

@applicant.route(
    "/resumes/review-import/<int:resume_id>",
    methods=["GET", "POST"]
)
@login_required
def review_resume_import(resume_id):

    if current_user.role != "Applicant":
        return redirect(
            url_for("dashboard.home")
        )

    resume = Resume.query.filter_by(
        id=resume_id,
        user_id=current_user.id
    ).first()

    if not resume:
        flash(
            "Resume not found.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    if not resume.extracted_text:
        flash(
            "No extracted text is available for this resume.",
            "danger"
        )

        return redirect(
            url_for("applicant.resumes")
        )

    # ------------------------------------------------------
    # Parse resume again on the server
    # ------------------------------------------------------

    parsed_data = parse_resume(
        resume.extracted_text
    )

    # ------------------------------------------------------
    # POST = Confirm Import
    # ------------------------------------------------------

    if request.method == "POST":

        selected_sections = request.form.getlist(
            "sections"
        )

        if not selected_sections:

            flash(
                "Please select at least one section to import.",
                "warning"
            )

            return render_template(
                "applicant/resume_import_review.html",
                resume=resume,
                parsed_data=parsed_data
            )

        imported_counts = {
            "skills": 0,
            "education": 0,
            "experience": 0,
            "certifications": 0,
            "projects": 0
        }

        skipped_counts = {
            "skills": 0,
            "education": 0,
            "experience": 0,
            "certifications": 0,
            "projects": 0
        }

        # ==================================================
        # SKILLS
        # ==================================================

        if "skills" in selected_sections:

            resume_skills = parsed_data.get(
                "skills",
                []
            )

            existing_skills = Skill.query.filter_by(
                user_id=current_user.id
            ).all()

            existing_skill_names = {
                skill.skill_name.strip().lower()
                for skill in existing_skills
                if skill.skill_name
            }

            for skill_name in resume_skills:

                if not skill_name:
                    continue

                clean_skill = skill_name.strip()

                if not clean_skill:
                    continue

                if clean_skill.lower() in existing_skill_names:

                    skipped_counts["skills"] += 1
                    continue

                new_skill = Skill(
                    user_id=current_user.id,
                    skill_name=clean_skill
                )

                db.session.add(
                    new_skill
                )

                existing_skill_names.add(
                    clean_skill.lower()
                )

                imported_counts["skills"] += 1

        # ==================================================
        # EDUCATION
        # ==================================================

        if "education" in selected_sections:

            resume_education = parsed_data.get(
                "education",
                []
            )

            existing_education = Education.query.filter_by(
                user_id=current_user.id
            ).all()

            existing_education_keys = {
                (
                    (education.degree or "").strip().lower(),
                    (education.institution or "").strip().lower()
                )
                for education in existing_education
            }

            for education_data in resume_education:

                degree = (
                    education_data.get("degree")
                    or ""
                ).strip()

                institution = (
                    education_data.get("institution")
                    or ""
                ).strip()

                if not degree or not institution:
                    continue

                duplicate_key = (
                    degree.lower(),
                    institution.lower()
                )

                if duplicate_key in existing_education_keys:

                    skipped_counts["education"] += 1
                    continue

                start_year = None
                end_year = None

                year_text = (
                    education_data.get("year")
                    or ""
                ).strip()

                year_matches = re.findall(
                    r"\b(19\d{2}|20\d{2})\b",
                    year_text
                )

                if len(year_matches) >= 2:

                    start_year = int(
                        year_matches[0]
                    )

                    end_year = int(
                        year_matches[1]
                    )

                elif len(year_matches) == 1:

                    end_year = int(
                        year_matches[0]
                    )

                details = education_data.get(
                    "details",
                    []
                )

                description = "\n".join(
                    detail.strip()
                    for detail in details
                    if detail and detail.strip()
                )

                new_education = Education(
                    user_id=current_user.id,
                    degree=degree,
                    institution=institution,
                    start_year=start_year,
                    end_year=end_year,
                    description=description or None
                )

                db.session.add(
                    new_education
                )

                existing_education_keys.add(
                    duplicate_key
                )

                imported_counts["education"] += 1

        # ==================================================
        # WORK EXPERIENCE
        # ==================================================

        if "experience" in selected_sections:

            resume_experience = parsed_data.get(
                "experience",
                []
            )

            existing_experience = WorkExperience.query.filter_by(
                user_id=current_user.id
            ).all()

            existing_experience_keys = {
                (
                    (experience.job_title or "").strip().lower(),
                    (experience.company_name or "").strip().lower()
                )
                for experience in existing_experience
            }

            for experience_data in resume_experience:

                job_title = (
                    experience_data.get("title")
                    or ""
                ).strip()

                company_name = (
                    experience_data.get("company")
                    or ""
                ).strip()

                if not job_title or not company_name:
                    continue

                duplicate_key = (
                    job_title.lower(),
                    company_name.lower()
                )

                if duplicate_key in existing_experience_keys:

                    skipped_counts["experience"] += 1
                    continue

                details = experience_data.get(
                    "details",
                    []
                )

                description = "\n".join(
                    detail.strip()
                    for detail in details
                    if detail and detail.strip()
                )

                new_experience = WorkExperience(
                    user_id=current_user.id,
                    job_title=job_title,
                    company_name=company_name,
                    description=description or None
                )

                db.session.add(
                    new_experience
                )

                existing_experience_keys.add(
                    duplicate_key
                )

                imported_counts["experience"] += 1

        # ==================================================
        # CERTIFICATIONS
        # ==================================================

        if "certifications" in selected_sections:

            resume_certifications = parsed_data.get(
                "certifications",
                []
            )

            existing_certifications = Certification.query.filter_by(
                user_id=current_user.id
            ).all()

            existing_certification_names = {
                certification.certification_name.strip().lower()
                for certification in existing_certifications
                if certification.certification_name
            }

            for certification_name in resume_certifications:

                if not certification_name:
                    continue

                clean_certification = (
                    certification_name.strip()
                )

                if not clean_certification:
                    continue

                if (
                    clean_certification.lower()
                    in existing_certification_names
                ):

                    skipped_counts["certifications"] += 1
                    continue

                new_certification = Certification(
                    user_id=current_user.id,
                    certification_name=clean_certification,
                    issuing_organization="Not specified"
                )

                db.session.add(
                    new_certification
                )

                existing_certification_names.add(
                    clean_certification.lower()
                )

                imported_counts["certifications"] += 1

        # ==================================================
        # PROJECTS
        # ==================================================

        if "projects" in selected_sections:

            resume_projects = parsed_data.get(
                "projects",
                []
            )

            existing_projects = Project.query.filter_by(
                user_id=current_user.id
            ).all()

            existing_project_titles = {
                project.project_title.strip().lower()
                for project in existing_projects
                if project.project_title
            }

            for project_data in resume_projects:

                project_title = (
                    project_data.get("name")
                    or ""
                ).strip()

                if not project_title:
                    continue

                if (
                    project_title.lower()
                    in existing_project_titles
                ):

                    skipped_counts["projects"] += 1
                    continue

                details = project_data.get(
                    "details",
                    []
                )

                description = "\n".join(
                    detail.strip()
                    for detail in details
                    if detail and detail.strip()
                )

                new_project = Project(
                    user_id=current_user.id,
                    project_title=project_title,
                    description=description or None
                )

                db.session.add(
                    new_project
                )

                existing_project_titles.add(
                    project_title.lower()
                )

                imported_counts["projects"] += 1

        # ==================================================
        # SAVE ALL CHANGES
        # ==================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "Resume profile import error:",
                repr(e)
            )

            flash(
                "Something went wrong while importing your resume data.",
                "danger"
            )

            return render_template(
                "applicant/resume_import_review.html",
                resume=resume,
                parsed_data=parsed_data
            )

        # ==================================================
        # IMPORT SUMMARY
        # ==================================================

        total_imported = sum(
            imported_counts.values()
        )

        total_skipped = sum(
            skipped_counts.values()
        )

        if total_imported > 0:

            flash(
                f"Resume information imported successfully. "
                f"{total_imported} new item(s) added"
                + (
                    f" and {total_skipped} duplicate item(s) skipped."
                    if total_skipped > 0
                    else "."
                ),
                "success"
            )

        else:

            flash(
                "No new information was imported. "
                "Existing profile information was preserved.",
                "info"
            )

        return redirect(
            url_for(
                "applicant.resume_import_success",
                resume_id=resume.id
            )
        )

    # ------------------------------------------------------
    # GET = Show Review Page
    # ------------------------------------------------------

    return render_template(
        "applicant/resume_import_review.html",
        resume=resume,
        parsed_data=parsed_data
    )


# ==========================================================
# RESUME IMPORT SUCCESS
# ==========================================================

@applicant.route(
    "/resumes/import-success/<int:resume_id>"
)
@login_required
def resume_import_success(resume_id):

    if current_user.role != "Applicant":
        return redirect(
            url_for("dashboard.home")
        )

    resume = Resume.query.filter_by(
        id=resume_id,
        user_id=current_user.id
    ).first()

    if not resume:
        return redirect(
            url_for("applicant.resumes")
        )

    return render_template(
        "applicant/resume_import_success.html",
        resume=resume
    )

# ==========================================================
# APPLICANT JOB BROWSING
# ==========================================================

@applicant.route(
    "/jobs",
    methods=["GET"]
)
@login_required
def jobs():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    # ------------------------------------------------------
    # Get only published jobs
    # ------------------------------------------------------

    jobs = Job.query.filter_by(
        status="Published"
    ).order_by(
        Job.created_at.desc()
    ).all()

    # ------------------------------------------------------
    # Get jobs already applied to by this applicant
    # ------------------------------------------------------

    applied_job_ids = {
        application.job_id
        for application in Application.query.filter_by(
            applicant_id=current_user.id
        ).all()
    }

    return render_template(
        "applicant/jobs.html",
        jobs=jobs,
        applied_job_ids=applied_job_ids
    )


# ==========================================================
# APPLICANT JOB DETAILS
# ==========================================================

@applicant.route(
    "/jobs/<int:job_id>",
    methods=["GET"]
)
@login_required
def job_detail(job_id):

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    # ------------------------------------------------------
    # Find published job
    # ------------------------------------------------------

    job = Job.query.filter(
        Job.id == job_id,
        func.lower(
            func.trim(Job.status)
        ) == "published"
    ).first()

    if not job:

        flash(
            "Job not found or is no longer available.",
            "danger"
        )

        return redirect(
            url_for("applicant.jobs")
        )

    # ------------------------------------------------------
    # Check whether applicant already applied
    # ------------------------------------------------------

    application = Application.query.filter_by(
        job_id=job.id,
        applicant_id=current_user.id
    ).first()

    return render_template(
        "applicant/job_detail.html",
        job=job,
        application=application
    )


# ==========================================================
# APPLY TO JOB
# ==========================================================

@applicant.route(
    "/jobs/<int:job_id>/apply",
    methods=["POST"]
)
@login_required
def apply_job(job_id):

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    # ------------------------------------------------------
    # Find published job
    # ------------------------------------------------------

    job = Job.query.filter(
        Job.id == job_id,
        func.lower(
            func.trim(Job.status)
        ) == "published"
    ).first()

    if not job:

        flash(
            "This job is no longer available.",
            "danger"
        )

        return redirect(
            url_for("applicant.jobs")
        )

    # ------------------------------------------------------
    # Check application deadline
    # ------------------------------------------------------

    if (
        job.application_deadline
        and datetime.utcnow().date()
        > job.application_deadline
    ):

        flash(
            "The application deadline for this job has passed.",
            "warning"
        )

        return redirect(
            url_for(
                "applicant.job_detail",
                job_id=job.id
            )
        )

    # ------------------------------------------------------
    # Prevent duplicate application
    # ------------------------------------------------------

    existing_application = Application.query.filter_by(
        job_id=job.id,
        applicant_id=current_user.id
    ).first()

    if existing_application:

        flash(
            "You have already applied for this job.",
            "warning"
        )

        return redirect(
            url_for(
                "applicant.job_detail",
                job_id=job.id
            )
        )

    # ------------------------------------------------------
    # Get optional cover letter
    # ------------------------------------------------------

    cover_letter = request.form.get(
        "cover_letter",
        ""
    ).strip()

    # ------------------------------------------------------
    # Create application
    # ------------------------------------------------------

    application = Application(
        job_id=job.id,
        applicant_id=current_user.id,
        cover_letter=cover_letter,
        status="Pending"
    )

    db.session.add(application)

    # ------------------------------------------------------
    # Save application
    # ------------------------------------------------------

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "Job application error:",
            repr(e)
        )

        flash(
            "Unable to submit your application. Please try again.",
            "danger"
        )

        return redirect(
            url_for(
                "applicant.job_detail",
                job_id=job.id
            )
        )

    # ------------------------------------------------------
    # Success
    # ------------------------------------------------------

    flash(
        "Application submitted successfully!",
        "success"
    )

    return redirect(
        url_for(
            "applicant.job_detail",
            job_id=job.id
        )
    )