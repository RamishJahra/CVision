import os
from unittest import result
import uuid
import random
import hashlib

from datetime import datetime, timedelta, date
from sqlalchemy import func

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    current_app,
    session,
    send_from_directory
)

from flask_login import login_required, current_user
from flask_mail import Message

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from models import db, mail
from models.user import User
from models.profile import (
    RecruiterProfile,
    ApplicantProfile
)
from models.job import Job
from models.application import Application
from models.resume import Resume
from models.notification import Notification
from services.job_resume_matcher import calculate_job_match
from models.company import Company, CompanyLocation
from services.cloudinary_service import (
    get_private_file_url,
    is_cloudinary_file,
    get_cloudinary_public_id
)
from services.cloudinary_service import (
    upload_image,
    delete_stored_image
)
recruiter = Blueprint(
    "recruiter",
    __name__,
    url_prefix="/recruiter"
)


# ==========================================================
# Helper: Automatically Close Expired Jobs
# ==========================================================

def close_expired_jobs():

    expired_jobs = Job.query.filter(
        Job.recruiter_id == current_user.id,
        Job.status == "Published",
        Job.application_deadline.isnot(None),
        Job.application_deadline < date.today()
    ).all()

    if expired_jobs:

        for job in expired_jobs:

            job.status = "Closed"

        db.session.commit()


# ==========================================================
# Recruiter Profile
# ==========================================================

@recruiter.route(
    "/profile",
    methods=["GET", "POST"]
)
@login_required
def profile():

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    profile = RecruiterProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:

        profile = RecruiterProfile(
            user_id=current_user.id
        )

        db.session.add(profile)
        db.session.commit()

    if request.method == "POST":

        profile.job_title = request.form.get(
            "job_title",
            ""
        ).strip()

        profile.linkedin_url = request.form.get(
            "linkedin_url",
            ""
        ).strip()

        profile.bio = request.form.get(
            "bio",
            ""
        ).strip()

        db.session.commit()

        flash(
            "Recruiter profile updated successfully!",
            "success"
        )

        return redirect(
            url_for("recruiter.profile")
        )

    return render_template(
        "recruiter/profile.html",
        profile=profile
    )


# ==========================================================
# Recruiter Profile Picture
# ==========================================================


@recruiter.route("/profile-picture", methods=["POST"])
@login_required
def profile_picture():

    if current_user.role != "Recruiter":
        return redirect(url_for("dashboard.home"))

    file = request.files.get("profile_image")

    if not file or not file.filename:
        flash("Please select an image.", "danger")
        return redirect(url_for("recruiter.profile"))

    allowed_extensions = {"jpg", "jpeg", "png", "webp"}
    extension = file.filename.rsplit(".", 1)[-1].lower()

    if extension not in allowed_extensions:
        flash("Only JPG, JPEG, PNG and WEBP images are allowed.", "danger")
        return redirect(url_for("recruiter.profile"))

    old_image = current_user.profile_image

    try:
        result = upload_image(file, folder="cvision/profile")
        new_filename = result["filename"]

        current_user.profile_image = new_filename
        db.session.commit()

        if old_image and old_image != "default.png":
            delete_stored_image(
                old_image,
                local_folder="uploads/profile"
            )

        flash("Profile picture updated successfully!", "success")

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Recruiter profile picture upload failed.")
        flash("Unable to update your profile picture.", "danger")

    return redirect(url_for("recruiter.profile"))

# ==========================================================
# Shared Company Profile
# ==========================================================

@recruiter.route("/company-profile", methods=["GET", "POST"])
@login_required
def company_profile():

    if current_user.role != "Recruiter":
        return redirect(url_for("dashboard.home"))

    profile = RecruiterProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        profile = RecruiterProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.flush()

    if request.method == "POST":

        company_name = request.form.get(
            "company_name", ""
        ).strip()

        if not company_name:
            flash("Please enter your company name.", "danger")

            return redirect(
                url_for("recruiter.company_profile")
            )

        try:
            # Find the recruiter's existing shared company.
            company = profile.company

            # If not associated with a company yet, try to find
            # an existing company with the same name.
            if company is None:
                company = Company.query.filter(
                    func.lower(Company.company_name)
                    == company_name.lower()
                ).first()

            # Create a company only when no matching record exists.
            if company is None:
                company = Company(company_name=company_name)
                db.session.add(company)
                db.session.flush()

            # Associate this recruiter with the shared company.
            profile.company = company

            # Save shared company information.
            company.company_name = company_name

            company.industry = (
                request.form.get("industry", "").strip() or None
            )

            company.company_size = (
                request.form.get("company_size", "").strip() or None
            )

            company.company_website = (
                request.form.get("company_website", "").strip() or None
            )

            company.company_description = (
                request.form.get("company_description", "").strip() or None
            )

            # Preserve legacy fields temporarily for compatibility
            # with existing templates and routes.
            profile.company_name = company.company_name
            profile.industry = company.industry
            profile.company_size = company.company_size
            profile.company_website = company.company_website
            profile.company_description = company.company_description
            profile.company_logo = company.company_logo

            # Shared company location.
            address = request.form.get(
                "company_location", ""
            ).strip()

            latitude_value = request.form.get("latitude", "").strip()
            longitude_value = request.form.get("longitude", "").strip()

            latitude = None
            longitude = None

            if latitude_value and longitude_value:
                try:
                    latitude = float(latitude_value)
                    longitude = float(longitude_value)

                    if not (
                        -90 <= latitude <= 90
                        and -180 <= longitude <= 180
                    ):
                        raise ValueError

                except (ValueError, TypeError):
                    flash(
                        "The selected map coordinates are invalid.",
                        "danger"
                    )
                    return redirect(
                        url_for("recruiter.company_profile")
                    )

            if address:
                location = company.location

                if location is None:
                    location = CompanyLocation(
                        company=company,
                        address=address
                    )
                    db.session.add(location)

                location.address = address
                location.latitude = latitude
                location.longitude = longitude

                if latitude is not None and longitude is not None:
                    location.google_maps_url = (
                        "https://www.google.com/maps?q="
                        f"{latitude},{longitude}"
                    )
                else:
                    location.google_maps_url = (
                        "https://www.google.com/maps/search/?api=1&query="
                        + address.replace(" ", "+")
                    )

                # Keep the old location field populated while
                # the remaining templates are migrated.
                profile.company_location = address

            else:
                # Removing the address removes the shared location.
                company.location = None
                profile.company_location = None

            db.session.commit()

            flash(
                "Company profile saved successfully!",
                "success"
            )

            return redirect(
                url_for("recruiter.company_profile")
            )

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Failed to save the shared company profile."
            )

            flash(
                "We couldn't save the company profile. "
                "Please try again.",
                "danger"
            )
    company = profile.company

    # Use legacy information as a temporary fallback for older records.
    company_name = (
        company.company_name
        if company
        else profile.company_name
    )

    industry = company.industry if company else profile.industry
    company_size = company.company_size if company else profile.company_size
    company_website = (
        company.company_website
        if company
        else profile.company_website
    )
    company_description = (
        company.company_description
        if company
        else profile.company_description
    )
    company_logo = company.company_logo if company else profile.company_logo

    location = company.location if company else None

    return render_template(
        "recruiter/company_profile.html",
        profile=profile,
        company=company,
        company_name=company_name,
        industry=industry,
        company_size=company_size,
        company_website=company_website,
        company_description=company_description,
        company_logo=company_logo,
        location=location
    )
# ==========================================================
# Shared Company Logo
# ==========================================================


@recruiter.route("/company-logo", methods=["POST"])
@login_required
def company_logo():

    if current_user.role != "Recruiter":
        return redirect(url_for("dashboard.home"))

    profile = RecruiterProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile or not profile.company:
        flash(
            "Please save your company profile before uploading a logo.",
            "warning"
        )
        return redirect(url_for("recruiter.company_profile"))

    file = request.files.get("company_logo")

    if not file or not file.filename:
        flash("Please select a company logo.", "danger")
        return redirect(url_for("recruiter.company_profile"))

    allowed_extensions = {"jpg", "jpeg", "png", "webp"}

    if "." not in file.filename:
        flash("Invalid image filename.", "danger")
        return redirect(url_for("recruiter.company_profile"))

    extension = file.filename.rsplit(".", 1)[-1].lower()

    if extension not in allowed_extensions:
        flash(
            "Only JPG, JPEG, PNG and WEBP images are allowed.",
            "danger"
        )
        return redirect(url_for("recruiter.company_profile"))

    company = profile.company
    old_logo = company.company_logo

    try:
        result = upload_image(
            file,
            folder="cvision/company-logos"
        )

        new_filename = result["filename"]

        company.company_logo = new_filename
        profile.company_logo = new_filename

        db.session.commit()

        if old_logo and old_logo != new_filename:
            delete_stored_image(
                old_logo,
                local_folder="uploads/profile"
            )

        flash("Company logo updated successfully!", "success")

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Company logo upload failed.")
        flash("Unable to update the company logo.", "danger")

    return redirect(url_for("recruiter.company_profile"))

# ==========================================================
# Job Management
# ==========================================================

@recruiter.route(
    "/jobs",
    methods=["GET"]
)
@login_required
def jobs():

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    close_expired_jobs()

    jobs = Job.query.filter(
        Job.recruiter_id == current_user.id,
        Job.status.in_(["Published", "Closed"])
    ).order_by(
        Job.created_at.desc()
    ).all()

    return render_template(
        "recruiter/jobs.html",
        jobs=jobs
    )

# ==========================================================
# REAL-TIME RECRUITER JOB UPDATES
# ==========================================================

@recruiter.route(
    "/jobs/live",
    methods=["GET"]
)
@login_required
def jobs_live():

    if current_user.role != "Recruiter":
        return {
            "error": "Unauthorized"
        }, 403

    close_expired_jobs()

    jobs = Job.query.filter(
        Job.recruiter_id == current_user.id,
        func.lower(
            func.trim(Job.status)
        ).in_(["published", "closed"])
    ).order_by(
        Job.created_at.desc()
    ).all()

    job_data = []

    for job in jobs:

        job_data.append({

            "id": job.id,

            "job_title": job.job_title,

            "description": job.description or "",

            "location": job.location or "",

            "job_type": job.job_type or "",

            "salary": job.salary or "",

            "status": (
                job.status.strip()
                if job.status
                else "Published"
            ),

            "application_deadline": (
                job.application_deadline.strftime("%d %b %Y")
                if job.application_deadline
                else None
            )

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
                job["status"],
                job["application_deadline"]
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
# Move Job to Closed
# ==========================================================

@recruiter.route(
    "/jobs/<int:job_id>/move-to-closed",
    methods=["POST"]
)
@login_required
def move_to_closed(job_id):

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    job = Job.query.filter_by(
        id=job_id,
        recruiter_id=current_user.id
    ).first()

    if not job:

        flash(
            "Job not found.",
            "danger"
        )

        return redirect(
            url_for("recruiter.jobs")
        )

    if job.status != "Closed":

        flash(
            "Only closed jobs can be moved to Closed Jobs.",
            "warning"
        )

        return redirect(
            url_for("recruiter.jobs")
        )

    job.status = "Archived"

    db.session.commit()

    flash(
        "Job moved to Closed Jobs successfully!",
        "success"
    )

    return redirect(
        url_for("recruiter.jobs")
    )

# ==========================================================
# Closed Jobs
# ==========================================================

@recruiter.route(
    "/jobs/closed",
    methods=["GET"]
)
@login_required
def closed_jobs():

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    jobs = Job.query.filter(
        Job.recruiter_id == current_user.id,
        func.lower(
            func.trim(Job.status)
        ) == "archived"
    ).order_by(
        Job.created_at.desc()
    ).all()

    return render_template(
        "recruiter/closed_jobs.html",
        jobs=jobs
    )

# ==========================================================
# Create Job
# ==========================================================

@recruiter.route(
    "/jobs/create",
    methods=["GET", "POST"]
)
@login_required
def create_job():

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    if request.method == "POST":

        job_title = request.form.get(
            "job_title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        job_type = request.form.get(
            "job_type",
            ""
        ).strip()

        experience_required = request.form.get(
            "experience_required",
            ""
        ).strip()

        education_required = request.form.get(
            "education_required",
            ""
        ).strip()

        skills_required = request.form.get(
            "skills_required",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        salary = request.form.get(
            "salary",
            ""
        ).strip()

        deadline_text = request.form.get(
            "application_deadline",
            ""
        ).strip()

        if not job_title or not description or not job_type:

            flash(
                "Job title, description and job type are required.",
                "danger"
            )

            return redirect(
                url_for("recruiter.create_job")
            )

        application_deadline = None

        if deadline_text:

            try:

                application_deadline = datetime.strptime(
                    deadline_text,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid application deadline.",
                    "danger"
                )

                return redirect(
                    url_for("recruiter.create_job")
                )

        job = Job(
            recruiter_id=current_user.id,
            job_title=job_title,
            description=description,
            job_type=job_type,
            experience_required=experience_required,
            education_required=education_required,
            skills_required=skills_required,
            location=location,
            salary=salary,
            application_deadline=application_deadline,
            status="Published"
        )

        # Save the published job
        db.session.add(job)
        db.session.commit()

        # --------------------------------------------------
        # Notify all applicants about the newly posted job
        # --------------------------------------------------

        try:

            from models.user import User

            applicants = User.query.filter_by(
                role="Applicant"
            ).all()

            for applicant in applicants:

                db.session.add(
                    Notification(
                        user_id=applicant.id,
                        title="New Job Posted",
                        message=(
                            f"{current_user.username} posted a new job: "
                            f"{job.job_title}."
                        ),
                        notification_type="new_job"
                    )
                )

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                "New job notification error:",
                repr(e)
            )

        flash(
            "Job created successfully!",
            "success"
        )

        return redirect(
            url_for("recruiter.jobs")
        )

    return render_template(
        "recruiter/create_job.html"
    )

# ==========================================================
# Job Details
# ==========================================================

@recruiter.route(
    "/jobs/<int:job_id>",
    methods=["GET"]
)
@login_required
def job_detail(job_id):

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    close_expired_jobs()

    job = Job.query.filter_by(
        id=job_id,
        recruiter_id=current_user.id
    ).first()

    if not job:

        flash(
            "Job not found.",
            "danger"
        )

        return redirect(
            url_for("recruiter.jobs")
        )

    return render_template(
        "recruiter/job_detail.html",
        job=job
    )


# ==========================================================
# Edit Job
# ==========================================================

@recruiter.route(
    "/jobs/<int:job_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_job(job_id):

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    close_expired_jobs()

    job = Job.query.filter_by(
        id=job_id,
        recruiter_id=current_user.id
    ).first()

    if not job:

        flash(
            "Job not found.",
            "danger"
        )

        return redirect(
            url_for("recruiter.jobs")
        )

    if job.status in ["Closed", "Archived"]:

        flash(
            "Closed jobs cannot be edited.",
            "warning"
        )

        return redirect(
            url_for(
                "recruiter.job_detail",
                job_id=job.id
            )
        )

    if request.method == "POST":

        job.job_title = request.form.get(
            "job_title",
            ""
        ).strip()

        job.description = request.form.get(
            "description",
            ""
        ).strip()

        job.job_type = request.form.get(
            "job_type",
            ""
        ).strip()

        job.experience_required = request.form.get(
            "experience_required",
            ""
        ).strip()

        job.education_required = request.form.get(
            "education_required",
            ""
        ).strip()

        job.skills_required = request.form.get(
            "skills_required",
            ""
        ).strip()

        job.location = request.form.get(
            "location",
            ""
        ).strip()

        job.salary = request.form.get(
            "salary",
            ""
        ).strip()

        deadline_text = request.form.get(
            "application_deadline",
            ""
        ).strip()

        if deadline_text:

            try:

                job.application_deadline = datetime.strptime(
                    deadline_text,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid application deadline.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "recruiter.edit_job",
                        job_id=job.id
                    )
                )

        else:

            job.application_deadline = None

        db.session.commit()

        flash(
            "Job updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "recruiter.job_detail",
                job_id=job.id
            )
        )

    return render_template(
        "recruiter/edit_job.html",
        job=job
    )


# ==========================================================
# Publish Job
# ==========================================================

@recruiter.route(
    "/jobs/<int:job_id>/publish",
    methods=["POST"]
)
@login_required
def publish_job(job_id):

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    job = Job.query.filter_by(
        id=job_id,
        recruiter_id=current_user.id
    ).first()

    if not job:

        flash(
            "Job not found.",
            "danger"
        )

        return redirect(
            url_for("recruiter.jobs")
        )

    if job.status in ["Closed", "Archived"]:

        flash(
            "A closed job cannot be published again.",
            "warning"
        )

        return redirect(
            url_for(
                "recruiter.job_detail",
                job_id=job.id
            )
        )

    if (
        job.application_deadline
        and job.application_deadline < date.today()
    ):

        job.status = "Closed"

        db.session.commit()

        flash(
            "This job's deadline has expired and the job is now closed.",
            "warning"
        )

        return redirect(
            url_for(
                "recruiter.job_detail",
                job_id=job.id
            )
        )

    job.status = "Published"

    db.session.commit()

    flash(
        "Job published successfully!",
        "success"
    )

    return redirect(
        url_for("recruiter.jobs")
    )


# ==========================================================
# Close Job
# ==========================================================

@recruiter.route(
    "/jobs/<int:job_id>/close",
    methods=["POST"]
)
@login_required
def close_job(job_id):

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    job = Job.query.filter_by(
        id=job_id,
        recruiter_id=current_user.id
    ).first()

    if not job:

        flash(
            "Job not found.",
            "danger"
        )

        return redirect(
            url_for("recruiter.jobs")
        )

    if job.status != "Published":

        flash(
            "Only published jobs can be closed.",
            "warning"
        )

        return redirect(
            url_for("recruiter.jobs")
        )

    job.status = "Closed"

    db.session.commit()

    flash(
        "Job closed successfully!",
        "success"
    )

    return redirect(
        url_for("recruiter.jobs")
    )


# ==========================================================
# Delete Job
# ==========================================================

@recruiter.route(
    "/jobs/<int:job_id>/delete",
    methods=["POST"]
)
@login_required
def delete_job(job_id):

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    job = Job.query.filter_by(
        id=job_id,
        recruiter_id=current_user.id
    ).first()

    if not job:

        flash(
            "Job not found.",
            "danger"
        )

        return redirect(
            url_for("recruiter.jobs")
        )

    db.session.delete(job)
    db.session.commit()

    flash(
        "Job deleted successfully!",
        "success"
    )

    return redirect(
        url_for("recruiter.jobs")
    )


# ==========================================================
# Recruiter Application Management
# ==========================================================

@recruiter.route(
    "/applications",
    methods=["GET"]
)
@login_required
def applications():

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    # Automatically close expired jobs.
    close_expired_jobs()

    applications = Application.query.join(
        Job,
        Application.job_id == Job.id
    ).join(
        User,
        Application.applicant_id == User.id
    ).filter(
        Job.recruiter_id == current_user.id
    ).order_by(
        Application.applied_at.desc()
    ).all()

    return render_template(
        "recruiter/applications.html",
        applications=applications
    )

# ==========================================================
# REAL-TIME RECRUITER APPLICATION UPDATES
# ==========================================================

@recruiter.route(
    "/applications/live",
    methods=["GET"]
)
@login_required
def applications_live():

    if current_user.role != "Recruiter":
        return {
            "error": "Unauthorized"
        }, 403

    close_expired_jobs()

    applications = Application.query.join(
        Job,
        Application.job_id == Job.id
    ).join(
        User,
        Application.applicant_id == User.id
    ).filter(
        Job.recruiter_id == current_user.id
    ).order_by(
        Application.applied_at.desc()
    ).all()

    application_data = []

    for application in applications:

        applicant = application.applicant
        job = application.job

        application_data.append({

            "id": application.id,

            "applicant_name": (
                applicant.full_name
                if applicant
                else "Unknown Applicant"
            ),

            "applicant_username": (
                applicant.username
                if applicant
                else ""
            ),
            "job_id": application.job_id,
            "job_title": (
                job.job_title
                if job
                else "Unknown Job"
            ),

            "job_location": (
                job.location
                if job and job.location
                else ""
            ),

            "status": (
                application.status
                if application.status
                else "Pending"
            ),

            "applied_date": (
                application.applied_at.strftime("%d %b %Y")
                if application.applied_at
                else "—"
            ),

            "applied_time": (
                application.applied_at.strftime("%I:%M %p")
                if application.applied_at
                else ""
            )

        })

    version_source = repr(
        [
            (
                application["id"],
                application["applicant_name"],
                application["applicant_username"],
                application["job_title"],
                application["job_location"],
                application["status"],
                application["applied_date"],
                application["applied_time"]
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
# Ranked Candidates for a Job
# ==========================================================

@recruiter.route(
    "/jobs/<int:job_id>/candidates",
    methods=["GET"]
)
@login_required
def ranked_candidates(job_id):

    if current_user.role != "Recruiter":
        return redirect(url_for("dashboard.home"))

    close_expired_jobs()

    job = Job.query.filter_by(
        id=job_id,
        recruiter_id=current_user.id
    ).first()

    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("recruiter.jobs"))

    applications = Application.query.filter_by(
        job_id=job.id
    ).all()

    ranked_applications = []

    for application in applications:
        try:
            result = calculate_job_match(job, application)
            ranked_applications.append(result)
        except Exception as error:
            current_app.logger.exception(
                "Job matching failed for application %s: %s",
                application.id,
                error
            )

    ranked_applications.sort(
        key=lambda item: item["overall_score"],
        reverse=True
    )

    return render_template(
        "recruiter/ranked_candidates.html",
        job=job,
        candidates=ranked_applications
    )
# ==========================================================
# Application Details
# ==========================================================

@recruiter.route(
    "/applications/<int:application_id>",
    methods=["GET"]
)
@login_required
def application_detail(application_id):

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    application = Application.query.join(
        Job,
        Application.job_id == Job.id
    ).filter(
        Application.id == application_id,
        Job.recruiter_id == current_user.id
    ).first()

    if not application:

        flash(
            "Application not found.",
            "danger"
        )

        return redirect(
            url_for("recruiter.applications")
        )

    applicant = application.applicant

    applicant_profile = ApplicantProfile.query.filter_by(
        user_id=applicant.id
    ).first()

    active_resume = Resume.query.filter_by(
        user_id=applicant.id,
        status="active"
    ).order_by(
        Resume.uploaded_at.desc()
    ).first()

    return render_template(
        "recruiter/application_detail.html",
        application=application,
        applicant=applicant,
        applicant_profile=applicant_profile,
        active_resume=active_resume
    )


# ==========================================================
# Update Application Status
# ==========================================================

@recruiter.route(
    "/applications/<int:application_id>/status",
    methods=["POST"]
)
@login_required
def update_application_status(application_id):

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    application = Application.query.join(
        Job,
        Application.job_id == Job.id
    ).filter(
        Application.id == application_id,
        Job.recruiter_id == current_user.id
    ).first()

    if not application:

        flash(
            "Application not found.",
            "danger"
        )

        return redirect(
            url_for("recruiter.applications")
        )

    new_status = request.form.get(
        "status",
        ""
    ).strip()

    allowed_statuses = {
        "Pending",
        "Shortlisted",
        "Rejected",
        "Hired"
    }

    if new_status not in allowed_statuses:

        flash(
            "Invalid application status.",
            "danger"
        )

        return redirect(
            url_for(
                "recruiter.application_detail",
                application_id=application.id
            )
        )

    current_status = application.status

    # ------------------------------------------------------
    # Status transition rules
    # ------------------------------------------------------

    valid_transitions = {
        "Pending": {
            "Pending",
            "Shortlisted",
            "Rejected"
        },
        "Shortlisted": {
            "Shortlisted",
            "Rejected",
            "Hired"
        },
        "Rejected": {
            "Rejected"
        },
        "Hired": {
            "Hired"
        }
    }

    allowed_transitions = valid_transitions.get(
        current_status,
        set()
    )

    if new_status not in allowed_transitions:

        flash(
            f"Application cannot be changed from "
            f"{current_status} to {new_status}.",
            "warning"
        )

        return redirect(
            url_for(
                "recruiter.application_detail",
                application_id=application.id
            )
        )

    application.status = new_status

    if new_status != current_status:
        db.session.add(
            Notification(
                user_id=application.applicant_id,
                title="Application Status Updated",
                message=(
                    f"Your application for "
                    f"{application.job.job_title} "
                    f"has been updated to {new_status}."
                ),
                notification_type="application_status",
                application_id=application.id
            )
        )

    db.session.commit()
    db.session.commit()

    flash(
        f"Application status updated to {new_status}.",
        "success"
    )

    return redirect(
        url_for(
            "recruiter.application_detail",
            application_id=application.id
        )
    )


# ==========================================================
# View / Download Applicant Resume
# ==========================================================

@recruiter.route(
    "/applications/<int:application_id>/resume",
    methods=["GET"]
)
@login_required
def view_applicant_resume(application_id):

    if current_user.role != "Recruiter":
        return redirect(url_for("dashboard.home"))

    application = Application.query.join(
        Job,
        Application.job_id == Job.id
    ).filter(
        Application.id == application_id,
        Job.recruiter_id == current_user.id
    ).first()

    if not application:
        flash("Application not found.", "danger")
        return redirect(url_for("recruiter.applications"))

    active_resume = Resume.query.filter_by(
        user_id=application.applicant_id,
        status="active"
    ).order_by(
        Resume.uploaded_at.desc()
    ).first()

    if not active_resume:
        flash(
            "This applicant does not have an active resume.",
            "warning"
        )
        return redirect(
            url_for(
                "recruiter.application_detail",
                application_id=application.id
            )
        )

    if is_cloudinary_file(active_resume.file_path):

        public_id = get_cloudinary_public_id(active_resume.file_path)

        try:
            signed_url = get_private_file_url(public_id)
            return redirect(signed_url)

        except Exception as e:
            print("Cloudinary recruiter resume error:", repr(e))
            flash("Unable to access the resume.", "danger")
            return redirect(
                url_for(
                    "recruiter.application_detail",
                    application_id=application.id
                )
            )

    resume_folder = current_app.config["RESUME_UPLOAD_FOLDER"]
    file_path = os.path.join(
        resume_folder,
        active_resume.file_path
    )

    if not os.path.exists(file_path):
        flash("Resume file could not be found.", "danger")
        return redirect(
            url_for(
                "recruiter.application_detail",
                application_id=application.id
            )
        )

    return send_from_directory(
        resume_folder,
        active_resume.file_path,
        as_attachment=False,
        download_name=active_resume.file_name
    )
# ==========================================================
# Recruiter Settings
# ==========================================================

@recruiter.route(
    "/settings",
    methods=["GET"]
)
@login_required
def settings():

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    return render_template(
        "recruiter/settings.html"
    )


# ==========================================================
# Change Password
# ==========================================================

@recruiter.route(
    "/settings/change-password",
    methods=["POST"]
)
@login_required
def change_password():

    if current_user.role != "Recruiter":

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

    if not check_password_hash(
        current_user.password,
        current_password
    ):

        flash(
            "Current password is incorrect.",
            "danger"
        )

        return redirect(
            url_for("recruiter.settings")
        )

    if len(new_password) < 8:

        flash(
            "New password must contain at least 8 characters.",
            "danger"
        )

        return redirect(
            url_for("recruiter.settings")
        )

    if new_password != confirm_password:

        flash(
            "New passwords do not match.",
            "danger"
        )

        return redirect(
            url_for("recruiter.settings")
        )

    if check_password_hash(
        current_user.password,
        new_password
    ):

        flash(
            "New password must be different from your current password.",
            "warning"
        )

        return redirect(
            url_for("recruiter.settings")
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
        url_for("recruiter.settings")
    )


# ==========================================================
# Change Email
# ==========================================================

@recruiter.route(
    "/settings/change-email",
    methods=["POST"]
)
@login_required
def change_email():

    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )

    new_email = request.form.get(
        "new_email",
        ""
    ).strip().lower()

    if not new_email:

        flash(
            "Please enter a new email address.",
            "danger"
        )

        return redirect(
            url_for("recruiter.settings")
        )

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
            url_for("recruiter.settings")
        )

    if new_email == current_user.email.lower():

        flash(
            "This is already your current email address.",
            "warning"
        )

        return redirect(
            url_for("recruiter.settings")
        )

    verification_code = str(
        random.randint(
            100000,
            999999
        )
    )

    current_user.verification_code = verification_code

    current_user.verification_expiry = (
        datetime.utcnow()
        + timedelta(minutes=10)
    )

    session["pending_email"] = new_email

    db.session.commit()

    try:

        msg = Message(
            subject="CVision - Verify Your New Email",
            sender=current_app.config[
                "MAIL_USERNAME"
            ],
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
        print("RECRUITER EMAIL SENDING ERROR:")
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
            url_for("recruiter.settings")
        )

    flash(
        "A verification code has been sent to your new email address.",
        "success"
    )

    return redirect(
        url_for("recruiter.verify_new_email")
    )


# ==========================================================
# Verify New Email
# ==========================================================

@recruiter.route(
    "/settings/verify-email",
    methods=["GET", "POST"]
)
@login_required
def verify_new_email():

    if current_user.role != "Recruiter":

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
            url_for("recruiter.settings")
        )

    if request.method == "POST":

        code = request.form.get(
            "verification_code",
            ""
        ).strip()

        if code != current_user.verification_code:

            flash(
                "Invalid verification code.",
                "danger"
            )

            return redirect(
                url_for("recruiter.verify_new_email")
            )

        if (
            not current_user.verification_expiry
            or
            datetime.utcnow()
            > current_user.verification_expiry
        ):

            flash(
                "Verification code has expired.",
                "danger"
            )

            return redirect(
                url_for("recruiter.settings")
            )

        current_user.email = pending_email

        current_user.verification_code = None

        current_user.verification_expiry = None

        current_user.is_verified = True

        session.pop(
            "pending_email",
            None
        )

        db.session.commit()

        flash(
            "Email address changed successfully!",
            "success"
        )

        return redirect(
            url_for("recruiter.settings")
        )

    return render_template(
        "recruiter/verify_email.html"
    )

# ==========================================================
# Recruiter Profile View (Read Only)
# ==========================================================

@recruiter.route("/profile-view", methods=["GET"])
@login_required
def profile_view():

    if current_user.role != "Recruiter":
        return redirect(url_for("dashboard.home"))

    profile = RecruiterProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    return render_template(
        "recruiter/profile_view.html",
        profile=profile
    )


# ==========================================================
# Company Profile View (Read Only)
# ==========================================================

@recruiter.route("/company-view", methods=["GET"])
@login_required
def company_view():

    if current_user.role != "Recruiter":
        return redirect(url_for("dashboard.home"))

    profile = RecruiterProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    company = profile.company if profile else None

    location = company.location if company else None

    return render_template(
        "recruiter/company_view.html",
        profile=profile,
        company=company,
        location=location
    )


# ==========================================================
# Public Recruiter Profile
# ==========================================================

@recruiter.route("/public/<string:username>", methods=["GET"])
@login_required
def public_profile(username):

    # Only logged-in users can reach this route.
    user = User.query.filter(
        User.username == username,
        func.lower(func.trim(User.role)) == "recruiter"
    ).first_or_404()

    profile = RecruiterProfile.query.filter_by(
        user_id=user.id
    ).first()

    # Use the shared company record, not duplicate recruiter fields.
    company = profile.company if profile else None
    location = company.location if company else None

    return render_template(
        "recruiter/public_profile.html",
        user=user,
        profile=profile,
        company=company,
        location=location
    )
