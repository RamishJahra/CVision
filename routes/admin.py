from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user

from models import db
from models.user import User


admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ==========================================================
# Admin Access Protection
# ==========================================================

def admin_required():

    if not current_user.is_authenticated:
        return False

    if current_user.role != "Admin":
        return False

    return True


# ==========================================================
# User Management
# ==========================================================

@admin.route("/users")
@login_required
def users():

    if not admin_required():
        return redirect(
            url_for("dashboard.home")
        )


    search = request.args.get(
        "search",
        ""
    ).strip()


    selected_role = request.args.get(
        "role",
        ""
    ).strip()


    # ------------------------------------------------------
    # Only Applicant and Recruiter
    # Admin is intentionally excluded
    # ------------------------------------------------------

    query = User.query.filter(
        User.role.in_(
            ["Applicant", "Recruiter"]
        )
    )


    # ------------------------------------------------------
    # Search
    # ------------------------------------------------------

    if search:

        search_value = f"%{search}%"

        query = query.filter(
            db.or_(
                User.full_name.ilike(search_value),
                User.username.ilike(search_value),
                User.email.ilike(search_value)
            )
        )


    # ------------------------------------------------------
    # Role Filter
    # Only Applicant / Recruiter allowed
    # ------------------------------------------------------

    if selected_role in [
        "Applicant",
        "Recruiter"
    ]:

        query = query.filter(
            User.role == selected_role
        )


    users = query.order_by(
        User.id.desc()
    ).all()


    # ------------------------------------------------------
    # Statistics
    # ------------------------------------------------------
    # ------------------------------------------------------
    # Statistics: Applicants and Recruiters ONLY
    # ------------------------------------------------------

    eligible_users = User.query.filter(
        User.role.in_(["Applicant", "Recruiter"])
    )

    total_users = eligible_users.count()

    total_applicants = User.query.filter_by(
        role="Applicant"
    ).count()

    total_recruiters = User.query.filter_by(
        role="Recruiter"
    ).count()

    verified_users = User.query.filter(
        User.role.in_(["Applicant", "Recruiter"]),
        User.is_verified == True
    ).count()


    return render_template(
        "admin/users.html",
        users=users,
        search=search,
        selected_role=selected_role,
        total_users=total_users,
        total_applicants=total_applicants,
        total_recruiters=total_recruiters,
        verified_users=verified_users
    )


# ==========================================================
# AJAX User Table
# ==========================================================

@admin.route("/users/filter")
@login_required
def filter_users():

    if not admin_required():

        return jsonify({
            "success": False,
            "message": "Unauthorized access."
        }), 403


    search = request.args.get(
        "search",
        ""
    ).strip()


    selected_role = request.args.get(
        "role",
        ""
    ).strip()


    # ------------------------------------------------------
    # Applicant + Recruiter ONLY
    # ------------------------------------------------------

    query = User.query.filter(
        User.role.in_(
            ["Applicant", "Recruiter"]
        )
    )


    # ------------------------------------------------------
    # Search
    # ------------------------------------------------------

    if search:

        search_value = f"%{search}%"

        query = query.filter(
            db.or_(
                User.full_name.ilike(search_value),
                User.username.ilike(search_value),
                User.email.ilike(search_value)
            )
        )


    # ------------------------------------------------------
    # Role
    # ------------------------------------------------------

    if selected_role in [
        "Applicant",
        "Recruiter"
    ]:

        query = query.filter(
            User.role == selected_role
        )


    users = query.order_by(
        User.id.desc()
    ).all()


    return render_template(
        "admin/_users_table.html",
        users=users
    )


# ==========================================================
# Ban / Unban User
# ==========================================================

@admin.route(
    "/users/<int:user_id>/toggle-ban",
    methods=["POST"]
)
@login_required
def toggle_ban(user_id):

    if not admin_required():

        return jsonify({
            "success": False,
            "message": "Unauthorized access."
        }), 403


    user = db.session.get(
        User,
        user_id
    )


    if not user:

        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404


    # ------------------------------------------------------
    # Admin Protection
    # ------------------------------------------------------

    if user.role == "Admin":

        return jsonify({
            "success": False,
            "message": "Admin accounts cannot be banned."
        }), 403


    # ------------------------------------------------------
    # Toggle
    # ------------------------------------------------------

    user.is_banned = not user.is_banned

    db.session.commit()


    if user.is_banned:

        message = (
            f"{user.full_name} has been banned."
        )

    else:

        message = (
            f"{user.full_name} has been unbanned."
        )


    return jsonify({
        "success": True,
        "banned": user.is_banned,
        "message": message
    })


# ==========================================================
# Delete User
# ==========================================================

@admin.route(
    "/users/<int:user_id>/delete",
    methods=["POST"]
)
@login_required
def delete_user(user_id):

    if not admin_required():

        return jsonify({
            "success": False,
            "message": "Unauthorized access."
        }), 403


    user = db.session.get(
        User,
        user_id
    )


    if not user:

        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404


    # ------------------------------------------------------
    # Admin Protection
    # ------------------------------------------------------

    if user.role == "Admin":

        return jsonify({
            "success": False,
            "message": "Admin accounts cannot be deleted."
        }), 403


    # ------------------------------------------------------
    # Store name before deleting the object
    # ------------------------------------------------------

    user_name = user.full_name


    try:

        # --------------------------------------------------
        # Applicant Profile
        # --------------------------------------------------

        if user.applicant_profile:

            db.session.delete(
                user.applicant_profile
            )


        # --------------------------------------------------
        # Recruiter Profile
        # --------------------------------------------------

        if user.recruiter_profile:

            db.session.delete(
                user.recruiter_profile
            )


        # --------------------------------------------------
        # Education
        # --------------------------------------------------

        for education in user.educations:

            db.session.delete(
                education
            )


        # --------------------------------------------------
        # Work Experience
        # --------------------------------------------------

        for experience in user.work_experiences:

            db.session.delete(
                experience
            )


        # --------------------------------------------------
        # Skills
        # --------------------------------------------------

        for skill in user.skills:

            db.session.delete(
                skill
            )


        # --------------------------------------------------
        # Certifications
        # --------------------------------------------------

        for certification in user.certifications:

            db.session.delete(
                certification
            )


        # --------------------------------------------------
        # Projects
        # --------------------------------------------------

        for project in user.projects:

            db.session.delete(
                project
            )


        # --------------------------------------------------
        # Finally delete User
        # --------------------------------------------------

        db.session.delete(user)

        db.session.commit()


        return jsonify({
            "success": True,
            "message": (
                f"{user_name} has been deleted."
            )
        })


    except Exception as e:

        db.session.rollback()

        print(
            "DELETE USER ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": (
                "Something went wrong while deleting "
                "the user."
            )
        }), 500