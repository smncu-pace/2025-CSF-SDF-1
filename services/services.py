# services_user.py
from typing import Optional
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
