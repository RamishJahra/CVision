
from models import db


class SocialPost(db.Model):
    __tablename__ = "social_posts"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    content = db.Column(db.Text, nullable=False, default="")
    image_filename = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    author = db.relationship("User", foreign_keys=[user_id])

    comments = db.relationship(
        "SocialComment",
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="SocialComment.created_at.asc()"
    )

    reactions = db.relationship(
        "SocialReaction",
        back_populates="post",
        cascade="all, delete-orphan"
    )


class SocialComment(db.Model):
    __tablename__ = "social_comments"

    id = db.Column(db.Integer, primary_key=True)

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("social_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    parent_comment_id = db.Column(
        db.Integer,
        db.ForeignKey("social_comments.id", ondelete="CASCADE"),
        nullable=True
    )

    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    post = db.relationship("SocialPost", back_populates="comments")
    author = db.relationship("User", foreign_keys=[user_id])

    replies = db.relationship(
        "SocialComment",
        backref=db.backref(
            "parent_comment",
            remote_side=[id]
        ),
        cascade="all, delete-orphan",
        single_parent=True
    )


class SocialReaction(db.Model):
    __tablename__ = "social_reactions"

    id = db.Column(db.Integer, primary_key=True)

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("social_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    reaction = db.Column(
        db.String(10),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    post = db.relationship("SocialPost", back_populates="reactions")
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint(
            "post_id",
            "user_id",
            name="uq_social_reaction_post_user"
        ),
        db.CheckConstraint(
            "reaction IN ('like', 'dislike')",
            name="ck_social_reaction_type"
        )
    )
