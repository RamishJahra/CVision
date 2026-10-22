from flask import Blueprint, render_template

public = Blueprint("public", __name__)


@public.route("/")
def home():
    return render_template("public/home.html")

@public.route("/career-resources")
def career_resources():
    return render_template("career_resources.html")