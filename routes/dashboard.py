from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models.user import User


dashboard = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


@dashboard.route("/")
@login_required
def home():

    if current_user.role == "Applicant":

        return render_template(
            "dashboard/applicant.html"
        )


    elif current_user.role == "Recruiter":

        return render_template(
            "dashboard/recruiter.html"
        )


    elif current_user.role == "Admin":

        # ==========================
        # Admin Statistics
        # ==========================

        total_users = User.query.count()

        total_applicants = User.query.filter_by(
            role="Applicant"
        ).count()

        total_recruiters = User.query.filter_by(
            role="Recruiter"
        ).count()

        verified_users = User.query.filter_by(
            is_verified=True
        ).count()


        # ==========================
        # Recent Users
        # ==========================

        recent_users = User.query.order_by(
            User.created_at.desc()
        ).limit(10).all()


        return render_template(
            "dashboard/admin.html",
            total_users=total_users,
            total_applicants=total_applicants,
            total_recruiters=total_recruiters,
            verified_users=verified_users,
            recent_users=recent_users
        )


    return "Invalid Role"