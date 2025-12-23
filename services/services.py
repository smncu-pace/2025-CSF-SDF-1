# services_user.py
from typing import Optional
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from models import User, db


def _fetch_user_by_id(user_id: int) -> Optional[User]:
    return User.query.get(user_id)


def _fetch_user_by_name(name: str) -> Optional[User]:
    return User.query.filter_by(name=name).first()


def _name_exists(name: str, exclude_user_id: int | None = None) -> bool:
    query = User.query.filter_by(name=name)
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return db.session.query(query.exists()).scalar()


def get_user(user_id: int) -> Optional[User]:
    return _fetch_user_by_id(user_id)
        

def create_user(
    name: str,
    password: str,
    avatar_url: str | None = None,
    signature: str = "",
) -> int:
    if not name or not password:
        raise ValueError("name and password are required")
    if _name_exists(name):
        raise ValueError("name already exists")

    user = User(
        name=name,
        password=password,
        avatar_url=avatar_url,
        signature=signature,
    )
    db.session.add(user)
    db.session.commit()
    return user.id


def check_password(name: str, password: str) -> bool:
    user = _fetch_user_by_name(name)
    if user is None:
        return False
    return user.password == password


def register_user(
    name: str,
    password: str,
    avatar_url: str | None = None,
    signature: str = "",
) -> int:
    return create_user(name, password, avatar_url=avatar_url, signature=signature)


def login_user(name: str, password: str) -> Optional[User]:
    user = _fetch_user_by_name(name)
    if user is None or user.password != password:
        return None

    return user


def get_user_avatar(user_id: int) -> Optional[str]:
    user = _fetch_user_by_id(user_id)
    if user is None:
        return None
    return user.avatar_url


def set_user_avatar(user_id: int, avatar_url: str | None) -> bool:
    user = _fetch_user_by_id(user_id)
    if user is None:
        return False
    user.avatar_url = avatar_url
    db.session.commit()
    return True


def update_user_profile(
    user_id: int,
    name: str | None = None,
    password: str | None = None,
    avatar_url: str | None = None,
    signature: str | None = None,
) -> Optional[User]:
    user = _fetch_user_by_id(user_id)
    if user is None:
        return None

    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("name cannot be empty")
        if _name_exists(name, exclude_user_id=user_id):
            raise ValueError("name already exists")
        user.name = name
    if password is not None:
        if not password:
            raise ValueError("password cannot be empty")
        user.password = password
    if avatar_url is not None:
        user.avatar_url = avatar_url
    if signature is not None:
        user.signature = signature

    db.session.commit()
    return user
=======
=======
>>>>>>> Stashed changes
from db import get_conn
from models import User, Message
import bcrypt

def get_user(user_id: int) -> Optional[User]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            # information
            cur.execute("""
                SELECT id, name, avatar_path
                FROM users
                WHERE id = %s
            """, (user_id,))
            row = cur.fetchone()
            if row is None:
                return None

            uid, name, avatar_path = row

            # favorites
            cur.execute("""
                SELECT memory_id
                FROM user_favorites
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (uid,))
            favorites = [r[0] for r in cur.fetchall()]

            # friends
            cur.execute("""
                SELECT friend_id
                FROM friendships
                WHERE user_id = %s
            """, (uid,))
            friends = [r[0] for r in cur.fetchall()]

            # messages
            cur.execute("""
                SELECT id, from_user, to_user, body, sent_at
                FROM messages
                WHERE to_user = %s
                ORDER BY sent_at DESC
            """, (uid,))
            messages_rows = cur.fetchall()
            messages = [
                Message(id=mid, from_user=from_u, to_user=to_u, body=body, sent_at=sent_at)
                for (mid, from_u, to_u, body, sent_at) in messages_rows
            ]

            return User(
                id=uid,
                name=name,
                avatar_path=avatar_path,
                favorites=favorites,
                friends=friends,
                messages=messages,
            )
        

def create_user(name: str, password: str, avatar_path: str | None = None) -> int:
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (name, avatar_path, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (name, avatar_path, password_hash))
            new_id = cur.fetchone()[0]
    return new_id


def check_password(name: str, password: str) -> bool:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT password_hash FROM users WHERE name = %s", (name,))
        row = cur.fetchone()
        if row is None:
            return False
        stored_hash = row[0].encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
