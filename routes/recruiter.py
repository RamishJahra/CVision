from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash
)

from flask_login import login_required, current_user

from models import db
from models.profile import RecruiterProfile


recruiter = Blueprint(
    "recruiter",
    __name__,
    url_prefix="/recruiter"
)


# ==========================
# Recruiter Profile
# ==========================

@recruiter.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    # Only Recruiter can access
    if current_user.role != "Recruiter":

        return redirect(
            url_for("dashboard.home")
        )


    # Find recruiter profile
    profile = RecruiterProfile.query.filter_by(
        user_id=current_user.id
    ).first()


    # Safety check
    if not profile:

        profile = RecruiterProfile(
            user_id=current_user.id
        )

        db.session.add(profile)

        db.session.commit()


    # ==========================
    # Update Profile
    # ==========================

    if request.method == "POST":

        profile.job_title = request.form.get(
            "job_title"
        )

        profile.company_name = request.form.get(
            "company_name"
        )

        profile.company_description = request.form.get(
            "company_description"
        )

        profile.company_website = request.form.get(
            "company_website"
        )

        profile.industry = request.form.get(
            "industry"
        )

        profile.company_size = request.form.get(
            "company_size"
        )

        profile.company_location = request.form.get(
            "company_location"
        )

        profile.linkedin_url = request.form.get(
            "linkedin_url"
        )

        profile.bio = request.form.get(
            "bio"
        )


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