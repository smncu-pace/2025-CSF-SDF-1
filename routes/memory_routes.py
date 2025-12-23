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
import base64
import mimetypes
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

import models.db
from flask import Blueprint, request, jsonify, current_app
from utils.helpers import paginate_sorted
from db import get_db_connection  # 在需要的地方再导入


memory_bp = Blueprint("memory", __name__)


# ------------ 小工具函数 ------------

def _user_exists(user_id: int, conn) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE id = %s", (user_id,))
    exists = cur.fetchone() is not None
    cur.close()
    return exists


def _memory_exists(memory_id: int, conn) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM memories WHERE id = %s", (memory_id,))
    exists = cur.fetchone() is not None
    cur.close()
    return exists


def _fetch_visible_user_ids(memory_id: int, conn) -> List[int]:
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id FROM memory_visible_users WHERE memory_id = %s",
        (memory_id,),
    )
    rows = cur.fetchall()
    cur.close()
    return [r["user_id"] for r in rows]


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


def _serialize_message(row: Dict[str, Any]) -> Dict[str, Any]:
    links: Dict[str, int] = {}
    if row.get("memory_id") is not None:
        links["memory_id"] = row["memory_id"]
    if row.get("picture_id") is not None:
        links["picture_id"] = row["picture_id"]
    if row.get("comment_id") is not None:
        links["comment_id"] = row["comment_id"]

    created = row.get("created_at")
    return {
        "id": row["id"],
        "sender_id": row["sender_id"],
        "receiver_id": row["receiver_id"],
        "text": row["text"],
        "time": created.isoformat() if isinstance(created, datetime) else None,
        "read": row["read"],
        "system": row["system"],
        "links": links,
    }


def _serialize_memory(row: Dict[str, Any], conn) -> Dict[str, Any]:
    mem_id = row["id"]
    visible_user_ids = _fetch_visible_user_ids(mem_id, conn)
    cover = _fetch_cover_picture(mem_id, conn)
    created = row.get("created_at")
    created_date = created.date() if isinstance(created, datetime) else None

    preview = {
        "memory_id": mem_id,
        "title": row["title"],
        "cover_picture": cover,
        "date": created_date.isoformat() if created_date else None,
        "location": row["location"],
    }

    return {
        "memory_id": mem_id,
        "title": row["title"],
        "visible_user_ids": visible_user_ids,
        "location": row["location"],
        "creator_id": row["creator_id"],
        "created_at": created.isoformat() if isinstance(created, datetime) else None,
        "preview": preview,
    }


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
    return {
        "comment_id": comment_id,
        "commenter_id": row["commenter_id"],
        "target_id": row["target_id"],
        "comment": row["content"],
        "links": pics,
        "sub_comments": [],      # 先留空，后面你要的话可以做子评论表
        "emoji_comments": {},    # 同理
        "created_at": created.isoformat() if isinstance(created, datetime) else None,
    }


def _serialize_user(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user_id": row["id"],
        "name": row.get("name"),
        "avatar": row.get("avatar_base64"),
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
        return jsonify({"ok": False, "error": "用户名或密码错误"}), 401

    return jsonify({
        "ok": True,
        "user": {
            "user_id": row["id"],
            "name": row["name"],
            "avatar": row.get("avatar_base64"),
        }
    })


@memory_bp.route("/user/<int:user_id>/profile", methods=["GET"])
def get_user_profile(user_id: int):
    """
    请求：个人信息；返回：用户名，用户头像。（前端可缓存）
    """
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
    })


# ========== 消息相关：系统 / 用户 / 全部 / 标记已读 ==========

def _fetch_messages_for_user(user_id: int, conn, system_only: bool | None):
    sql = """
        SELECT id, sender_id, receiver_id, text, created_at, read, system,
               memory_id, picture_id, comment_id
        FROM messages
        WHERE receiver_id = %s
    """
    params = [user_id]
    if system_only is True:
        sql += " AND system = TRUE"
    elif system_only is False:
        sql += " AND system = FALSE"

    sql += " ORDER BY created_at DESC"

    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows


@memory_bp.route("/user/<int:user_id>/messages/system", methods=["GET"])
def get_system_messages(user_id: int):
    """请求：系统消息；返回：来自系统的消息"""
    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        rows = _fetch_messages_for_user(user_id, conn, system_only=True)
        return jsonify([_serialize_message(r) for r in rows])
    finally:
        conn.close()


@memory_bp.route("/user/<int:user_id>/messages/user", methods=["GET"])
def get_user_messages(user_id: int):
    """请求：用户消息；返回：来自其他用户的消息"""
    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        rows = _fetch_messages_for_user(user_id, conn, system_only=False)
        return jsonify([_serialize_message(r) for r in rows])
    finally:
        conn.close()


@memory_bp.route("/user/<int:user_id>/messages", methods=["GET"])
def get_all_messages(user_id: int):
    """
    请求：获取消息；
    返回：消息id，发送者id，消息内容，消息时间，消息已读状态。
    """
    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        rows = _fetch_messages_for_user(user_id, conn, system_only=None)
        return jsonify([_serialize_message(r) for r in rows])
    finally:
        conn.close()


@memory_bp.route("/user/<int:user_id>/messages/<int:msg_id>/read", methods=["POST"])
def mark_message_read(user_id: int, msg_id: int):
    """
    请求：标记已读；推送：将指定id的消息标为已读。
    """
    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            "UPDATE messages SET read = TRUE WHERE id = %s AND receiver_id = %s "
            "RETURNING id;",
            (msg_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            cur.close()
            return jsonify({"error": "消息不存在或不属于该用户"}), 404

        conn.commit()
        cur.close()
        return jsonify({"ok": True, "message_id": msg_id})
    finally:
        conn.close()


# ========== 回忆：预览 / 获取 / 限定人员 / 包含人员 / 新建 / 往年今日 ==========

@memory_bp.route("/memory/<int:memory_id>/preview", methods=["GET"])
def preview_memory(memory_id: int):
    """
    请求：预览回忆；
    返回：标题 + 封面图 + 日期 + 地点
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, location, creator_id, created_at "
            "FROM memories WHERE id = %s",
            (memory_id,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return jsonify({"error": "回忆不存在"}), 404

        return jsonify(_serialize_memory(row, conn))
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

    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT m.id, m.title, m.location, m.creator_id, m.created_at
            FROM memories m
            LEFT JOIN memory_visible_users mv ON mv.memory_id = m.id
            WHERE m.creator_id = %s OR mv.user_id = %s
            ORDER BY m.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, user_id, limit, offset),
        )
        rows = cur.fetchall()
        cur.close()

        return jsonify([_serialize_memory(row, conn) for row in rows])
    finally:
        conn.close()


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

    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT m.id, m.title, m.location, m.creator_id, m.created_at
            FROM memories m
            LEFT JOIN memory_visible_users mv ON mv.memory_id = m.id
            WHERE m.creator_id = %s OR mv.user_id = %s
            """,
            (user_id, user_id),
        )
        rows = cur.fetchall()
        cur.close()

        filtered = []
        for row in rows:
            vis_ids = sorted(set(_fetch_visible_user_ids(row["id"], conn)))
            if vis_ids == target_ids:
                filtered.append(_serialize_memory(row, conn))

        # 按 created_at 再排序一下
        filtered.sort(key=lambda m: m["created_at"] or "", reverse=True)
        page = paginate_sorted(filtered, l, r)
        return jsonify(page)
    finally:
        conn.close()


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

    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT m.id, m.title, m.location, m.creator_id, m.created_at
            FROM memories m
            LEFT JOIN memory_visible_users mv ON mv.memory_id = m.id
            WHERE m.creator_id = %s OR mv.user_id = %s
            """,
            (user_id, user_id),
        )
        rows = cur.fetchall()
        cur.close()

        filtered = []
        for row in rows:
            vis_set = set(_fetch_visible_user_ids(row["id"], conn))
            if target_set.issubset(vis_set) and vis_set != target_set:
                filtered.append(_serialize_memory(row, conn))

        filtered.sort(key=lambda m: m["created_at"] or "", reverse=True)
        page = paginate_sorted(filtered, l, r)
        return jsonify(page)
    finally:
        conn.close()


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

    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        cur = conn.cursor()

        # 插入 memories
        if created_at is None:
            cur.execute(
                """
                INSERT INTO memories (title, location, creator_id)
                VALUES (%s, %s, %s)
                RETURNING id, title, location, creator_id, created_at
                """,
                (title, location, user_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO memories (title, location, creator_id, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id, title, location, creator_id, created_at
                """,
                (title, location, user_id, created_at),
            )
        mem_row = cur.fetchone()

        mem_id = mem_row["id"]

        # 插入可见用户（确保自己也在里面）
        if user_id not in visible_ids:
            visible_ids.append(user_id)

        for uid in set(visible_ids):
            cur.execute(
                """
                INSERT INTO memory_visible_users (memory_id, user_id)
                VALUES (%s, %s)
                ON CONFLICT (memory_id, user_id) DO NOTHING
                """,
                (mem_id, uid),
            )

        # 插入图片
        for p in pictures:
            cur.execute(
                """
                INSERT INTO pictures (memory_id, pict, title)
                VALUES (%s, %s, %s)
                """,
                (mem_id, p, title),
            )

        conn.commit()
        cur.close()

        return jsonify(_serialize_memory(mem_row, conn)), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"创建回忆失败: {str(e)}"}), 500
    finally:
        conn.close()


@memory_bp.route("/user/<int:user_id>/memories/on-this-day", methods=["GET"])
def memories_on_this_day(user_id: int):
    """
    请求：往年今日；
    返回：所有的往年今日 [预览回忆]，没有就返回 null。
    """
    today = datetime.now().date()

    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT m.id, m.title, m.location, m.creator_id, m.created_at
            FROM memories m
            LEFT JOIN memory_visible_users mv ON mv.memory_id = m.id
            WHERE m.creator_id = %s OR mv.user_id = %s
            """,
            (user_id, user_id),
        )
        rows = cur.fetchall()
        cur.close()

        previews = []
        for row in rows:
            created = row["created_at"]
            if not isinstance(created, datetime):
                continue
            d = created.date()
            if d.month == today.month and d.day == today.day and d.year < today.year:
                previews.append(_serialize_memory(row, conn)["preview"])

        previews.sort(key=lambda p: p["date"] or "", reverse=True)

        if not previews:
            return jsonify(None)

        return jsonify(previews)
    finally:
        conn.close()


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

    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404
        if not _memory_exists(memory_id, conn):
            return jsonify({"error": "回忆不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO favorites (user_id, memory_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, memory_id) DO NOTHING
            """,
            (user_id, memory_id),
        )

        conn.commit()

        # 返回当前收藏列表的 memory_id
        cur.execute(
            "SELECT memory_id FROM favorites WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()

        return jsonify({
            "ok": True,
            "favorites": [r["memory_id"] for r in rows],
        })
    finally:
        conn.close()


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

    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.id, m.title, m.location, m.creator_id, m.created_at
            FROM favorites f
            JOIN memories m ON f.memory_id = m.id
            WHERE f.user_id = %s
            ORDER BY m.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()
        cur.close()

        return jsonify([_serialize_memory(row, conn) for row in rows])
    finally:
        conn.close()


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

    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.id, m.title, m.location, m.creator_id, m.created_at
            FROM favorites f
            JOIN memories m ON f.memory_id = m.id
            WHERE f.user_id = %s
            ORDER BY f.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()
        cur.close()

        return jsonify([_serialize_memory(row, conn) for row in rows])
    finally:
        conn.close()


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

    conn = get_db_connection()
    try:
        if not _user_exists(user_id, conn):
            return jsonify({"error": "用户不存在"}), 404

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

    conn = get_db_connection()
    try:
        if not _memory_exists(memory_id, conn):
            return jsonify({"error": "回忆不存在"}), 404
        if not _user_exists(commenter_id, conn):
            return jsonify({"error": "评论用户不存在"}), 404

        cur = conn.cursor()

        # 插入评论
        cur.execute(
            """
            INSERT INTO comments (memory_id, commenter_id, target_id, content)
            VALUES (%s, %s, %s, %s)
            RETURNING id, memory_id, commenter_id, target_id, content, created_at
            """,
            (memory_id, commenter_id, target_id, content),
        )
        row = cur.fetchone()
        comment_id = row["id"]

        # picture_ids 只允许属于该 memory 的图片
        for pid in picture_ids:
            cur.execute(
                "SELECT 1 FROM pictures WHERE id = %s AND memory_id = %s",
                (pid, memory_id),
            )
            if cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO comment_picture_links (comment_id, picture_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (comment_id, pid),
                )

        conn.commit()
        cur.close()

        return jsonify(_serialize_comment(row, conn)), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"添加评论失败: {str(e)}"}), 500
    finally:
        conn.close()


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

    conn = get_db_connection()
    try:
        if not _memory_exists(memory_id, conn):
            return jsonify({"error": "回忆不存在"}), 404

        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, memory_id, commenter_id, target_id, content, created_at
            FROM comments
            WHERE memory_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (memory_id, limit, offset),
        )
        rows = cur.fetchall()
        cur.close()

        return jsonify([_serialize_comment(row, conn) for row in rows])
    finally:
        conn.close()


# ========== Debug: pg-test（你之前的） ==========

@memory_bp.route("/debug/pg-test", methods=["GET"])
def pg_test():
    """
    连接 PostgreSQL，建一个 debug_ping 表，插入 & 查询几条记录。
    用来确认数据库连通 + 能读写。
    """
    try:
        conn = get_db_connection()
    except Exception as e:
        return jsonify({
            "ok": False,
            "step": "connect",
            "error": str(e),
        }), 500

    try:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS debug_ping (
            id          SERIAL PRIMARY KEY,
            message     TEXT NOT NULL,
            created_at  TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """)
        cur.execute(
            "INSERT INTO debug_ping (message) VALUES (%s) RETURNING id, created_at;",
            ("hello from memory backend",),
        )
        inserted = cur.fetchone()

        cur.execute(
            """
            SELECT id, message, created_at
            FROM debug_ping
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        rows = cur.fetchall()

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "ok": True,
            "inserted": inserted,
            "recent_rows": rows,
        })
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
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
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM users")
        count = cur.fetchone()["c"]
        if count > 0:
            cur.close()
            conn.close()
            return jsonify({
                "ok": True,
                "skip": True,
                "reason": "users 表已经有数据了，不重复初始化",
            })

        # 1. 创建用户
        users_info = [
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
            )
            uid = cur.fetchone()["id"]
            user_ids[name] = uid

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
        today = datetime.now().date()
        mem1_date = datetime(today.year - 1, today.month, today.day)
        mem2_date = datetime(today.year - 1, today.month, max(1, today.day - 1))

        # 海边散步
        cur.execute(
            """
            INSERT INTO memories (title, location, creator_id, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id, title, location, creator_id, created_at
            """,
            ("海边散步", "东京湾", user_ids["Alice"], mem1_date),
        )
        mem1 = cur.fetchone()

        # 图书馆复习
        cur.execute(
            """
            INSERT INTO memories (title, location, creator_id, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id, title, location, creator_id, created_at
            """,
            ("图书馆复习", "校园图书馆", user_ids["Bob"], mem2_date),
        )
        mem2 = cur.fetchone()

        # 3. 可见人员
        # 海边散步：Alice, Bob
        cur.execute(
            "INSERT INTO memory_visible_users (memory_id, user_id) VALUES (%s, %s)",
            (mem1["id"], user_ids["Alice"]),
        )
        cur.execute(
            "INSERT INTO memory_visible_users (memory_id, user_id) VALUES (%s, %s)",
            (mem1["id"], user_ids["Bob"]),
        )

        # 图书馆复习：Alice, Bob, Carol
        for u in ["Alice", "Bob", "Carol"]:
            cur.execute(
                "INSERT INTO memory_visible_users (memory_id, user_id) VALUES (%s, %s)",
                (mem2["id"], user_ids[u]),
            )

        # 4. 图片
        for pict in ["/pics/m1_p1.png", "/pics/m1_p2.png"]:
            cur.execute(
                "INSERT INTO pictures (memory_id, pict, title) VALUES (%s, %s, %s)",
                (mem1["id"], pict, mem1["title"]),
            )

        cur.execute(
            "INSERT INTO pictures (memory_id, pict, title) VALUES (%s, %s, %s)",
            (mem2["id"], "/pics/m2_p1.png", mem2["title"]),
        )

        # 5. 消息（1 条系统 + 1 条普通）
        cur.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, text, system, memory_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                None,
                user_ids["Alice"],
                "系统：Bob 邀请你加入回忆《海边散步》",
                True,
                mem1["id"],
            ),
        )

        cur.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, text, system)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_ids["Bob"],
                user_ids["Alice"],
                "周末一起去看海吗？",
                False,
            ),
        )

        # 6. 收藏示例：Alice 收藏 mem1、mem2；Bob 收藏 mem1
        cur.execute(
            "INSERT INTO favorites (user_id, memory_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_ids["Alice"], mem1["id"]),
        )
        cur.execute(
            "INSERT INTO favorites (user_id, memory_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_ids["Alice"], mem2["id"]),
        )
        cur.execute(
            "INSERT INTO favorites (user_id, memory_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_ids["Bob"], mem1["id"]),
        )

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "ok": True,
            "created_users": user_ids,
            "created_memories": {
                "mem1_id": mem1["id"],
                "mem2_id": mem2["id"],
            },
            "created_favorites": {
                "Alice": [mem1["id"], mem2["id"]],
                "Bob": [mem1["id"]],
            },
        }), 201
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"ok": False, "error": str(e)}), 500
