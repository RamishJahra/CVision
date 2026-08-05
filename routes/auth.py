from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.location import District, Area
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import random

from datetime import datetime, timedelta

from flask_mail import Message

from models import mail

from flask_login import login_user, logout_user, login_required

from models import db

from models.user import User
import re

auth = Blueprint("auth", __name__)


# ==========================
# Register
# ==========================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name")

        username = request.form.get("username")

        email = request.form.get("email")

        phone = request.form.get("phone")
        phone_pattern = r"^01[3-9]\d{8}$"


        if not re.match(phone_pattern, phone):

            flash(
                "Invalid Bangladesh phone number",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        date_of_birth = request.form.get("date_of_birth")

        district_id = request.form.get("district_id")

        area_id = request.form.get("area_id")

        password = request.form.get("password")

        confirm_password = request.form.get("confirm_password")

        role = request.form.get("role")

        # Check duplicate username
        if User.query.filter_by(username=username).first():

            flash("Username already exists.", "danger")

            return redirect(url_for("auth.register"))

        # Check duplicate email
        if User.query.filter_by(email=email).first():

            flash("Email already exists.", "danger")

            return redirect(url_for("auth.register"))
        if password != confirm_password:

            flash(
                "Passwords do not match",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        hashed_password = generate_password_hash(password)
        otp = str(random.randint(100000,999999))
        
        user = User(

    full_name=full_name,

    username=username,

    email=email,

    phone=phone,

    date_of_birth=date_of_birth,

    district_id=district_id,

    area_id=area_id,

    password=hashed_password,

    role=role,

    verification_code=otp,

    verification_expiry=datetime.now() + timedelta(minutes=10),

    is_verified=False

)
        db.session.add(user)

        db.session.commit()
        msg = Message(

            "CVision Email Verification",

            sender="yourgmail@gmail.com",

            recipients=[email]

        )


        msg.body = f"""

        Welcome to CVision!


        Your verification code is:

        {otp}


        This code will expire in 10 minutes.


        """


        mail.send(msg)
                

        flash("Registration Successful! Please login.", "success")

        return redirect(
    url_for(
        "auth.verify_email",
        email=email
    )
)

    return render_template("auth/register.html")

@auth.route("/verify-email", methods=["GET", "POST"])
def verify_email():

    email = request.args.get("email")


    if request.method == "POST":

        otp = request.form.get("otp")


        user = User.query.filter_by(
            email=email
        ).first()


        if not user:

            flash(
                "User not found.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )



        if user.verification_code != otp:

            flash(
                "Invalid verification code.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.verify_email",
                    email=email
                )
            )



        if datetime.now() > user.verification_expiry:

            flash(
                "OTP expired. Please request a new one.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.verify_email",
                    email=email
                )
            )



        user.is_verified = True

        user.verification_code = None

        user.verification_expiry = None


        db.session.commit()



        flash(
            "Email verified successfully. You can login now.",
            "success"
        )


        return redirect(
            url_for("auth.login")
        )


    return render_template(
        "auth/verify_email.html",
        email=email
    )


# ==========================
# Login
# ==========================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")

        password = request.form.get("password")


        user = User.query.filter_by(
            email=email
        ).first()



        # User does not exist

        if not user:

            flash(
                "Account not found.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )



        # Email verification check

        if not user.is_verified:

            flash(
                "Please verify your email before logging in.",
                "warning"
            )

            return redirect(
                url_for(
                    "auth.verify_email",
                    email=email
                )
            )



        # Password check

        if not check_password_hash(
            user.password,
            password
        ):


            flash(
                "Incorrect password.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )



        # Create session

        login_user(user)



        flash(
            "Login successful!",
            "success"
        )



        # Role based redirect

        if user.role == "Applicant":

            return redirect(
                url_for("applicant.dashboard")
            )


        elif user.role == "Recruiter":

            return redirect(
                url_for("recruiter.dashboard")
            )


        elif user.role == "Admin":

            return redirect(
                url_for("admin.dashboard")
            )


        else:

            return redirect(
                url_for("public.home")
            )



    return render_template(
        "auth/login.html"
    )
# ==========================
# Logout
# ==========================

@auth.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("public.home"))

# ==========================
# Check Username (AJAX)
# ==========================

@auth.route("/check_username", methods=["POST"])
def check_username():

    username = request.form.get("username", "").strip()

    if username == "":
        return jsonify({
            "available": False,
            "message": "Username cannot be empty."
        })

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({
            "available": False,
            "message": "❌ Username already taken"
        })

    return jsonify({
        "available": True,
        "message": "✅ Username available"
    })
# ==========================
# Get Districts
# ==========================

@auth.route("/get_districts")
def get_districts():

    districts = District.query.all()

    return jsonify([
        {
            "id": district.id,
            "name": district.name
        }
        for district in districts
    ])



# ==========================
# Get Areas By District
# ==========================

@auth.route("/get_areas/<int:district_id>")
def get_areas(district_id):

    areas = Area.query.filter_by(
        district_id=district_id
    ).all()


    return jsonify([

        {
            "id": area.id,
            "name": area.name
        }

        for area in areas

    ])
# ==========================
# Check Email (AJAX)
# ==========================

@auth.route("/check_email", methods=["POST"])
def check_email():

    email = request.form.get("email", "").strip()


    if email == "":
        return jsonify({

            "available": False,

            "message": ""

        })


    existing_email = User.query.filter_by(
        email=email
    ).first()



    if existing_email:

        return jsonify({

            "available": False,

            "message": "❌ Email already registered"

        })


    return jsonify({

        "available": True,

        "message": "✅ Email available"

    })