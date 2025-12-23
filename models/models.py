# -*- coding: utf-8 -*-
from . import db

# -------------------------------
# 中间表
# -------------------------------

user_memory = db.Table(
    "user_memory",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("memory_id", db.Integer, db.ForeignKey("memory.id"), primary_key=True)
)

picture_comment = db.Table(
    "picture_comment",
    db.Column("picture_id", db.Integer, db.ForeignKey("picture.id"), primary_key=True),
    db.Column("comment_id", db.Integer, db.ForeignKey("comment.id"), primary_key=True)
)

user_message = db.Table(
    "user_message",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("message_id", db.Integer, db.ForeignKey("message.id"), primary_key=True)
)

# -------------------------------
# 5 张主表
# -------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    memories = db.relationship(
        "Memory",
        secondary=user_memory,
        back_populates="users"
    )

    messages = db.relationship(
        "Message",
        secondary=user_message,
        back_populates="users"
    )


class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text)

    pictures = db.relationship(
        "Picture",
        back_populates="memory",
        cascade="all, delete-orphan"
    )

    users = db.relationship(
        "User",
        secondary=user_memory,
        back_populates="memories"
    )


class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(255))
    memory_id = db.Column(db.Integer, db.ForeignKey("memory.id"))

    memory = db.relationship("Memory", back_populates="pictures")
    comments = db.relationship(
        "Comment",
        secondary=picture_comment,
        back_populates="pictures"
    )


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    user = db.relationship("User")

    pictures = db.relationship(
        "Picture",
        secondary=picture_comment,
        back_populates="comments"
    )


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255))

    users = db.relationship(
        "User",
        secondary=user_message,
        back_populates="messages"
    )
