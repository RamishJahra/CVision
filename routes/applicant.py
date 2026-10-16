import os
import uuid
import fitz
import hashlib
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
from models.notification import Notification
from sqlalchemy import func
from services.resume_parser import (
    parse_resume,
    parse_experience_dates
)
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


    # ==========================
    # Current Education
    # ==========================

    is_current = (
        request.form.get("is_current") == "1"
    )


    # If currently studying,
    # end year should remain NULL.

    if is_current:

        end_year = None


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

        is_current=is_current,

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
# Edit Education
# ==========================

@applicant.route(
    "/education/<int:education_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_education(education_id):

    if current_user.role != "Applicant":
        return redirect(url_for("dashboard.home"))

    education = Education.query.filter_by(
        id=education_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        # ==================================================
        # Basic Information
        # ==================================================

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

        cgpa = request.form.get(
            "cgpa",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        # ==================================================
        # Validation
        # ==================================================

        if not degree or not institution:

            flash(
                "Degree and institution are required.",
                "danger"
            )

            return redirect(
                url_for(
                    "applicant.edit_education",
                    education_id=education.id
                )
            )

        # ==================================================
        # Education Years
        # ==================================================

        start_year_raw = request.form.get(
            "start_year",
            ""
        ).strip()

        end_year_raw = request.form.get(
            "end_year",
            ""
        ).strip()

        # Convert empty strings to None
        start_year = (
            int(start_year_raw)
            if start_year_raw
            else None
        )

        end_year = (
            int(end_year_raw)
            if end_year_raw
            else None
        )

        # ==================================================
        # Currently Studying
        # ==================================================

        is_current = (
            request.form.get("is_current") == "1"
        )

        # If currently studying, there must be
        # no end year.
        if is_current:
            end_year = None

        # ==================================================
        # Update Education
        # ==================================================

        education.degree = degree

        education.institution = institution

        education.field_of_study = (
            field_of_study or None
        )

        education.start_year = start_year

        education.end_year = end_year

        education.is_current = is_current

        education.cgpa = (
            cgpa or None
        )

        education.description = (
            description or None
        )

        # ==================================================
        # Save
        # ==================================================

        db.session.commit()

        flash(
            "Education updated successfully!",
            "success"
        )

        return redirect(
            url_for("applicant.education")
        )

    # ==================================================
    # GET
    # ==================================================

    return render_template(
        "applicant/edit_education.html",
        education=education
    )

# ==========================
# Delete Education
# ==========================

@applicant.route(
    "/education/<int:education_id>/delete",
    methods=["POST"]
)
@login_required
def delete_education(education_id):

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )


    education = Education.query.filter_by(
        id=education_id,
        user_id=current_user.id
    ).first_or_404()


    db.session.delete(education)

    db.session.commit()


    flash(
        "Education deleted successfully!",
        "success"
    )


    return redirect(
        url_for("applicant.education")
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
@applicant.route(
    "/experience/<int:experience_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_experience(experience_id):

    if current_user.role != "Applicant":
        return redirect(url_for("dashboard.home"))

    experience = WorkExperience.query.filter_by(
        id=experience_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

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

        start_date_raw = request.form.get(
            "start_date",
            ""
        ).strip()

        end_date_raw = request.form.get(
            "end_date",
            ""
        ).strip()

        currently_working = (
            request.form.get("currently_working") == "1"
        )

        description = request.form.get(
            "description",
            ""
        ).strip()

        # -----------------------------------------
        # Validation
        # -----------------------------------------

        if not job_title or not company_name:

            flash(
                "Job title and company name are required.",
                "danger"
            )

            return redirect(
                url_for(
                    "applicant.edit_experience",
                    experience_id=experience.id
                )
            )

        # -----------------------------------------
        # Convert Start Date
        # -----------------------------------------

        start_date = None

        if start_date_raw:

            try:

                start_date = datetime.strptime(
                    start_date_raw,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid start date.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "applicant.edit_experience",
                        experience_id=experience.id
                    )
                )

        # -----------------------------------------
        # Convert End Date
        # -----------------------------------------

        end_date = None

        if not currently_working and end_date_raw:

            try:

                end_date = datetime.strptime(
                    end_date_raw,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid end date.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "applicant.edit_experience",
                        experience_id=experience.id
                    )
                )

        # Currently working = no end date
        if currently_working:
            end_date = None

        # -----------------------------------------
        # Update Experience
        # -----------------------------------------

        experience.job_title = job_title

        experience.company_name = company_name

        experience.employment_type = (
            employment_type or None
        )

        experience.location = (
            location or None
        )

        experience.start_date = start_date

        experience.end_date = end_date

        experience.currently_working = (
            currently_working
        )

        experience.description = (
            description or None
        )

        db.session.commit()

        flash(
            "Work experience updated successfully!",
            "success"
        )

        return redirect(
            url_for("applicant.experience")
        )

    return render_template(
        "applicant/edit_experience.html",
        experience=experience
    )


@applicant.route(
    "/experience/<int:experience_id>/delete",
    methods=["POST"]
)
@login_required
def delete_experience(experience_id):

    if current_user.role != "Applicant":
        return redirect(url_for("dashboard.home"))

    experience = WorkExperience.query.filter_by(
        id=experience_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(experience)

    db.session.commit()

    flash(
        "Work experience deleted successfully!",
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
@applicant.route(
    "/skills/delete",
    methods=["POST"]
)
@login_required
def delete_selected_skills():

    if current_user.role != "Applicant":
        return redirect(url_for("dashboard.home"))

    skill_ids = request.form.getlist(
        "skill_ids"
    )

    if not skill_ids:

        flash(
            "Please select at least one skill to delete.",
            "warning"
        )

        return redirect(
            url_for("applicant.skills")
        )

    # Convert IDs to integers safely
    valid_skill_ids = []

    for skill_id in skill_ids:

        try:
            valid_skill_ids.append(
                int(skill_id)
            )

        except (TypeError, ValueError):
            continue

    if not valid_skill_ids:

        flash(
            "No valid skills were selected.",
            "warning"
        )

        return redirect(
            url_for("applicant.skills")
        )

    # --------------------------------------------------
    # Get only skills belonging to current applicant
    # --------------------------------------------------

    selected_skills = Skill.query.filter(
        Skill.id.in_(valid_skill_ids),
        Skill.user_id == current_user.id
    ).all()

    if not selected_skills:

        flash(
            "No selected skills were found.",
            "warning"
        )

        return redirect(
            url_for("applicant.skills")
        )

    # --------------------------------------------------
    # Delete selected skills
    # --------------------------------------------------

    deleted_count = len(selected_skills)

    for skill in selected_skills:
        db.session.delete(skill)

    db.session.commit()

    # --------------------------------------------------
    # Success message
    # --------------------------------------------------

    flash(
        f"{deleted_count} skill(s) deleted successfully!",
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


# ==========================================================
# Edit Certification
# ==========================================================

@applicant.route(
    "/certifications/<int:certification_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_certification(certification_id):

    certification = Certification.query.filter_by(
        id=certification_id,
        user_id=current_user.id
    ).first_or_404()


    # ======================================================
    # POST - Update Certification
    # ======================================================

    if request.method == "POST":

        certification_name = request.form.get(
            "certification_name",
            ""
        ).strip()

        issuing_organization = request.form.get(
            "issuing_organization",
            ""
        ).strip()

        issue_date = request.form.get(
            "issue_date",
            ""
        ).strip()

        expiry_date = request.form.get(
            "expiry_date",
            ""
        ).strip()

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


        # ==================================================
        # Validation
        # ==================================================

        if not certification_name:

            flash(
                "Certification name is required.",
                "danger"
            )

            return render_template(
                "applicant/edit_certification.html",
                certification=certification
            )


        if not issuing_organization:

            flash(
                "Issuing organization is required.",
                "danger"
            )

            return render_template(
                "applicant/edit_certification.html",
                certification=certification
            )


        # ==================================================
        # Convert Dates
        # ==================================================

        try:

            if issue_date:

                certification.issue_date = datetime.strptime(
                    issue_date,
                    "%Y-%m-%d"
                ).date()

            else:

                certification.issue_date = None


            if expiry_date:

                certification.expiry_date = datetime.strptime(
                    expiry_date,
                    "%Y-%m-%d"
                ).date()

            else:

                certification.expiry_date = None


        except ValueError:

            flash(
                "Please provide valid certification dates.",
                "danger"
            )

            return render_template(
                "applicant/edit_certification.html",
                certification=certification
            )


        # ==================================================
        # Update Fields
        # ==================================================

        certification.certification_name = (
            certification_name
        )

        certification.issuing_organization = (
            issuing_organization
        )

        certification.credential_id = (
            credential_id or None
        )

        certification.credential_url = (
            credential_url or None
        )

        certification.description = (
            description or None
        )


        # ==================================================
        # Save
        # ==================================================

        try:

            db.session.commit()

            flash(
                "Certification updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "applicant.certifications"
                )
            )

        except Exception as e:

            db.session.rollback()

            print(
                "Edit certification error:",
                e
            )

            flash(
                "Unable to update certification.",
                "danger"
            )


    # ======================================================
    # GET - Show Edit Form
    # ======================================================

    return render_template(
        "applicant/edit_certification.html",
        certification=certification
    )


# ==========================================================
# Delete Certification
# ==========================================================

@applicant.route(
    "/certifications/<int:certification_id>/delete",
    methods=["POST"]
)
@login_required
def delete_certification(certification_id):

    certification = Certification.query.filter_by(
        id=certification_id,
        user_id=current_user.id
    ).first_or_404()


    try:

        db.session.delete(
            certification
        )

        db.session.commit()

        flash(
            "Certification deleted successfully.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        print(
            "Delete certification error:",
            e
        )

        flash(
            "Unable to delete certification.",
            "danger"
        )


    return redirect(
        url_for(
            "applicant.certifications"
        )
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
# ============================================================
# EDIT PROJECT
# ============================================================

@applicant.route(
    "/projects/<int:project_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_project(project_id):

    if current_user.role != "Applicant":
        return redirect(
            url_for("dashboard.home")
        )

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        project_title = request.form.get(
            "project_title",
            ""
        ).strip()

        technologies = request.form.get(
            "technologies",
            ""
        ).strip()

        start_date_raw = request.form.get(
            "start_date",
            ""
        ).strip()

        end_date_raw = request.form.get(
            "end_date",
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

        description = request.form.get(
            "description",
            ""
        ).strip()

        # --------------------------------------------------
        # Validation
        # --------------------------------------------------

        if not project_title:

            flash(
                "Project title is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "applicant.edit_project",
                    project_id=project.id
                )
            )

        # --------------------------------------------------
        # Start date
        # --------------------------------------------------

        start_date = None

        if start_date_raw:

            try:

                start_date = datetime.strptime(
                    start_date_raw,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid start date.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "applicant.edit_project",
                        project_id=project.id
                    )
                )

        # --------------------------------------------------
        # End date
        # --------------------------------------------------

        end_date = None

        if end_date_raw:

            try:

                end_date = datetime.strptime(
                    end_date_raw,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid end date.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "applicant.edit_project",
                        project_id=project.id
                    )
                )

        # --------------------------------------------------
        # Update project
        # --------------------------------------------------

        project.project_title = project_title

        project.technologies = (
            technologies
            if technologies
            else None
        )

        project.start_date = start_date

        project.end_date = end_date

        project.project_url = (
            project_url
            if project_url
            else None
        )

        project.github_url = (
            github_url
            if github_url
            else None
        )

        project.description = (
            description
            if description
            else None
        )

        db.session.commit()

        flash(
            "Project updated successfully!",
            "success"
        )

        return redirect(
            url_for("applicant.projects")
        )

    return render_template(
        "applicant/edit_project.html",
        project=project
    )


# ============================================================
# DELETE PROJECT
# ============================================================

@applicant.route(
    "/projects/<int:project_id>/delete",
    methods=["POST"]
)
@login_required
def delete_project(project_id):

    if current_user.role != "Applicant":
        return redirect(
            url_for("dashboard.home")
        )

    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(project)

    db.session.commit()

    flash(
        "Project deleted successfully!",
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

        # --------------------------------------------------
        # Import counters
        # --------------------------------------------------

        imported_counts = {
            "contact_links": 0,
            "skills": 0,
            "education": 0,
            "experience": 0,
            "certifications": 0,
            "projects": 0
        }

        skipped_counts = {
            "contact_links": 0,
            "skills": 0,
            "education": 0,
            "experience": 0,
            "certifications": 0,
            "projects": 0
        }

        # ==================================================
        # CONTACT LINKS
        # ==================================================

        if "contact_links" in selected_sections:

            profile = ApplicantProfile.query.filter_by(
                user_id=current_user.id
            ).first()

            if not profile:

                profile = ApplicantProfile(
                    user_id=current_user.id
                )

                db.session.add(
                    profile
                )

            contact_links = {

                "linkedin_url": (
                    parsed_data.get("linkedin")
                    or ""
                ).strip(),

                "github_url": (
                    parsed_data.get("github")
                    or ""
                ).strip(),

                "portfolio_url": (
                    parsed_data.get("website")
                    or ""
                ).strip()
            }

            for field_name, value in contact_links.items():

                if not value:
                    continue

                current_value = (
                    getattr(
                        profile,
                        field_name,
                        ""
                    )
                    or ""
                ).strip()

                if current_value:

                    skipped_counts[
                        "contact_links"
                    ] += 1

                    continue

                setattr(
                    profile,
                    field_name,
                    value
                )

                imported_counts[
                    "contact_links"
                ] += 1

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

                if (
                    clean_skill.lower()
                    in existing_skill_names
                ):

                    skipped_counts[
                        "skills"
                    ] += 1

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

                imported_counts[
                    "skills"
                ] += 1

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
                    (
                        education.degree
                        or ""
                    ).strip().lower(),

                    (
                        education.institution
                        or ""
                    ).strip().lower()
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

                    skipped_counts[
                        "education"
                    ] += 1

                    continue

                # --------------------------------------------------
                # Education dates
                # --------------------------------------------------

                start_year = education_data.get(
                    "start_year"
                )

                end_year = education_data.get(
                    "end_year"
                )

                is_current = bool(
                    education_data.get(
                        "is_current",
                        False
                    )
                )

                # --------------------------------------------------
                # Backward compatibility
                # --------------------------------------------------

                if (
                    start_year is None
                    and end_year is None
                ):

                    year_text = (
                        education_data.get("year")
                        or ""
                    ).strip()

                    is_current = bool(
                        re.search(
                            r"\b(Present|Current|Now)\b",
                            year_text,
                            re.IGNORECASE
                        )
                    )

                    year_matches = re.findall(
                        r"\b(19\d{2}|20\d{2})\b",
                        year_text
                    )

                    if len(year_matches) >= 2:

                        start_year = int(
                            year_matches[0]
                        )

                        if is_current:

                            end_year = None

                        else:

                            end_year = int(
                                year_matches[1]
                            )

                    elif len(year_matches) == 1:

                        start_year = int(
                            year_matches[0]
                        )

                        if is_current:

                            end_year = None

                        else:

                            end_year = None

                # --------------------------------------------------
                # Education description
                # --------------------------------------------------

                details = education_data.get(
                    "details",
                    []
                )

                description = "\n".join(
                    detail.strip()
                    for detail in details
                    if detail and detail.strip()
                )

                # --------------------------------------------------
                # Create Education record
                # --------------------------------------------------

                new_education = Education(

                    user_id=current_user.id,

                    degree=degree,

                    institution=institution,

                    start_year=start_year,

                    end_year=end_year,

                    is_current=is_current,

                    description=description or None

                )

                db.session.add(
                    new_education
                )

                existing_education_keys.add(
                    duplicate_key
                )

                imported_counts[
                    "education"
                ] += 1

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
                    (
                        experience.job_title
                        or ""
                    ).strip().lower(),

                    (
                        experience.company_name
                        or ""
                    ).strip().lower()
                )

                for experience in existing_experience

            }

            for experience_data in resume_experience:

                # --------------------------------------------------
                # Job Title
                # --------------------------------------------------

                job_title = (
                    experience_data.get("title")
                    or experience_data.get("job_title")
                    or ""
                ).strip()

                # --------------------------------------------------
                # Company
                # --------------------------------------------------

                company_name = (
                    experience_data.get("company")
                    or experience_data.get("company_name")
                    or ""
                ).strip()

                if not job_title or not company_name:
                    continue

                # --------------------------------------------------
                # Duplicate Check
                # --------------------------------------------------

                duplicate_key = (
                    job_title.lower(),
                    company_name.lower()
                )

                if duplicate_key in existing_experience_keys:

                    skipped_counts[
                        "experience"
                    ] += 1

                    continue

                # --------------------------------------------------
                # Experience Dates
                # --------------------------------------------------

                start_date = experience_data.get(
                    "start_date"
                )

                end_date = experience_data.get(
                    "end_date"
                )

                currently_working = bool(
                    experience_data.get(
                        "currently_working",
                        False
                    )
                )

                # --------------------------------------------------
                # Backward Compatibility
                # --------------------------------------------------

                if (
                    start_date is None
                    and end_date is None
                ):

                    duration = (
                        experience_data.get(
                            "duration"
                        )
                        or ""
                    ).strip()

                    date_data = parse_experience_dates(
                        duration
                    )

                    start_date = date_data[
                        "start_date"
                    ]

                    end_date = date_data[
                        "end_date"
                    ]

                    currently_working = date_data[
                        "currently_working"
                    ]

                # --------------------------------------------------
                # Convert string dates
                # --------------------------------------------------

                if start_date:

                    if isinstance(
                        start_date,
                        str
                    ):

                        try:

                            start_date = datetime.strptime(
                                start_date,
                                "%Y-%m-%d"
                            ).date()

                        except ValueError:

                            start_date = None

                if end_date:

                    if isinstance(
                        end_date,
                        str
                    ):

                        try:

                            end_date = datetime.strptime(
                                end_date,
                                "%Y-%m-%d"
                            ).date()

                        except ValueError:

                            end_date = None

                # --------------------------------------------------
                # Currently working
                # --------------------------------------------------

                if currently_working:

                    end_date = None

                # --------------------------------------------------
                # Description
                # --------------------------------------------------

                details = experience_data.get(
                    "details",
                    []
                )

                description = "\n".join(
                    detail.strip()
                    for detail in details
                    if detail and detail.strip()
                )

                # --------------------------------------------------
                # Create Work Experience
                # --------------------------------------------------

                new_experience = WorkExperience(

                    user_id=current_user.id,

                    job_title=job_title,

                    company_name=company_name,

                    start_date=start_date,

                    end_date=end_date,

                    currently_working=currently_working,

                    description=description or None

                )

                db.session.add(
                    new_experience
                )

                existing_experience_keys.add(
                    duplicate_key
                )

                imported_counts[
                    "experience"
                ] += 1

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

            for certification_data in resume_certifications:

                if not certification_data:
                    continue

                clean_certification = (
                    certification_data.get(
                        "certification_name",
                        ""
                    )
                    or ""
                ).strip()

                if not clean_certification:
                    continue

                if (
                    clean_certification.lower()
                    in existing_certification_names
                ):

                    skipped_counts[
                        "certifications"
                    ] += 1

                    continue

                issuing_organization = (
                    certification_data.get(
                        "issuing_organization"
                    )
                    or "Not specified"
                ).strip()

                issue_date = certification_data.get(
                    "issue_date"
                )

                expiry_date = certification_data.get(
                    "expiry_date"
                )

                credential_id = (
                    certification_data.get(
                        "credential_id"
                    )
                    or ""
                ).strip()

                credential_url = (
                    certification_data.get(
                        "credential_url"
                    )
                    or ""
                ).strip()

                description = (
                    certification_data.get(
                        "description"
                    )
                    or ""
                ).strip()

                # --------------------------------------------------
                # Convert string dates to Python date objects
                # --------------------------------------------------

                if issue_date and isinstance(
                    issue_date,
                    str
                ):

                    try:

                        issue_date = datetime.strptime(
                            issue_date,
                            "%Y-%m-%d"
                        ).date()

                    except ValueError:

                        issue_date = None

                if expiry_date and isinstance(
                    expiry_date,
                    str
                ):

                    try:

                        expiry_date = datetime.strptime(
                            expiry_date,
                            "%Y-%m-%d"
                        ).date()

                    except ValueError:

                        expiry_date = None

                # --------------------------------------------------
                # Create certification
                # --------------------------------------------------

                new_certification = Certification(

                    user_id=current_user.id,

                    certification_name=(
                        clean_certification
                    ),

                    issuing_organization=(
                        issuing_organization
                    ),

                    issue_date=issue_date,

                    expiry_date=expiry_date,

                    credential_id=(
                        credential_id
                        or None
                    ),

                    credential_url=(
                        credential_url
                        or None
                    ),

                    description=(
                        description
                        or None
                    )

                )

                db.session.add(
                    new_certification
                )

                existing_certification_names.add(
                    clean_certification.lower()
                )

                imported_counts[
                    "certifications"
                ] += 1
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

            existing_project_keys = {

                (
                    (
                        project.project_title
                        or ""
                    ).strip().lower()
                )

                for project in existing_projects

            }

            for project_data in resume_projects:

                project_title = (

                    project_data.get("name")

                    or project_data.get(
                        "project_title"
                    )

                    or ""

                ).strip()

                if not project_title:
                    continue

                duplicate_key = (
                    project_title.lower()
                )

                if duplicate_key in existing_project_keys:

                    skipped_counts[
                        "projects"
                    ] += 1

                    continue

                # ---------------------------------------------
                # Technologies
                # ---------------------------------------------

                technologies = (

                    project_data.get(
                        "technologies"
                    )

                    or ""

                ).strip()

                # ---------------------------------------------
                # Description
                # ---------------------------------------------

                details = project_data.get(
                    "details",
                    []
                )

                description = "\n".join(

                    detail.strip()

                    for detail in details

                    if detail
                    and detail.strip()

                )

                # ---------------------------------------------
                # Dates
                # ---------------------------------------------

                start_date = project_data.get(
                    "start_date"
                )

                end_date = project_data.get(
                    "end_date"
                )

                if start_date:

                    if isinstance(
                        start_date,
                        str
                    ):

                        try:

                            start_date = datetime.strptime(
                                start_date,
                                "%Y-%m-%d"
                            ).date()

                        except ValueError:

                            start_date = None

                if end_date:

                    if isinstance(
                        end_date,
                        str
                    ):

                        try:

                            end_date = datetime.strptime(
                                end_date,
                                "%Y-%m-%d"
                            ).date()

                        except ValueError:

                            end_date = None

                # ---------------------------------------------
                # URLs
                # ---------------------------------------------

                project_url = (

                    project_data.get(
                        "project_url"
                    )

                    or ""

                ).strip()

                github_url = (

                    project_data.get(
                        "github_url"
                    )

                    or ""

                ).strip()

                # ---------------------------------------------
                # Create Project
                # ---------------------------------------------

                new_project = Project(

                    user_id=current_user.id,

                    project_title=project_title,

                    technologies=(
                        technologies
                        or None
                    ),

                    start_date=start_date,

                    end_date=end_date,

                    project_url=(
                        project_url
                        or None
                    ),

                    github_url=(
                        github_url
                        or None
                    ),

                    description=(
                        description
                        or None
                    )

                )

                db.session.add(
                    new_project
                )

                existing_project_keys.add(
                    duplicate_key
                )

                imported_counts[
                    "projects"
                ] += 1

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
                    f" and {total_skipped} duplicate/existing "
                    f"item(s) skipped."
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
# AUTO CLOSE EXPIRED JOBS
# ==========================================================

def close_expired_jobs():

    today = datetime.utcnow().date()

    expired_jobs = Job.query.filter(
        Job.application_deadline.isnot(None),
        Job.application_deadline < today,
        func.lower(
            func.trim(Job.status)
        ) == "published"
    ).all()

    for job in expired_jobs:

        job.status = "Closed"

    if expired_jobs:

        db.session.commit()


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
    # Automatically close expired jobs
    # ------------------------------------------------------

    close_expired_jobs()

    # ------------------------------------------------------
    # Get only published jobs
    # ------------------------------------------------------

    jobs = Job.query.filter(
        func.lower(
            func.trim(Job.status)
        ) == "published"
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
# REAL-TIME APPLICANT JOB UPDATES
# ==========================================================

@applicant.route(
    "/jobs/live",
    methods=["GET"]
)
@login_required
def jobs_live():

    if current_user.role != "Applicant":
        return {
            "error": "Unauthorized"
        }, 403

    close_expired_jobs()

    jobs = Job.query.filter(
        func.lower(
            func.trim(Job.status)
        ) == "published"
    ).order_by(
        Job.created_at.desc()
    ).all()

    applied_job_ids = {
        application.job_id
        for application in Application.query.filter_by(
            applicant_id=current_user.id
        ).all()
    }

    job_data = []

    for job in jobs:

        company_name = None
        recruiter_name = None

        if job.recruiter:

            recruiter_name = job.recruiter.full_name

            if (
                job.recruiter.recruiter_profile
                and job.recruiter.recruiter_profile.company_name
            ):
                company_name = (
                    job.recruiter.recruiter_profile.company_name
                )

        job_data.append({

            "id": job.id,

            "job_title": job.job_title,

            "description": job.description or "",

            "location": job.location or "",

            "job_type": job.job_type or "",

            "salary": job.salary or "",

            "application_deadline": (
                job.application_deadline.strftime("%d %b %Y")
                if job.application_deadline
                else None
            ),

            "company_name": company_name,

            "recruiter_name": recruiter_name or "",

            "applied": job.id in applied_job_ids

        })

    version_source = repr(
        [
            (
                job["id"],
                job["job_title"],
                job["description"],
                job["location"],
                job["job_type"],
                job["salary"],
                job["application_deadline"],
                job["company_name"],
                job["recruiter_name"],
                job["applied"]
            )
            for job in job_data
        ]
    )

    version = hashlib.md5(
        version_source.encode("utf-8")
    ).hexdigest()

    return {
        "version": version,
        "jobs": job_data
    }

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
    # Automatically close expired jobs
    # ------------------------------------------------------

    close_expired_jobs()

    # ------------------------------------------------------
    # First find the job
    # ------------------------------------------------------

    job = Job.query.filter_by(
        id=job_id
    ).first()

    if not job:

        flash(
            "Job not found.",
            "danger"
        )

        return redirect(
            url_for("applicant.jobs")
        )

    # ------------------------------------------------------
    # Check applicant's existing application
    # ------------------------------------------------------

    application = Application.query.filter_by(
        job_id=job.id,
        applicant_id=current_user.id
    ).first()

    # ------------------------------------------------------
    # If job is closed/unpublished and applicant has NOT
    # applied, don't allow access.
    #
    # If applicant HAS applied, allow them to see details.
    # ------------------------------------------------------

    job_status = (
        job.status or ""
    ).strip().lower()

    if job_status != "published" and not application:

        flash(
            "Job not found or is no longer available.",
            "danger"
        )

        return redirect(
            url_for("applicant.jobs")
        )

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
    # Automatically close expired jobs
    # ------------------------------------------------------

    close_expired_jobs()

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

        # Automatically close the expired job

        job.status = "Closed"

        db.session.commit()

        flash(
            "The application deadline for this job has passed.",
            "warning"
        )

        return redirect(
            url_for("applicant.jobs")
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
    # Notify recruiter about the new application
    # ------------------------------------------------------

    if job.recruiter_id:

        try:

            db.session.add(
                Notification(
                    user_id=job.recruiter_id,
                    title="New Job Application",
                    message=(
                        f"{current_user.full_name or current_user.username} "
                        f"applied for {job.job_title}."
                    ),
                    notification_type="new_application",
                    application_id=application.id
                )
            )

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "Recruiter notification error:",
                repr(e)
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


# ==========================================================
# APPLICANT MY APPLICATIONS
# ==========================================================

@applicant.route(
    "/applications",
    methods=["GET"]
)
@login_required
def my_applications():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    # ------------------------------------------------------
    # Get all applications submitted by current applicant
    # ------------------------------------------------------

    applications = Application.query.filter_by(
        applicant_id=current_user.id
    ).join(
        Job,
        Application.job_id == Job.id
    ).order_by(
        Application.applied_at.desc()
    ).all()

    return render_template(
        "applicant/my_applications.html",
        applications=applications
    )


# ==========================================================
# REAL-TIME MY APPLICATIONS
# ==========================================================

@applicant.route(
    "/applications/live",
    methods=["GET"]
)
@login_required
def my_applications_live():

    if current_user.role != "Applicant":

        return {
            "error": "Unauthorized"
        }, 403

    # ------------------------------------------------------
    # Get applicant applications
    # ------------------------------------------------------

    applications = Application.query.filter_by(
        applicant_id=current_user.id
    ).join(
        Job,
        Application.job_id == Job.id
    ).order_by(
        Application.applied_at.desc()
    ).all()

    application_data = []

    for application in applications:

        job = application.job

        company_name = ""

        recruiter_name = ""

        if job and job.recruiter:

            recruiter_name = (
                job.recruiter.full_name
                or ""
            )

            if (
                job.recruiter.recruiter_profile
                and
                job.recruiter.recruiter_profile.company_name
            ):

                company_name = (
                    job.recruiter
                    .recruiter_profile
                    .company_name
                )

        application_data.append({

            "id": application.id,

            "job_id": (
                application.job_id
                if application.job_id
                else None
            ),

            "job_title": (
                job.job_title
                if job
                else "Job no longer available"
            ),

            "company_name": (
                company_name
                or recruiter_name
                or "Company"
            ),

            "location": (
                job.location
                if job
                else ""
            ),

            "job_type": (
                job.job_type
                if job
                else ""
            ),

            "salary": (
                job.salary
                if job
                else ""
            ),

            "job_status": (
                job.status
                if job
                else "Unavailable"
            ),

            "status": (
                application.status
                or "Pending"
            ),

            "cover_letter": (
                application.cover_letter
                or ""
            ),

            "applied_at": (
                application.applied_at.strftime(
                    "%d %b %Y, %I:%M %p"
                )
                if application.applied_at
                else ""
            ),

            "updated_at": (
                application.updated_at.strftime(
                    "%d %b %Y, %I:%M %p"
                )
                if application.updated_at
                else ""
            )

        })

    # ------------------------------------------------------
    # Create version from current application state
    # ------------------------------------------------------

    version_source = repr(
        [
            (
                application["id"],
                application["job_id"],
                application["status"],
                application["updated_at"]
            )
            for application in application_data
        ]
    )

    version = hashlib.md5(
        version_source.encode("utf-8")
    ).hexdigest()

    return {
        "version": version,
        "applications": application_data
    }
# ==========================================================
# Read-Only Applicant Profile
# ==========================================================

@applicant.route("/profile/view")
@login_required
def applicant_profile():

    # ------------------------------------------------------
    # Get applicant profile
    # ------------------------------------------------------

    profile = ApplicantProfile.query.filter_by(
        user_id=current_user.id
    ).first()


    # ------------------------------------------------------
    # Get applicant information
    # ------------------------------------------------------

    education = Education.query.filter_by(
        user_id=current_user.id
    ).all()


    experience = WorkExperience.query.filter_by(
        user_id=current_user.id
    ).all()


    skills = Skill.query.filter_by(
        user_id=current_user.id
    ).all()


    certifications = Certification.query.filter_by(
        user_id=current_user.id
    ).all()


    projects = Project.query.filter_by(
        user_id=current_user.id
    ).all()


    # ------------------------------------------------------
    # Render read-only profile
    # ------------------------------------------------------

    return render_template(
        "applicant/applicant_profile.html",
        profile=profile,
        education=education,
        experience=experience,
        skills=skills,
        certifications=certifications,
        projects=projects
    )

# ============================================================
# Read-Only Applicant Resume
# ============================================================

@applicant.route(
    "/resume/view"
)
@login_required
def applicant_resume():

    if current_user.role != "Applicant":

        return redirect(
            url_for("dashboard.home")
        )

    # --------------------------------------------------------
    # Get all resumes belonging to current applicant
    # --------------------------------------------------------

    resumes = Resume.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Resume.uploaded_at.desc()
    ).all()

    # --------------------------------------------------------
    # Find active resume
    # --------------------------------------------------------

    active_resume = Resume.query.filter_by(
        user_id=current_user.id,
        status="active"
    ).order_by(
        Resume.uploaded_at.desc()
    ).first()

    # --------------------------------------------------------
    # Analyze active resume
    # --------------------------------------------------------

    parsed_data = None
    score_data = None

    if active_resume and active_resume.extracted_text:

        try:

            parsed_data = parse_resume(
                active_resume.extracted_text
            )

            score_data = calculate_resume_score(
                parsed_data
            )

        except Exception as e:

            print(
                "Read-only resume analysis error:",
                repr(e)
            )

            parsed_data = None
            score_data = None

    return render_template(
        "applicant/applicant_resume.html",
        resumes=resumes,
        active_resume=active_resume,
        parsed_data=parsed_data,
        score_data=score_data
    )