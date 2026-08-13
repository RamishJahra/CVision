import os
import uuid


from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    current_app,
    session
)

from flask_login import login_required, current_user
from flask_mail import Message

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from models import db,mail
from models.user import User
from models.profile import RecruiterProfile

import random

from datetime import datetime, timedelta

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

# ==========================
# Recruiter Profile Picture
# ==========================

@recruiter.route(
    "/profile-picture",
    methods=["POST"]
)
@login_required
def profile_picture():

    if current_user.role != "Recruiter":

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
            url_for("recruiter.profile")
        )


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
            url_for("recruiter.profile")
        )


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


    current_user.profile_image = new_filename

    db.session.commit()


    flash(
        "Profile picture updated successfully!",
        "success"
    )


    return redirect(
        url_for("recruiter.profile")
    )

# ==========================
# Recruiter Settings
# ==========================

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

# ==========================
# Change Password
# ==========================

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
            url_for("recruiter.settings")
        )


    # Password length

    if len(new_password) < 8:

        flash(
            "New password must contain at least 8 characters.",
            "danger"
        )

        return redirect(
            url_for("recruiter.settings")
        )


    # Confirm password

    if new_password != confirm_password:

        flash(
            "New passwords do not match.",
            "danger"
        )

        return redirect(
            url_for("recruiter.settings")
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

# ==========================
# Change Email
# ==========================

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


    # Duplicate email check

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


    # Same email check

    if new_email == current_user.email.lower():

        flash(
            "This is already your current email address.",
            "warning"
        )

        return redirect(
            url_for("recruiter.settings")
        )


    # Generate verification code

    verification_code = str(
        random.randint(100000, 999999)
    )


    current_user.verification_code = (
        verification_code
    )

    current_user.verification_expiry = (
        datetime.utcnow()
        + timedelta(minutes=10)
    )


    session["pending_email"] = new_email

    db.session.commit()


    # Send email

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

# ==========================
# Verify New Email
# ==========================

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


        # Check code

        if code != current_user.verification_code:

            flash(
                "Invalid verification code.",
                "danger"
            )

            return redirect(
                url_for("recruiter.verify_new_email")
            )


        # Check expiry

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


        # Update email

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