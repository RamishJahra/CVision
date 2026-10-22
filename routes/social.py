import os
import uuid

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    url_for
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models import db
from models.user import User
from models.social import SocialPost, SocialComment, SocialReaction
from models.notification import Notification


social = Blueprint(
    "social",
    __name__,
    url_prefix="/social/api"
)

ALLOWED_ROLES = {"applicant", "recruiter"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_CONTENT_LENGTH = 5000
MAX_COMMENT_LENGTH = 2000
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def role_name(user):
    role = (user.role or "").strip().lower()

    if role == "recruiter":
        return "Recruiter"

    if role == "applicant":
        return "Applicant"

    return user.role or "Member"


def can_use_social():
    return (current_user.role or "").strip().lower() in ALLOWED_ROLES


def create_social_notification(user_id, title, message, notification_type):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False
    )

    db.session.add(notification)


def image_url(filename):
    if not filename:
        return None

    return url_for(
        "static",
        filename=f"uploads/social/{filename}"
    )


def author_data(user):
    return {
        "id": user.id,
        "username": user.username,
        "name": user.full_name or user.username,
        "initial": (
            (user.full_name or user.username or "U")[0].upper()
        ),
        "role": (user.role or "").lower(),
        "label": role_name(user),
        "profile_picture": (
            url_for(
                "static",
                filename=f"uploads/profile/{user.profile_image}"
            )
            if user.profile_image and user.profile_image != "default.png"
            else None
        )
    }


def comment_data(comment):
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "parent_comment_id": comment.parent_comment_id,
        "content": comment.content,
        "created_at": (
            comment.created_at.isoformat()
            if comment.created_at else None
        ),
        "updated_at": (
            comment.updated_at.isoformat()
            if comment.updated_at else None
        ),
        "author": author_data(comment.author),
        "can_manage": comment.user_id == current_user.id
    }


def post_data(post):
    reactions = post.reactions

    return {
        "id": post.id,
        "content": post.content,
        "image_url": image_url(post.image_filename),
        "created_at": (
            post.created_at.isoformat()
            if post.created_at else None
        ),
        "updated_at": (
            post.updated_at.isoformat()
            if post.updated_at else None
        ),
        "author": author_data(post.author),
        "can_manage": post.user_id == current_user.id,
        "like_count": sum(
            1 for reaction in reactions
            if reaction.reaction == "like"
        ),
        "dislike_count": sum(
            1 for reaction in reactions
            if reaction.reaction == "dislike"
        ),
        "my_reaction": next(
            (
                reaction.reaction
                for reaction in reactions
                if reaction.user_id == current_user.id
            ),
            None
        ),
        "comments": [
            comment_data(comment)
            for comment in post.comments
        ]
    }


def get_post_or_404(post_id):
    post = db.session.get(SocialPost, post_id)

    if post is None:
        return None, (jsonify({
            "success": False,
            "message": "Post not found."
        }), 404)

    return post, None


def get_comment_or_404(comment_id):
    comment = db.session.get(SocialComment, comment_id)

    if comment is None:
        return None, (jsonify({
            "success": False,
            "message": "Comment not found."
        }), 404)

    return comment, None


def save_post_image(file):
    if not file or not file.filename:
        return None, None

    original_name = secure_filename(file.filename)

    if "." not in original_name:
        return None, "Invalid image filename."

    extension = original_name.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return None, "Unsupported image format."

    # Enforce the limit while reading the upload.
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)

    if size > MAX_IMAGE_SIZE:
        return None, "Images must be 5 MB or smaller."

    filename = f"{uuid.uuid4().hex}.{extension}"

    upload_folder = current_app.config.get(
        "SOCIAL_UPLOAD_FOLDER",
        os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "social"
        )
    )

    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))

    return filename, None


def remove_post_image(filename):
    if not filename:
        return

    upload_folder = current_app.config.get(
        "SOCIAL_UPLOAD_FOLDER",
        os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "social"
        )
    )

    path = os.path.join(upload_folder, os.path.basename(filename))

    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        current_app.logger.exception("Could not remove social image.")


@social.before_request
def check_social_access():
    if not current_user.is_authenticated:
        return jsonify({
            "success": False,
            "message": "Please log in to continue."
        }), 401

    if not can_use_social():
        return jsonify({
            "success": False,
            "message": "Your account cannot access the social feed."
        }), 403


# ==========================================
# GET SHARED FEED
# ==========================================

@social.route("/posts", methods=["GET"])
@login_required
def get_posts():
    posts = (
        SocialPost.query
        .join(User, SocialPost.user_id == User.id)
        .filter(
            db.func.lower(User.role).in_(list(ALLOWED_ROLES)),
            User.is_banned.is_(False)
        )
        .order_by(SocialPost.created_at.desc(), SocialPost.id.desc())
        .all()
    )

    return jsonify({
        "success": True,
        "posts": [post_data(post) for post in posts]
    })


# ==========================================
# CREATE POST WITH OPTIONAL IMAGE
# ==========================================

@social.route("/posts", methods=["POST"])
@login_required
def create_post():
    content = (request.form.get("content") or "").strip()
    image = request.files.get("image")

    if len(content) > MAX_CONTENT_LENGTH:
        return jsonify({
            "success": False,
            "message": "Posts cannot exceed 5000 characters."
        }), 400

    if not content and not (image and image.filename):
        return jsonify({
            "success": False,
            "message": "Write a post or attach an image."
        }), 400

    filename, error = save_post_image(image)

    if error:
        return jsonify({
            "success": False,
            "message": error
        }), 400

    post = SocialPost(
        user_id=current_user.id,
        content=content,
        image_filename=filename
    )

    try:
        db.session.add(post)
        db.session.commit()
    except Exception:
        db.session.rollback()
        remove_post_image(filename)
        current_app.logger.exception("Could not create social post.")

        return jsonify({
            "success": False,
            "message": "Could not publish your post."
        }), 500

    return jsonify({
        "success": True,
        "message": "Post published successfully.",
        "post": post_data(post)
    }), 201


# ==========================================
# EDIT OWN POST
# ==========================================

@social.route("/posts/<int:post_id>", methods=["PATCH"])
@login_required
def update_post(post_id):
    post, error_response = get_post_or_404(post_id)

    if error_response:
        return error_response

    if post.user_id != current_user.id:
        return jsonify({
            "success": False,
            "message": "You can only edit your own posts."
        }), 403

    data = request.get_json(silent=True) or {}
    content = data.get("content")

    if not isinstance(content, str):
        return jsonify({
            "success": False,
            "message": "Post content is required."
        }), 400

    content = content.strip()

    if not content and not post.image_filename:
        return jsonify({
            "success": False,
            "message": "A post must contain text or an image."
        }), 400

    if len(content) > MAX_CONTENT_LENGTH:
        return jsonify({
            "success": False,
            "message": "Posts cannot exceed 5000 characters."
        }), 400

    post.content = content

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not update social post.")

        return jsonify({
            "success": False,
            "message": "Could not update your post."
        }), 500

    return jsonify({
        "success": True,
        "message": "Post updated successfully.",
        "post": post_data(post)
    })


# ==========================================
# DELETE OWN POST
# ==========================================

@social.route("/posts/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    post, error_response = get_post_or_404(post_id)

    if error_response:
        return error_response

    if post.user_id != current_user.id:
        return jsonify({
            "success": False,
            "message": "You can only delete your own posts."
        }), 403

    filename = post.image_filename

    try:
        db.session.delete(post)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not delete social post.")

        return jsonify({
            "success": False,
            "message": "Could not delete your post."
        }), 500

    remove_post_image(filename)

    return jsonify({
        "success": True,
        "message": "Post deleted successfully."
    })


# ==========================================
# LIKE / DISLIKE
# ==========================================

@social.route(
    "/posts/<int:post_id>/reaction",
    methods=["POST"]
)
@login_required
def react_to_post(post_id):
    post, error_response = get_post_or_404(post_id)

    if error_response:
        return error_response

    data = request.get_json(silent=True) or {}
    reaction_type = data.get("reaction")

    if reaction_type not in {"like", "dislike"}:
        return jsonify({
            "success": False,
            "message": "Reaction must be like or dislike."
        }), 400

    reaction = SocialReaction.query.filter_by(
        post_id=post.id,
        user_id=current_user.id
    ).first()

    # Notify only when a like is newly added or changed from dislike.
    was_already_liked = (
        reaction is not None
        and reaction.reaction == "like"
    )

    should_notify = (
        reaction_type == "like"
        and not was_already_liked
        and post.user_id != current_user.id
    )

    if reaction and reaction.reaction == reaction_type:
        db.session.delete(reaction)
        current_reaction = None

    elif reaction:
        reaction.reaction = reaction_type
        current_reaction = reaction_type

    else:
        reaction = SocialReaction(
            post_id=post.id,
            user_id=current_user.id,
            reaction=reaction_type
        )
        db.session.add(reaction)
        current_reaction = reaction_type

    if should_notify:
        actor_name = current_user.full_name or current_user.username

        create_social_notification(
            user_id=post.user_id,
            title="New like on your post",
            message=f"{actor_name} liked your post.",
            notification_type="social_like"
        )

    try:
        db.session.commit()

        # Query the database for current counts rather than iterating
        # over a relationship that may contain a deleted reaction.
        like_count = SocialReaction.query.filter_by(
            post_id=post.id,
            reaction="like"
        ).count()

        dislike_count = SocialReaction.query.filter_by(
            post_id=post.id,
            reaction="dislike"
        ).count()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not save reaction.")

        return jsonify({
            "success": False,
            "message": "Could not save your reaction."
        }), 500

    return jsonify({
        "success": True,
        "my_reaction": current_reaction,
        "like_count": like_count,
        "dislike_count": dislike_count
    })


# ==========================================
# ADD COMMENT OR REPLY
# ==========================================

@social.route(
    "/posts/<int:post_id>/comments",
    methods=["POST"]
)
@login_required
def create_comment(post_id):
    post, error_response = get_post_or_404(post_id)

    if error_response:
        return error_response

    data = request.get_json(silent=True) or {}
    content = data.get("content")
    parent_id = data.get("parent_comment_id")

    if not isinstance(content, str):
        return jsonify({
            "success": False,
            "message": "Comment content is required."
        }), 400

    content = content.strip()

    if not content:
        return jsonify({
            "success": False,
            "message": "Comment cannot be empty."
        }), 400

    if len(content) > MAX_COMMENT_LENGTH:
        return jsonify({
            "success": False,
            "message": "Comments cannot exceed 2000 characters."
        }), 400

    parent = None

    if parent_id is not None:
        try:
            parent_id = int(parent_id)
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Invalid parent comment."
            }), 400

        parent = db.session.get(SocialComment, parent_id)

        if parent is None or parent.post_id != post.id:
            return jsonify({
                "success": False,
                "message": "The comment being replied to was not found."
            }), 404

    comment = SocialComment(
        post_id=post.id,
        user_id=current_user.id,
        parent_comment_id=parent.id if parent else None,
        content=content
    )

    try:
        db.session.add(comment)

        actor_name = current_user.full_name or current_user.username

        # A reply notifies the parent comment's author.
        # A normal comment notifies the post owner.
        recipient_id = (
            parent.user_id if parent else post.user_id
        )

        # Never notify a user about their own action.
        if recipient_id != current_user.id:
            if parent:
                create_social_notification(
                    user_id=recipient_id,
                    title="New reply to your comment",
                    message=f"{actor_name} replied to your comment.",
                    notification_type="social_reply"
                )
            else:
                create_social_notification(
                    user_id=recipient_id,
                    title="New comment on your post",
                    message=f"{actor_name} commented on your post.",
                    notification_type="social_comment"
                )

        db.session.commit()

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Could not create comment or notification."
        )

        return jsonify({
            "success": False,
            "message": "Could not add your comment."
        }), 500

    return jsonify({
        "success": True,
        "message": "Reply added successfully." if parent else "Comment added successfully.",
        "comment": comment_data(comment)
    }), 201


# ==========================================
# EDIT OWN COMMENT
# ==========================================

@social.route(
    "/comments/<int:comment_id>",
    methods=["PATCH"]
)
@login_required
def update_comment(comment_id):
    comment, error_response = get_comment_or_404(comment_id)

    if error_response:
        return error_response

    if comment.user_id != current_user.id:
        return jsonify({
            "success": False,
            "message": "You can only edit your own comments."
        }), 403

    data = request.get_json(silent=True) or {}
    content = data.get("content")

    if not isinstance(content, str):
        return jsonify({
            "success": False,
            "message": "Comment content is required."
        }), 400

    content = content.strip()

    if not content or len(content) > MAX_COMMENT_LENGTH:
        return jsonify({
            "success": False,
            "message": "Comment must contain 1–2000 characters."
        }), 400

    comment.content = content

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not update comment.")

        return jsonify({
            "success": False,
            "message": "Could not update your comment."
        }), 500

    return jsonify({
        "success": True,
        "message": "Comment updated successfully.",
        "comment": comment_data(comment)
    })


# ==========================================
# DELETE OWN COMMENT
# ==========================================

@social.route(
    "/comments/<int:comment_id>",
    methods=["DELETE"]
)
@login_required
def delete_comment(comment_id):
    comment, error_response = get_comment_or_404(comment_id)

    if error_response:
        return error_response

    if comment.user_id != current_user.id:
        return jsonify({
            "success": False,
            "message": "You can only delete your own comments."
        }), 403

    try:
        db.session.delete(comment)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not delete comment.")

        return jsonify({
            "success": False,
            "message": "Could not delete your comment."
        }), 500

    return jsonify({
        "success": True,
        "message": "Comment deleted successfully."
    })

# ==========================================
# LOGIN-PROTECTED APPLICANT PROFILE POSTS
# ==========================================

@social.route(
    "/public/users/<int:user_id>/posts",
    methods=["GET"]
)
@login_required
def get_public_user_posts(user_id):
    user = db.session.get(User, user_id)

    if (
        user is None
        or (user.role or "").strip().lower() != "applicant"
        or user.is_banned
    ):
        return jsonify({
            "success": False,
            "message": "Profile not found."
        }), 404

    posts = (
        SocialPost.query
        .filter_by(user_id=user.id)
        .order_by(
            SocialPost.created_at.desc(),
            SocialPost.id.desc()
        )
        .all()
    )

    result = []

    for post in posts:
        comments = []

        for comment in post.comments:
            author = comment.author

            comments.append({
                "id": comment.id,
                "content": comment.content,
                "created_at": (
                    comment.created_at.isoformat()
                    if comment.created_at else None
                ),
                "author": {
                    "name": (
                        author.full_name or author.username
                    ),
                    "profile_picture": (
                        url_for(
                            "static",
                            filename=(
                                "uploads/profile/"
                                + author.profile_image
                            )
                        )
                        if (
                            author.profile_image
                            and author.profile_image != "default.png"
                        )
                        else None
                    )
                }
            })

        result.append({
            "id": post.id,
            "content": post.content or "",
            "image_url": image_url(post.image_filename),
            "created_at": (
                post.created_at.isoformat()
                if post.created_at else None
            ),
            "like_count": sum(
                1 for reaction in post.reactions
                if reaction.reaction == "like"
            ),
            "comments": comments
        })

    return jsonify({
        "success": True,
        "posts": result
    })
