from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from models import db
from models.user import User


admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


def admin_required():

    return (
        current_user.is_authenticated
        and current_user.role == "Admin"
    )


@admin.route("/users")
@login_required
def users():

    if not admin_required():

        return "Unauthorized", 403


    search = request.args.get(
        "search",
        ""
    ).strip()


    role = request.args.get(
        "role",
        ""
    ).strip()


    query = User.query


    # ==========================
    # Search
    # ==========================

    if search:

        query = query.filter(
            db.or_(
                User.full_name.ilike(
                    f"%{search}%"
                ),
                User.username.ilike(
                    f"%{search}%"
                ),
                User.email.ilike(
                    f"%{search}%"
                )
            )
        )


    # ==========================
    # Role Filter
    # ==========================

    if role:

        query = query.filter(
            User.role == role
        )


    users = query.order_by(
        User.created_at.desc()
    ).all()


    return render_template(
        "admin/users.html",
        users=users,
        search=search,
        selected_role=role
    )