# -*- coding: utf-8 -*-
# routes/memory_routes.py

"""
回忆库所有业务路由（PostgreSQL 版本）

接口涵盖：
- 验证登录
- 个人信息
- 系统消息 / 用户消息 / 所有消息
- 消息标记已读
- 回忆预览
- 回忆列表（全部 / 限定人员 / 包含人员）
- 新建回忆
- 往年今日
- 收藏增删查
- 评论增查
- Debug: pg-test / init-demo-data
"""

from __future__ import annotations
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from flask import Blueprint, request, jsonify
from sqlalchemy import or_

from models import (
    db,
    User,
    Memory,
    Picture,
    Comment,
    Message,
    UserMemory,
    UserMessage,
    DebugPing,
)
=======
import base64
import mimetypes
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

import models.db
from flask import Blueprint, request, jsonify, current_app
>>>>>>> Stashed changes
=======
import base64
import mimetypes
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

import models.db
from flask import Blueprint, request, jsonify, current_app
>>>>>>> Stashed changes
from utils.helpers import paginate_sorted


memory_bp = Blueprint("memory", __name__)


# ------------ 小工具函数 ------------

def _user_exists(user_id: int) -> bool:
    return User.query.get(user_id) is not None


def _memory_exists(memory_id: int) -> bool:
    return Memory.query.get(memory_id) is not None


def _fetch_visible_user_ids(memory_id: int) -> List[int]:
    rows = (
        db.session.query(UserMemory.user_id)
        .filter(UserMemory.memory_id == memory_id)
        .all()
    )
    return [r[0] for r in rows]


<<<<<<< Updated upstream
def _fetch_cover_picture(memory_id: int) -> str | None:
    pic = (
        Picture.query.filter_by(memory_id=memory_id)
        .order_by(Picture.id.asc())
        .first()
    )
    return pic.pict if pic else None
=======
def _fetch_avatar_base64(user_id: int, conn) -> str | None:
    cur = conn.cursor()
    cur.execute(
        "SELECT image_base64 FROM avatars WHERE user_id = %s",
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    return row["image_base64"] if row else None


def _load_avatar_file_base64(filename: str | None) -> str | None:
    """Read an avatar file under app root and return base64 string; returns None on failure."""
    if not filename:
        return None
    abs_path = filename
    if not os.path.isabs(filename):
        abs_path = os.path.join(current_app.root_path, filename)

    try:
        with open(abs_path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        return None
    except Exception:
        return None

    return base64.b64encode(raw).decode("ascii")


def _to_base64_or_original(pict_path: str | None) -> str | None:
    """
    将图片路径转换为 base64 data URI；读取失败时保留原始路径，避免前端直接崩溃。
    """
    if not pict_path:
        return None

    stripped = pict_path.strip()
    # 已经是 data URI 或纯 base64 时直接返回
    if stripped.startswith("data:"):
        return stripped

    try:
        abs_path = pict_path
        if not os.path.isabs(pict_path):
            abs_path = os.path.join(current_app.root_path, pict_path.lstrip("/"))

        with open(abs_path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        return pict_path
    except Exception:
        return pict_path

    mime, _ = mimetypes.guess_type(abs_path)
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}" if mime else b64


def _fetch_avatar_base64(user_id: int, conn) -> str | None:
    cur = conn.cursor()
    cur.execute(
        "SELECT image_base64 FROM avatars WHERE user_id = %s",
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    return row["image_base64"] if row else None


def _load_avatar_file_base64(filename: str | None) -> str | None:
    """Read an avatar file under app root and return base64 string; returns None on failure."""
    if not filename:
        return None
    abs_path = filename
    if not os.path.isabs(filename):
        abs_path = os.path.join(current_app.root_path, filename)

    try:
        with open(abs_path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        return None
    except Exception:
        return None

    return base64.b64encode(raw).decode("ascii")


def _to_base64_or_original(pict_path: str | None) -> str | None:
    """
    将图片路径转换为 base64 data URI；读取失败时保留原始路径，避免前端直接崩溃。
    """
    if not pict_path:
        return None

    stripped = pict_path.strip()
    # 已经是 data URI 或纯 base64 时直接返回
    if stripped.startswith("data:"):
        return stripped

    try:
        abs_path = pict_path
        if not os.path.isabs(pict_path):
            abs_path = os.path.join(current_app.root_path, pict_path.lstrip("/"))

        with open(abs_path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        return pict_path
    except Exception:
        return pict_path

    mime, _ = mimetypes.guess_type(abs_path)
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}" if mime else b64


def _fetch_cover_picture(memory_id: int, conn) -> str | None:
    cur = conn.cursor()
    cur.execute(
        "SELECT pict FROM pictures WHERE memory_id = %s ORDER BY id ASC LIMIT 1",
        (memory_id,),
    )
    row = cur.fetchone()
    cur.close()
    return _to_base64_or_original(row["pict"]) if row else None
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes


def _serialize_message(message: Message, receiver_id: int, is_read: bool) -> Dict[str, Any]:
    links: Dict[str, int] = {}
    if message.memory_id is not None:
        links["memory_id"] = message.memory_id
    if message.picture_id is not None:
        links["picture_id"] = message.picture_id
    if message.comment_id is not None:
        links["comment_id"] = message.comment_id

    created = message.created_at
    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "receiver_id": receiver_id,
        "text": message.text,
        "time": created.isoformat() if isinstance(created, datetime) else None,
        "read": is_read,
        "system": message.system,
        "links": links,
    }


def _serialize_memory(memory: Memory) -> Dict[str, Any]:
    mem_id = memory.id
    visible_user_ids = _fetch_visible_user_ids(mem_id)
    cover = _fetch_cover_picture(mem_id)
    created = memory.created_at
    created_date = created.date() if isinstance(created, datetime) else None

    preview = {
        "memory_id": mem_id,
        "title": memory.title,
        "cover_picture": cover,
        "date": created_date.isoformat() if created_date else None,
        "location": memory.location,
    }

    return {
        "memory_id": mem_id,
        "title": memory.title,
        "visible_user_ids": visible_user_ids,
        "location": memory.location,
        "creator_id": memory.creator_id,
        "created_at": created.isoformat() if isinstance(created, datetime) else None,
        "preview": preview,
    }


<<<<<<< Updated upstream
<<<<<<< Updated upstream
def _serialize_comment(comment: Comment) -> Dict[str, Any]:
    comment_id = comment.id
    pics = [p.id for p in comment.pictures]
    created = comment.created_at
=======
=======
>>>>>>> Stashed changes
def _serialize_picture(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "picture_id": row["id"],
        "memory_id": row["memory_id"],
        "title": row.get("title"),
        "image_base64": _to_base64_or_original(row.get("pict")),
    }


def _serialize_comment(row: Dict[str, Any], conn) -> Dict[str, Any]:
    comment_id = row["id"]
    # 取关联的图片
    cur = conn.cursor()
    cur.execute(
        "SELECT picture_id FROM comment_picture_links WHERE comment_id = %s",
        (comment_id,),
    )
    pics = [r["picture_id"] for r in cur.fetchall()]
    cur.close()

    created = row.get("created_at")
>>>>>>> Stashed changes
    return {
        "comment_id": comment_id,
        "commenter_id": comment.commenter_id,
        "target_id": comment.target_id,
        "comment": comment.content,
        "links": pics,
        "sub_comments": [],      # 先留空，后面你要的话可以做子评论表
        "emoji_comments": {},    # 同理
        "created_at": created.isoformat() if isinstance(created, datetime) else None,
    }


def _serialize_user(user: User) -> Dict[str, Any]:
    return {
<<<<<<< Updated upstream
        "user_id": user.id,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "signature": user.signature,
=======
        "user_id": row["id"],
        "name": row.get("name"),
        "avatar": row.get("avatar_base64"),
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    }


# ========== 登录 & 用户信息 ==========

@memory_bp.route("/auth/login", methods=["POST"])
def validate_login():
    """
    请求：验证登录；推送：用户名，密码
    body: {"username": "...", "password": "..."}
    """
    data = request.get_json() or {}
    name = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not name or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

<<<<<<< Updated upstream
    user = User.query.filter_by(name=name).first()
    if not user or user.password != password:
=======
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT u.id, u.name, u.password, a.image_base64 AS avatar_base64
                FROM users u
                LEFT JOIN avatars a ON a.user_id = u.id
                WHERE u.name = %s
                """,
                (name,),
            )
        except Exception:
            # 兼容老库：没有 avatars 表时退回 users.avatar
            cur.execute(
                """
                SELECT id, name, password, avatar AS avatar_base64
                FROM users
                WHERE name = %s
                """,
                (name,),
            )
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    if not row or row["password"] != password:
>>>>>>> Stashed changes
        return jsonify({"ok": False, "error": "用户名或密码错误"}), 401

    return jsonify({
        "ok": True,
        "user": {
<<<<<<< Updated upstream
            "user_id": user.id,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "signature": user.signature,
=======
            "user_id": row["id"],
            "name": row["name"],
            "avatar": row.get("avatar_base64"),
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        }
    })


@memory_bp.route("/user/<int:user_id>/profile", methods=["GET"])
def get_user_profile(user_id: int):
    """
    请求：个人信息；返回：用户名，用户头像。（前端可缓存）
    """
<<<<<<< Updated upstream
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    return jsonify({
        "user_id": user.id,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "signature": user.signature,
=======
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT u.id, u.name, a.image_base64 AS avatar_base64
                FROM users u
                LEFT JOIN avatars a ON a.user_id = u.id
                WHERE u.id = %s
                """,
                (user_id,),
            )
        except Exception:
            # 兼容老库：没有 avatars 表时退回 users.avatar
            cur.execute(
                """
                SELECT id, name, avatar AS avatar_base64
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "用户不存在"}), 404

    return jsonify({
        "user_id": row["id"],
        "name": row["name"],
        "avatar": row.get("avatar_base64"),
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    })


# ========== 消息相关：系统 / 用户 / 全部 / 标记已读 ==========

def _fetch_messages_for_user(user_id: int, system_only: bool | None):
    query = (
        db.session.query(UserMessage, Message)
        .join(Message, UserMessage.message_id == Message.id)
        .filter(UserMessage.user_id == user_id)
    )
    if system_only is True:
        query = query.filter(Message.system.is_(True))
    elif system_only is False:
        query = query.filter(Message.system.is_(False))

    query = query.order_by(Message.created_at.desc())
    return query.all()


@memory_bp.route("/user/<int:user_id>/messages/system", methods=["GET"])
def get_system_messages(user_id: int):
    """请求：系统消息；返回：来自系统的消息"""
    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    rows = _fetch_messages_for_user(user_id, system_only=True)
    return jsonify([_serialize_message(msg, user_id, um.is_read) for um, msg in rows])


@memory_bp.route("/user/<int:user_id>/messages/user", methods=["GET"])
def get_user_messages(user_id: int):
    """请求：用户消息；返回：来自其他用户的消息"""
    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    rows = _fetch_messages_for_user(user_id, system_only=False)
    return jsonify([_serialize_message(msg, user_id, um.is_read) for um, msg in rows])


@memory_bp.route("/user/<int:user_id>/messages", methods=["GET"])
def get_all_messages(user_id: int):
    """
    请求：获取消息；
    返回：消息id，发送者id，消息内容，消息时间，消息已读状态。
    """
    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    rows = _fetch_messages_for_user(user_id, system_only=None)
    return jsonify([_serialize_message(msg, user_id, um.is_read) for um, msg in rows])


@memory_bp.route("/user/<int:user_id>/messages/<int:msg_id>/read", methods=["POST"])
def mark_message_read(user_id: int, msg_id: int):
    """
    请求：标记已读；推送：将指定id的消息标为已读。
    """
    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    link = UserMessage.query.filter_by(user_id=user_id, message_id=msg_id).first()
    if not link:
        return jsonify({"error": "消息不存在或不属于该用户"}), 404

    link.is_read = True
    db.session.commit()
    return jsonify({"ok": True, "message_id": msg_id})


# ========== 回忆：预览 / 获取 / 限定人员 / 包含人员 / 新建 / 往年今日 ==========

@memory_bp.route("/memory/<int:memory_id>/preview", methods=["GET"])
def preview_memory(memory_id: int):
    """
    请求：预览回忆；
    返回：标题 + 封面图 + 日期 + 地点
    """
    memory = Memory.query.get(memory_id)
    if not memory:
        return jsonify({"error": "回忆不存在"}), 404

    return jsonify(_serialize_memory(memory))


@memory_bp.route("/memory/<int:memory_id>/pictures", methods=["GET"])
def get_memory_pictures(memory_id: int):
    """
    请求：获取回忆的所有图片（base64）。
    返回：包含 image_base64 的图片列表。
    """
    conn = get_db_connection()
    try:
        if not _memory_exists(memory_id, conn):
            return jsonify({"error": "回忆不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, memory_id, pict, title
            FROM pictures
            WHERE memory_id = %s
            ORDER BY id ASC
            """,
            (memory_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return jsonify([_serialize_picture(r) for r in rows])
    finally:
        conn.close()


@memory_bp.route("/pictures/<int:picture_id>", methods=["GET"])
def get_picture_by_id(picture_id: int):
    """
    请求：通过图片 id 获取图片（base64）。
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, memory_id, pict, title FROM pictures WHERE id = %s",
            (picture_id,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return jsonify({"error": "图片不存在"}), 404

        return jsonify(_serialize_picture(row))
    finally:
        conn.close()


@memory_bp.route("/memory/<int:memory_id>/pictures", methods=["GET"])
def get_memory_pictures(memory_id: int):
    """
    请求：获取回忆的所有图片（base64）。
    返回：包含 image_base64 的图片列表。
    """
    conn = get_db_connection()
    try:
        if not _memory_exists(memory_id, conn):
            return jsonify({"error": "回忆不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, memory_id, pict, title
            FROM pictures
            WHERE memory_id = %s
            ORDER BY id ASC
            """,
            (memory_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return jsonify([_serialize_picture(r) for r in rows])
    finally:
        conn.close()


@memory_bp.route("/pictures/<int:picture_id>", methods=["GET"])
def get_picture_by_id(picture_id: int):
    """
    请求：通过图片 id 获取图片（base64）。
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, memory_id, pict, title FROM pictures WHERE id = %s",
            (picture_id,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return jsonify({"error": "图片不存在"}), 404

        return jsonify(_serialize_picture(row))
    finally:
        conn.close()


@memory_bp.route("/user/<int:user_id>/memories", methods=["GET"])
def get_memories(user_id: int):
    """
    请求：获取回忆；
    返回：按时间排序，最近的第 [l,r] 条回忆（1-based）
    """
    l = int(request.args.get("l", 1))
    r = int(request.args.get("r", 10))
    if r < l:
        return jsonify([])

    limit = r - l + 1
    offset = l - 1

    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    memories = (
        Memory.query.outerjoin(UserMemory)
        .filter(or_(Memory.creator_id == user_id, UserMemory.user_id == user_id))
        .distinct()
        .order_by(Memory.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return jsonify([_serialize_memory(m) for m in memories])


@memory_bp.route("/user/<int:user_id>/memories/only-users", methods=["GET"])
def get_memories_only_users(user_id: int):
    """
    请求：限定人员；
    返回：按时间排序，最近的第 [l,r] 条回忆，
         且可见人员集合 == 给定 user_ids 集合。
    """
    l = int(request.args.get("l", 1))
    r = int(request.args.get("r", 10))
    ids_str = request.args.get("user_ids", "")
    if not ids_str:
        return jsonify({"error": "缺少 user_ids 参数"}), 400

    target_ids = sorted({int(x) for x in ids_str.split(",") if x.strip()})

    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    rows = (
        Memory.query.outerjoin(UserMemory)
        .filter(or_(Memory.creator_id == user_id, UserMemory.user_id == user_id))
        .distinct()
        .all()
    )

    filtered = []
    for memory in rows:
        vis_ids = sorted(set(_fetch_visible_user_ids(memory.id)))
        if vis_ids == target_ids:
            filtered.append(_serialize_memory(memory))

    filtered.sort(key=lambda m: m["created_at"] or "", reverse=True)
    page = paginate_sorted(filtered, l, r)
    return jsonify(page)


@memory_bp.route("/user/<int:user_id>/memories/include-users", methods=["GET"])
def get_memories_include_users(user_id: int):
    """
    请求：包含人员；
    返回：按时间排序，最近的第 [l,r] 条回忆，
         可见人员集合 ⊃ target_ids（真超集：不能只包含这些人）。
    """
    l = int(request.args.get("l", 1))
    r = int(request.args.get("r", 10))
    ids_str = request.args.get("user_ids", "")
    if not ids_str:
        return jsonify({"error": "缺少 user_ids 参数"}), 400

    target_set = {int(x) for x in ids_str.split(",") if x.strip()}

    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    rows = (
        Memory.query.outerjoin(UserMemory)
        .filter(or_(Memory.creator_id == user_id, UserMemory.user_id == user_id))
        .distinct()
        .all()
    )

    filtered = []
    for memory in rows:
        vis_set = set(_fetch_visible_user_ids(memory.id))
        if target_set.issubset(vis_set) and vis_set != target_set:
            filtered.append(_serialize_memory(memory))

    filtered.sort(key=lambda m: m["created_at"] or "", reverse=True)
    page = paginate_sorted(filtered, l, r)
    return jsonify(page)


@memory_bp.route("/user/<int:user_id>/memories", methods=["POST"])
def create_memory(user_id: int):
    """
    请求：新建回忆；
    推送：回忆标题，图片集合，创建时间，地点。
    body 示例：
    {
        "title": "周末爬山",
        "visible_user_ids": [1,2,3],
        "location": "富士山",
        "pictures": ["/pics/a.png", "/pics/b.png"],
        "created_at": "2025-11-15T10:00:00"   # 可选
    }
    """
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    visible_ids = data.get("visible_user_ids") or []
    location = data.get("location") or ""
    pictures = data.get("pictures") or []
    created_at_str = data.get("created_at")

    if not title:
        return jsonify({"error": "标题不能为空"}), 400
    if not pictures:
        return jsonify({"error": "至少要有一张图片"}), 400

    # created_at 可选
    created_at = None
    if created_at_str:
        try:
            created_at = datetime.fromisoformat(created_at_str)
        except Exception:
            pass

    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    try:
        memory = Memory(
            title=title,
            location=location,
            creator_id=user_id,
            created_at=created_at or datetime.now(),
        )
        db.session.add(memory)
        db.session.flush()

        if user_id not in visible_ids:
            visible_ids.append(user_id)

        for uid in set(visible_ids):
            db.session.add(
                UserMemory(user_id=uid, memory_id=memory.id)
            )

        for p in pictures:
            db.session.add(
                Picture(memory_id=memory.id, pict=p, title=title)
            )

        db.session.commit()
        return jsonify(_serialize_memory(memory)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"创建回忆失败: {str(e)}"}), 500


@memory_bp.route("/user/<int:user_id>/memories/on-this-day", methods=["GET"])
def memories_on_this_day(user_id: int):
    """
    请求：往年今日；
    返回：所有的往年今日 [预览回忆]，没有就返回 null。
    """
    today = datetime.now().date()

    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    rows = (
        Memory.query.outerjoin(UserMemory)
        .filter(or_(Memory.creator_id == user_id, UserMemory.user_id == user_id))
        .distinct()
        .all()
    )

    previews = []
    for memory in rows:
        created = memory.created_at
        if not isinstance(created, datetime):
            continue
        d = created.date()
        if d.month == today.month and d.day == today.day and d.year < today.year:
            previews.append(_serialize_memory(memory)["preview"])

    previews.sort(key=lambda p: p["date"] or "", reverse=True)

    if not previews:
        return jsonify(None)

    return jsonify(previews)


# ========== 收藏：添加 / 获取 ==========

@memory_bp.route("/user/<int:user_id>/favorites", methods=["POST"])
def add_favorite(user_id: int):
    """
    请求：添加收藏；
    body: {"memory_id": 3}
    """
    data = request.get_json() or {}
    memory_id = data.get("memory_id")
    if memory_id is None:
        return jsonify({"error": "缺少 memory_id"}), 400

    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404
    if not _memory_exists(memory_id):
        return jsonify({"error": "回忆不存在"}), 404

    link = UserMemory.query.filter_by(user_id=user_id, memory_id=memory_id).first()
    if link is None:
        link = UserMemory(user_id=user_id, memory_id=memory_id, is_favorite=True)
        db.session.add(link)
    else:
        link.is_favorite = True
    db.session.commit()

    favorites = (
        UserMemory.query.filter_by(user_id=user_id, is_favorite=True)
        .order_by(UserMemory.joined_at.desc())
        .all()
    )

    return jsonify({
        "ok": True,
        "favorites": [f.memory_id for f in favorites],
    })


@memory_bp.route("/user/<int:user_id>/favorites", methods=["GET"])
def get_favorites(user_id: int):
    """
    请求：获取收藏；
    返回：按时间排序，最近的第 [l,r] 条收藏。
    """
    l = int(request.args.get("l", 1))
    r = int(request.args.get("r", 10))
    if r < l:
        return jsonify([])

    limit = r - l + 1
    offset = l - 1

    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    memories = (
        Memory.query.join(UserMemory, UserMemory.memory_id == Memory.id)
        .filter(UserMemory.user_id == user_id, UserMemory.is_favorite.is_(True))
        .order_by(Memory.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return jsonify([_serialize_memory(m) for m in memories])


@memory_bp.route("/user/<int:user_id>/collections", methods=["GET"])
def get_collections(user_id: int):
    """
    请求：获取收藏（兼容前端 collections 路由）；行为同 /favorites
    返回：按收藏时间倒序的回忆列表 [l, r]
    """
    l = int(request.args.get("l", 1))
    r = int(request.args.get("r", 10))
    if r < l:
        return jsonify([])

    limit = r - l + 1
    offset = l - 1

    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

    memories = (
        Memory.query.join(UserMemory, UserMemory.memory_id == Memory.id)
        .filter(UserMemory.user_id == user_id, UserMemory.is_favorite.is_(True))
        .order_by(UserMemory.joined_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return jsonify([_serialize_memory(m) for m in memories])


# ========== 人员列表（用于前端 persons 路由） ==========

@memory_bp.route("/user/<int:user_id>/persons", methods=["GET"])
def get_persons(user_id: int):
    """
    请求：获取人员列表；前端期望 /persons 路由
    查询参数：l, r（1-based），按 id 升序
    """
    l = int(request.args.get("l", 1))
    r = int(request.args.get("r", 10))
    if r < l:
        return jsonify([])

    limit = r - l + 1
    offset = l - 1

    if not _user_exists(user_id):
        return jsonify({"error": "用户不存在"}), 404

<<<<<<< Updated upstream
    users = (
        User.query.filter(User.id != user_id)
        .order_by(User.id.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return jsonify([_serialize_user(u) for u in users])
=======
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT u.id, u.name, a.image_base64 AS avatar_base64
                FROM users u
                LEFT JOIN avatars a ON a.user_id = u.id
                WHERE u.id != %s
                ORDER BY u.id ASC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
        except Exception:
            # 兼容老库：没有 avatars 表时退回 users.avatar
            cur.execute(
                """
                SELECT id, name, avatar AS avatar_base64
                FROM users
                WHERE id != %s
                ORDER BY id ASC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
        rows = cur.fetchall()
        cur.close()
        return jsonify([_serialize_user(r) for r in rows])
    finally:
        conn.close()
>>>>>>> Stashed changes


# ========== 评论：添加 / 获取 ==========

@memory_bp.route("/memory/<int:memory_id>/comments", methods=["POST"])
def add_comment_to_memory(memory_id: int):
    """
    请求：添加评论；
    推送：评论人，评论信息。
    body:
    {
        "commenter_id": 1,
        "target_id": 2,            # 可选，没有可以等于 commenter_id
        "comment": "好好看！",
        "picture_ids": [10, 11]
    }
    """
    data = request.get_json() or {}
    commenter_id = int(data.get("commenter_id") or 0)
    target_id = int(data.get("target_id") or commenter_id)
    content = (data.get("comment") or "").strip()
    picture_ids = data.get("picture_ids") or []

    if not content:
        return jsonify({"error": "评论内容不能为空"}), 400

    if not _memory_exists(memory_id):
        return jsonify({"error": "回忆不存在"}), 404
    if not _user_exists(commenter_id):
        return jsonify({"error": "评论用户不存在"}), 404

    try:
        comment = Comment(
            memory_id=memory_id,
            commenter_id=commenter_id,
            target_id=target_id,
            content=content,
        )
        if picture_ids:
            pics = (
                Picture.query.filter(Picture.id.in_(picture_ids))
                .filter(Picture.memory_id == memory_id)
                .all()
            )
            comment.pictures = pics

        db.session.add(comment)
        db.session.commit()

        return jsonify(_serialize_comment(comment)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"添加评论失败: {str(e)}"}), 500


@memory_bp.route("/memory/<int:memory_id>/comments", methods=["GET"])
def get_comments(memory_id: int):
    """
    请求：获取评论；
    返回：在一个回忆中，按时间排序，最近的第 [l,r] 条评论。
    """
    l = int(request.args.get("l", 1))
    r = int(request.args.get("r", 10))
    if r < l:
        return jsonify([])

    limit = r - l + 1
    offset = l - 1

    if not _memory_exists(memory_id):
        return jsonify({"error": "回忆不存在"}), 404

    comments = (
        Comment.query.filter_by(memory_id=memory_id)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return jsonify([_serialize_comment(c) for c in comments])


# ========== Debug: pg-test（你之前的） ==========

@memory_bp.route("/debug/pg-test", methods=["GET"])
def pg_test():
    """
    连接 PostgreSQL，建一个 debug_ping 表，插入 & 查询几条记录。
    用来确认数据库连通 + 能读写。
    """
    try:
        db.create_all()
        ping = DebugPing(message="hello from memory backend")
        db.session.add(ping)
        db.session.commit()

        rows = (
            DebugPing.query.order_by(DebugPing.created_at.desc())
            .limit(5)
            .all()
        )

        return jsonify({
            "ok": True,
            "inserted": {
                "id": ping.id,
                "created_at": ping.created_at,
            },
            "recent_rows": [
                {
                    "id": r.id,
                    "message": r.message,
                    "created_at": r.created_at,
                }
                for r in rows
            ],
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "ok": False,
            "step": "query",
            "error": str(e),
        }), 500


# ========== Debug: 初始化一点 demo 数据 ==========

@memory_bp.route("/debug/init-demo-data", methods=["POST"])
def init_demo_data():
    """
    初始化几条用户 / 回忆 / 图片 / 消息 / 收藏数据，方便你测试。
    如果 users 表不为空，则不会重复创建。
    """
    try:
        if User.query.count() > 0:
            return jsonify({
                "ok": True,
                "skip": True,
                "reason": "users 表已经有数据了，不重复初始化",
            })

        users_info = [
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            ("Alice", "/avatar/alice.png", "alice123", "向海而行"),
            ("Bob", "/avatar/bob.png", "bob123", "今天也要努力"),
            ("Carol", "/avatar/carol.png", "carol123", "记录生活的小确幸"),
        ]
        user_ids: Dict[str, int] = {}
        for name, avatar, pwd, signature in users_info:
            user = User(
                name=name,
                avatar_url=avatar,
                password=pwd,
                signature=signature,
=======
=======
>>>>>>> Stashed changes
            ("Alice", "alice123"),
            ("Bob", "bob123"),
            ("Carol", "carol123"),
        ]
        user_ids = {}
        for name, pwd in users_info:
            cur.execute(
                """
                INSERT INTO users (name, password)
                VALUES (%s, %s)
                RETURNING id
                """,
                (name, pwd),
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            )
            db.session.add(user)
            db.session.flush()
            user_ids[name] = user.id

<<<<<<< Updated upstream
=======
        # 1.1 add base64 avatars for demo users；如果没有 avatars 表则跳过
        try:
            avatar_files = {
                "Alice": "mowan.png",
                "Bob": "modi.jpg",
                "Carol": "mowan.png",
            }
            for name, filename in avatar_files.items():
                avatar_b64 = _load_avatar_file_base64(filename)
                if avatar_b64:
                    cur.execute(
                        """
                        INSERT INTO avatars (user_id, filename, image_base64)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE
                        SET filename = EXCLUDED.filename,
                            image_base64 = EXCLUDED.image_base64
                        """,
                        (user_ids[name], filename, avatar_b64),
                    )
        except Exception:
            pass

        # 1.1 add base64 avatars for demo users；如果没有 avatars 表则跳过
        try:
            avatar_files = {
                "Alice": "mowan.png",
                "Bob": "modi.jpg",
                "Carol": "mowan.png",
            }
            for name, filename in avatar_files.items():
                avatar_b64 = _load_avatar_file_base64(filename)
                if avatar_b64:
                    cur.execute(
                        """
                        INSERT INTO avatars (user_id, filename, image_base64)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE
                        SET filename = EXCLUDED.filename,
                            image_base64 = EXCLUDED.image_base64
                        """,
                        (user_ids[name], filename, avatar_b64),
                    )
        except Exception:
            pass

        # 2. 创建两条回忆
>>>>>>> Stashed changes
        today = datetime.now().date()
        mem1_date = datetime(today.year - 1, today.month, today.day)
        mem2_date = datetime(today.year - 1, today.month, max(1, today.day - 1))

        mem1 = Memory(
            title="海边散步",
            location="东京湾",
            creator_id=user_ids["Alice"],
            created_at=mem1_date,
        )
        mem2 = Memory(
            title="图书馆复习",
            location="校园图书馆",
            creator_id=user_ids["Bob"],
            created_at=mem2_date,
        )
        db.session.add_all([mem1, mem2])
        db.session.flush()

        def ensure_user_memory(uid: int, mem_id: int, favorite: bool = False):
            link = UserMemory.query.filter_by(user_id=uid, memory_id=mem_id).first()
            if link is None:
                link = UserMemory(user_id=uid, memory_id=mem_id, is_favorite=favorite)
                db.session.add(link)
            elif favorite:
                link.is_favorite = True

        ensure_user_memory(user_ids["Alice"], mem1.id)
        ensure_user_memory(user_ids["Bob"], mem1.id)
        for u in ["Alice", "Bob", "Carol"]:
            ensure_user_memory(user_ids[u], mem2.id)

        for pict in ["/pics/m1_p1.png", "/pics/m1_p2.png"]:
            db.session.add(Picture(memory_id=mem1.id, pict=pict, title=mem1.title))
        db.session.add(Picture(memory_id=mem2.id, pict="/pics/m2_p1.png", title=mem2.title))

        msg1 = Message(
            sender_id=None,
            text="系统：Bob 邀请你加入回忆《海边散步》",
            system=True,
            memory_id=mem1.id,
        )
        msg2 = Message(
            sender_id=user_ids["Bob"],
            text="周末一起去看海吗？",
            system=False,
        )
        db.session.add_all([msg1, msg2])
        db.session.flush()

        db.session.add(UserMessage(user_id=user_ids["Alice"], message_id=msg1.id))
        db.session.add(UserMessage(user_id=user_ids["Alice"], message_id=msg2.id))

        ensure_user_memory(user_ids["Alice"], mem1.id, favorite=True)
        ensure_user_memory(user_ids["Alice"], mem2.id, favorite=True)
        ensure_user_memory(user_ids["Bob"], mem1.id, favorite=True)

        db.session.commit()

        return jsonify({
            "ok": True,
            "created_users": user_ids,
            "created_memories": {
                "mem1_id": mem1.id,
                "mem2_id": mem2.id,
            },
            "created_favorites": {
                "Alice": [mem1.id, mem2.id],
                "Bob": [mem1.id],
            },
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
