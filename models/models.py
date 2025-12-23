from . import db

# -------------------------------
# 关联表（带额外字段）
# -------------------------------

class UserMemory(db.Model):
    __tablename__ = "user_memory"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    memory_id = db.Column(db.Integer, db.ForeignKey("memories.id"), primary_key=True)
    joined_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    role = db.Column(db.String(32), nullable=False, default="user")
    is_favorite = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="user_memories")
    memory = db.relationship("Memory", back_populates="user_memories")


class UserMessage(db.Model):
    __tablename__ = "user_message"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), primary_key=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="user_messages")
    message = db.relationship("Message", back_populates="user_messages")


comment_picture_links = db.Table(
    "comment_picture_links",
    db.Column("comment_id", db.Integer, db.ForeignKey("comments.id"), primary_key=True),
    db.Column("picture_id", db.Integer, db.ForeignKey("pictures.id"), primary_key=True),
)

# -------------------------------
# 主表
# -------------------------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    avatar_url = db.Column(db.String(255))
    password = db.Column(db.String(255), nullable=False)
    signature = db.Column(db.String(255), nullable=False, default="")

    user_memories = db.relationship(
        "UserMemory",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    memories = db.relationship(
        "Memory",
        secondary="user_memory",
        viewonly=True,
    )

    user_messages = db.relationship(
        "UserMessage",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    messages = db.relationship(
        "Message",
        secondary="user_message",
        viewonly=True,
    )


class Memory(db.Model):
    __tablename__ = "memories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(255))
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    user_memories = db.relationship(
        "UserMemory",
        back_populates="memory",
        cascade="all, delete-orphan",
    )

    pictures = db.relationship(
        "Picture",
        back_populates="memory",
        cascade="all, delete-orphan",
    )

    comments = db.relationship(
        "Comment",
        back_populates="memory",
        cascade="all, delete-orphan",
    )


class Picture(db.Model):
    __tablename__ = "pictures"

    id = db.Column(db.Integer, primary_key=True)
    pict = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    memory_id = db.Column(db.Integer, db.ForeignKey("memories.id"), nullable=False)

    memory = db.relationship("Memory", back_populates="pictures")
    comments = db.relationship(
        "Comment",
        secondary=comment_picture_links,
        back_populates="pictures",
    )


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    memory_id = db.Column(db.Integer, db.ForeignKey("memories.id"), nullable=False)
    commenter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    memory = db.relationship("Memory", back_populates="comments")
    commenter = db.relationship("User", foreign_keys=[commenter_id])
    target = db.relationship("User", foreign_keys=[target_id])

    pictures = db.relationship(
        "Picture",
        secondary=comment_picture_links,
        back_populates="comments",
    )


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    system = db.Column(db.Boolean, nullable=False, default=False)
    memory_id = db.Column(db.Integer, db.ForeignKey("memories.id"))
    picture_id = db.Column(db.Integer, db.ForeignKey("pictures.id"))
    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"))

    sender = db.relationship("User", foreign_keys=[sender_id])
    user_messages = db.relationship(
        "UserMessage",
        back_populates="message",
        cascade="all, delete-orphan",
    )
    users = db.relationship(
        "User",
        secondary="user_message",
        viewonly=True,
    )


class DebugPing(db.Model):
    __tablename__ = "debug_ping"

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
