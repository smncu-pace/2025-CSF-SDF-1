from . import db

# -------------------------------
# 中间表
# -------------------------------

user_memory = db.Table(
    "user_memory",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("memory_id", db.Integer, db.ForeignKey("memory.id"), primary_key=True),
    db.Column("joined_at", db.DateTime, nullable=False, default=db.func.now()),
    db.Column("role", db.String(32), nullable=False, default="user"),         # “Owner" / "monitor" / "user"
    db.Column("is_favorite", db.Boolean, nullable=False, default=False),
)

picture_comment = db.Table(
    "picture_comment",
    db.Column("picture_id", db.Integer, db.ForeignKey("picture.id"), primary_key=True),
    db.Column("comment_id", db.Integer, db.ForeignKey("comment.id"), primary_key=True)
)

user_message = db.Table(
    "user_message",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("message_id", db.Integer, db.ForeignKey("message.id"), primary_key=True),
    db.Column("is_read", db.Boolean, nullable=False, default=False),
)

# -------------------------------
# 5 张主表
# -------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    avatar_url = db.Column(db.String(255))
    password = db.Column(db.String(255), nullable=False)
    signature = db.Column(db.String(255), nullable=False, default="")

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
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    location = db.Column(db.String(255))
    cover_url = db.Column(db.String(255))
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    description = db.Column(db.Text)

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
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    time = db.Column(db.DateTime, nullable=False, default=db.func.now())
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
    type = db.Column(db.String(32), nullable=False, default="null") # "comment" / "picture" / "memory"
    link_id = db.Column(db.Integer)
    time = db.Column(db.DateTime, nullable=False, default=db.func.now())
    title = db.Column(db.String(255))

    users = db.relationship(
        "User",
        secondary=user_message,
        back_populates="messages"
    )
