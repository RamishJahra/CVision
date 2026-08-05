from flask import Blueprint, render_template
from flask_login import login_required, current_user


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

        return render_template(
            "dashboard/admin.html"
        )


    return "Invalid Role"