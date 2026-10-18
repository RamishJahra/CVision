from flask import Blueprint, request, jsonify
from models import db
from models.feedback import Feedback

feedback = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback.route("/submit", methods=["POST"])
def submit_feedback():
    data = request.get_json(silent=True) or {}

    rating = data.get("rating")
    message = (data.get("message") or "").strip()
    is_anonymous = data.get("is_anonymous", True)
    name = (data.get("name") or "").strip()

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Please select a valid rating."
        }), 400

    if rating < 1 or rating > 5:
        return jsonify({
            "success": False,
            "message": "Rating must be between 1 and 5."
        }), 400

    if not message:
        return jsonify({
            "success": False,
            "message": "Please write your feedback."
        }), 400

    if len(message) > 2000:
        return jsonify({
            "success": False,
            "message": "Feedback must be 2000 characters or fewer."
        }), 400

    is_anonymous = str(is_anonymous).lower() in ("true", "1", "yes")

    if not is_anonymous and not name:
        return jsonify({
            "success": False,
            "message": "Please enter your name or select anonymous feedback."
        }), 400

    try:
        item = Feedback(
            name=None if is_anonymous else name[:100],
            rating=rating,
            message=message,
            is_anonymous=is_anonymous
        )

        db.session.add(item)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Thank you! Your feedback has been submitted."
        }), 201

    except Exception:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Unable to submit feedback right now."
        }), 500