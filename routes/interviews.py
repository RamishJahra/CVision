from datetime import datetime
from urllib.parse import urlparse

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    jsonify,
)
from flask_login import login_required, current_user
from flask_mail import Message

from models import db, mail
from models.application import Application
from models.interview import Interview
from models.notification import Notification
from models.job import Job


interviews = Blueprint("interviews", __name__, url_prefix="/interviews")

INTERVIEW_TYPES = {"Online", "In-person", "Phone"}
INTERVIEW_STATUSES = {"Scheduled", "Completed", "Cancelled", "No-show"}


def _recruiter_application(application_id):
    """Return an application only if its job belongs to the signed-in recruiter."""
    return (
        Application.query
        .join(Job, Application.job_id == Job.id)
        .filter(
            Application.id == application_id,
            Job.recruiter_id == current_user.id
        )
        .first()
    )


def _recruiter_interview(interview_id):
    """Return an interview only if the signed-in recruiter owns its job."""
    return (
        Interview.query
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Interview.id == interview_id,
            Job.recruiter_id == current_user.id,
            Interview.recruiter_id == current_user.id
        )
        .first()
    )


def _valid_http_url(value):
    if not value:
        return True

    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _parse_form():
    """Validate and parse the interview form; returns (values, error)."""
    raw_date = (request.form.get("scheduled_at") or "").strip()
    interview_type = (
        request.form.get("interview_type") or "Online"
    ).strip()
    meeting_link = (request.form.get("meeting_link") or "").strip()
    location = (request.form.get("location") or "").strip()
    instructions = (request.form.get("instructions") or "").strip()

    if not raw_date:
        return None, "Please select the interview date and time."

    try:
        scheduled_at = datetime.strptime(
            raw_date, "%Y-%m-%dT%H:%M"
        )
    except ValueError:
        return None, "The interview date or time is invalid."

    if interview_type not in INTERVIEW_TYPES:
        return None, "Please select a valid interview type."

    if interview_type == "Online":
        if not meeting_link:
            return None, "A meeting link is required for an online interview."

        if not _valid_http_url(meeting_link):
            return None, (
                "The meeting link must be a valid "
                "http:// or https:// URL."
            )

    if interview_type == "In-person" and not location:
        return None, "A location is required for an in-person interview."

    return {
        "scheduled_at": scheduled_at,
        "interview_type": interview_type,
        "meeting_link": meeting_link or None,
        "location": location or None,
        "instructions": instructions or None,
    }, None


def _create_in_app_notification(
    user_id, title, message, application_id
):
    db.session.add(Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type="interview",
        application_id=application_id,
        is_read=False
    ))


def _send_interview_email(interview, subject, message_text):
    """Send email to the candidate and recruiter."""
    application = interview.application
    recipients = []

    if application and application.applicant:
        email = application.applicant.email
        if email:
            recipients.append(email)

    if interview.recruiter and interview.recruiter.email:
        recipients.append(interview.recruiter.email)

    # Remove duplicate email addresses.
    recipients = list(dict.fromkeys(recipients))

    if not recipients:
        return False

    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=message_text
        )
        mail.send(msg)
        return True

    except Exception:
        current_app.logger.exception(
            "Interview email could not be sent."
        )
        return False


def _interview_message(interview, action):
    application = interview.application

    job_title = (
        application.job.job_title
        if application and application.job
        else "the job you applied for"
    )

    date_text = interview.scheduled_at.strftime(
        "%d %b %Y at %I:%M %p"
    )

    details = [
        f"Interview update: {action}",
        f"Job: {job_title}",
        f"Date and time: {date_text}",
        f"Type: {interview.interview_type}",
        f"Status: {interview.status}",
    ]

    if interview.meeting_link:
        details.append(f"Meeting link: {interview.meeting_link}")

    if interview.location:
        details.append(f"Location: {interview.location}")

    if interview.instructions:
        details.append(f"Instructions: {interview.instructions}")

    return "\n".join(details)


def _notify_parties(interview, action):
    application = interview.application

    if not application:
        return False

    job_title = (
        application.job.job_title
        if application.job
        else "your job application"
    )

    date_text = interview.scheduled_at.strftime(
        "%d %b %Y at %I:%M %p"
    )

    title = f"Interview {action}"
    message = (
        f"{action} for {job_title}. "
        f"Date and time: {date_text}. "
        f"Status: {interview.status}."
    )

    _create_in_app_notification(
        application.applicant_id,
        title,
        message,
        application.id
    )

    if interview.recruiter_id != application.applicant_id:
        _create_in_app_notification(
            interview.recruiter_id,
            title,
            message,
            application.id
        )

    return _send_interview_email(
        interview,
        f"CVision Interview {action}",
        _interview_message(interview, action)
    )


def _serialize_applicant_interview(interview):
    """Convert an interview into JSON-safe data for AJAX updates."""
    application = interview.application
    job = application.job if application else None
    recruiter = interview.recruiter

    return {
        "id": interview.id,
        "interview_type": interview.interview_type,
        "status": interview.status,
        "scheduled_date": (
            interview.scheduled_at.strftime("%d %b %Y")
            if interview.scheduled_at else ""
        ),
        "scheduled_time": (
            interview.scheduled_at.strftime("%I:%M %p")
            if interview.scheduled_at else ""
        ),
        "job_title": (
            getattr(job, "job_title", None) or "Job interview"
        ),
        "recruiter_name": (
            getattr(recruiter, "full_name", None)
            or "CVision recruiter"
        ),
        "meeting_link": interview.meeting_link or "",
        "location": interview.location or "",
        "instructions": interview.instructions or "",
    }


@interviews.route("/recruiter", methods=["GET"])
@login_required
def recruiter_list():
    if current_user.role != "Recruiter":
        flash(
            "Only recruiters can access interview management.",
            "warning"
        )
        return redirect(url_for("dashboard.home"))

    interview_rows = (
        Interview.query
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Job.recruiter_id == current_user.id,
            Interview.recruiter_id == current_user.id
        )
        .order_by(Interview.scheduled_at.desc())
        .all()
    )

    applications = (
        Application.query
        .join(Job, Application.job_id == Job.id)
        .filter(Job.recruiter_id == current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    return render_template(
        "interviews/recruiter.html",
        interviews=interview_rows,
        applications=applications,
        interview_types=sorted(INTERVIEW_TYPES),
        interview_statuses=sorted(INTERVIEW_STATUSES)
    )


@interviews.route("/schedule/<int:application_id>", methods=["POST"])
@login_required
def schedule(application_id):
    if current_user.role != "Recruiter":
        return {"error": "Unauthorized"}, 403

    application = _recruiter_application(application_id)

    if not application:
        flash(
            "Application not found or you do not manage this job.",
            "danger"
        )
        return redirect(url_for("interviews.recruiter_list"))

    values, error = _parse_form()

    if error:
        flash(error, "danger")
        return redirect(url_for("interviews.recruiter_list"))

    interview = Interview(
        application_id=application.id,
        recruiter_id=current_user.id,
        status="Scheduled",
        **values
    )

    db.session.add(interview)

    try:
        db.session.flush()
        email_sent = _notify_parties(interview, "Scheduled")
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not schedule interview.")

        flash(
            "Could not schedule the interview. Please try again.",
            "danger"
        )
        return redirect(url_for("interviews.recruiter_list"))

    if email_sent:
        flash(
            "Interview scheduled. In-app and email notifications were sent.",
            "success"
        )
    else:
        flash(
            "Interview scheduled and in-app notifications created, "
            "but email could not be sent. Check your mail configuration.",
            "warning"
        )

    return redirect(url_for("interviews.recruiter_list"))


@interviews.route("/<int:interview_id>/update", methods=["POST"])
@login_required
def update(interview_id):
    if current_user.role != "Recruiter":
        return {"error": "Unauthorized"}, 403

    interview = _recruiter_interview(interview_id)

    if not interview:
        flash(
            "Interview not found or you do not manage this job.",
            "danger"
        )
        return redirect(url_for("interviews.recruiter_list"))

    values, error = _parse_form()

    if error:
        flash(error, "danger")
        return redirect(url_for("interviews.recruiter_list"))

    for key, value in values.items():
        setattr(interview, key, value)

    # Preserve the existing behavior of reactivating a cancelled interview
    # when it is rescheduled.
    if interview.status == "Cancelled":
        interview.status = "Scheduled"

    try:
        db.session.flush()
        email_sent = _notify_parties(interview, "Rescheduled")
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not update interview.")

        flash(
            "Could not update the interview. Please try again.",
            "danger"
        )
        return redirect(url_for("interviews.recruiter_list"))

    if email_sent:
        flash("Interview updated and notifications sent.", "success")
    else:
        flash(
            "Interview updated, but email could not be sent. "
            "Check your mail configuration.",
            "warning"
        )

    return redirect(url_for("interviews.recruiter_list"))


@interviews.route("/<int:interview_id>/status", methods=["POST"])
@login_required
def update_status(interview_id):
    if current_user.role != "Recruiter":
        return {"error": "Unauthorized"}, 403

    interview = _recruiter_interview(interview_id)

    if not interview:
        flash(
            "Interview not found or you do not manage this job.",
            "danger"
        )
        return redirect(url_for("interviews.recruiter_list"))

    new_status = (request.form.get("status") or "").strip()

    if new_status not in INTERVIEW_STATUSES:
        flash("Invalid interview status.", "danger")
        return redirect(url_for("interviews.recruiter_list"))

    if interview.status == new_status:
        flash("The interview already has that status.", "info")
        return redirect(url_for("interviews.recruiter_list"))

    interview.status = new_status

    try:
        db.session.flush()
        email_sent = _notify_parties(interview, new_status)
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Could not update interview status."
        )

        flash(
            "Could not update the interview status. Please try again.",
            "danger"
        )
        return redirect(url_for("interviews.recruiter_list"))

    if email_sent:
        flash(
            f"Interview status changed to {new_status}. Notifications sent.",
            "success"
        )
    else:
        flash(
            f"Interview status changed to {new_status}, "
            "but email could not be sent.",
            "warning"
        )

    return redirect(url_for("interviews.recruiter_list"))


@interviews.route("/applicant", methods=["GET"])
@login_required
def applicant_list():
    if current_user.role != "Applicant":
        flash(
            "Only applicants can access their interview schedule.",
            "warning"
        )
        return redirect(url_for("dashboard.home"))

    interview_rows = (
        Interview.query
        .join(Application, Interview.application_id == Application.id)
        .filter(Application.applicant_id == current_user.id)
        .order_by(Interview.scheduled_at.desc())
        .all()
    )

    return render_template(
        "interviews/applicant.html",
        interviews=interview_rows
    )


@interviews.route("/applicant/updates", methods=["GET"])
@login_required
def applicant_updates():
    """AJAX endpoint polled by the applicant interview page."""
    if current_user.role != "Applicant":
        return jsonify({
            "error": "Only applicants can access these interviews."
        }), 403

    interview_rows = (
        Interview.query
        .join(Application, Interview.application_id == Application.id)
        .filter(Application.applicant_id == current_user.id)
        .order_by(Interview.scheduled_at.desc())
        .all()
    )

    response = jsonify({
        "interviews": [
            _serialize_applicant_interview(interview)
            for interview in interview_rows
        ]
    })

    # Prevent browsers or intermediaries from caching interview updates.
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"

    return response, 200

@interviews.route("/recruiter/updates", methods=["GET"])
@login_required
def recruiter_updates():
    """Return the signed-in recruiter's interviews for AJAX polling."""
    if current_user.role != "Recruiter":
        return jsonify({
            "error": "Only recruiters can access interview management."
        }), 403

    interview_rows = (
        Interview.query
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Job.recruiter_id == current_user.id,
            Interview.recruiter_id == current_user.id
        )
        .order_by(Interview.scheduled_at.desc())
        .all()
    )

    results = []

    for interview in interview_rows:
        application = interview.application
        applicant = application.applicant if application else None
        job = application.job if application else None

        results.append({
            "id": interview.id,
            "application_id": interview.application_id,
            "applicant_name": (
                getattr(applicant, "full_name", None) or "Applicant"
            ),
            "job_title": (
                getattr(job, "job_title", None) or "Job interview"
            ),
            "scheduled_date": (
                interview.scheduled_at.strftime("%d %b %Y")
                if interview.scheduled_at else ""
            ),
            "scheduled_time": (
                interview.scheduled_at.strftime("%I:%M %p")
                if interview.scheduled_at else ""
            ),
            "scheduled_at_input": (
                interview.scheduled_at.strftime("%Y-%m-%dT%H:%M")
                if interview.scheduled_at else ""
            ),
            "interview_type": interview.interview_type,
            "status": interview.status,
            "meeting_link": interview.meeting_link or "",
            "location": interview.location or "",
            "instructions": interview.instructions or "",
        })

    response = jsonify({"interviews": results})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"

    return response, 200
