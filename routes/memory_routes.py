# -*- coding: utf-8 -*-
# routes/memory_routes.py

"""
基于 services/memory_services.py 的 SQLAlchemy 版本路由
"""

from __future__ import annotations

import base64
import mimetypes
import os
import uuid
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from services.memory_services import (
    query_memories_by_time,
    query_memories_by_members_exact,
    query_memories_by_members_include,
    query_favorite_memories,
    query_memories_on_this_day,
    create_memory,
    delete_memory,
    get_memory_detail,
    update_memory_basic,
    get_memory_members,
    request_add_members,
    add_member_to_memory,
    add_monitors,
    remove_members,
    remove_monitors,
)


memory_bp = Blueprint("memory", __name__)


def _parse_time_value(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _save_cover_base64(cover_base64: str | None) -> str | None:
    if not cover_base64:
        return None

    data = cover_base64.strip()
    mime = None
    if data.startswith("data:"):
        header, b64 = data.split(",", 1)
        if ";base64" in header:
            mime = header[5:].split(";", 1)[0]
        data = b64

    try:
        raw = base64.b64decode(data, validate=True)
    except Exception:
        return None

    ext = mimetypes.guess_extension(mime or "") or ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    rel_dir = os.path.join("uploads", "covers")
    abs_dir = os.path.join(current_app.root_path, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, filename)

    with open(abs_path, "wb") as f:
        f.write(raw)

    return f"/{rel_dir}/{filename}"


def _load_cover_base64(cover_url: str | None) -> str | None:
    if not cover_url:
        return None
    abs_path = os.path.join(current_app.root_path, cover_url.lstrip("/"))
    try:
        with open(abs_path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return None


# ========== 回忆查询 ==========

@memory_bp.route("/memory/query/time", methods=["POST"])
def api_query_memories_by_time():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    time_value = data.get("time")
    rows = query_memories_by_time(user_id, time_value)
    for row in rows:
        row["picture"] = _load_cover_base64(row.get("picture"))
    return jsonify(rows)


@memory_bp.route("/memory/query/only-members", methods=["POST"])
def api_query_memories_by_members_exact():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    members = data.get("members") or []
    rows = query_memories_by_members_exact(user_id, members)
    for row in rows:
        row["picture"] = _load_cover_base64(row.get("picture"))
    return jsonify(rows)


@memory_bp.route("/memory/query/include-members", methods=["POST"])
def api_query_memories_by_members_include():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    members = data.get("members") or []
    rows = query_memories_by_members_include(user_id, members)
    for row in rows:
        row["picture"] = _load_cover_base64(row.get("picture"))
    return jsonify(rows)


@memory_bp.route("/memory/query/favorites", methods=["POST"])
def api_query_favorite_memories():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    rows = query_favorite_memories(user_id)
    for row in rows:
        row["picture"] = _load_cover_base64(row.get("picture"))
    return jsonify(rows)


@memory_bp.route("/memory/query/on-this-day", methods=["POST"])
def api_query_memories_on_this_day():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    time_value = data.get("time")
    rows = query_memories_on_this_day(user_id, time_value)
    for row in rows:
        row["picture"] = _load_cover_base64(row.get("picture"))
    return jsonify(rows)


# ========== 回忆创建 / 删除 / 详情 / 修改 ==========

@memory_bp.route("/memory/create", methods=["POST"])
def api_create_memory():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    title = (data.get("title") or "").strip()
    location = data.get("location")
    description = data.get("description")
    cover_base64 = data.get("cover_base64")
    cover_url = _save_cover_base64(cover_base64)
    if cover_base64 and not cover_url:
        return jsonify({"message": "封面格式错误"}), 400
    time_range = data.get("time") or []
    start_time = _parse_time_value(time_range[0]) if len(time_range) > 0 else None
    end_time = _parse_time_value(time_range[1]) if len(time_range) > 1 else None

    try:
        memory_id = create_memory(
            user_id=user_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            location=location,
            description=description,
            cover_url=cover_url,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"MemoryID": memory_id})


@memory_bp.route("/memory/delete", methods=["POST"])
def api_delete_memory():
    data = request.get_json() or {}
    memory_id = int(data.get("MemoryID") or 0)
    user_id = int(data.get("UserID") or 0)
    result = delete_memory(memory_id, user_id)
    if result is None:
        return jsonify(None)
    return jsonify(result), 400


@memory_bp.route("/memory/detail", methods=["POST"])
def api_get_memory_detail():
    data = request.get_json() or {}
    memory_id = int(data.get("MemoryID") or 0)
    detail = get_memory_detail(memory_id)
    if detail is None:
        return jsonify({"message": "未找到回忆"}), 404
    if detail.get("cover_url") is not None:
        detail["cover_base64"] = _load_cover_base64(detail["cover_url"])
    return jsonify(detail)


@memory_bp.route("/memory/update-basic", methods=["POST"])
def api_update_memory_basic():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    memory_id = int(data.get("MemoryID") or 0)
    title = data.get("title")
    location = data.get("location")
    description = data.get("description")
    time_range = data.get("time") or []
    start_time = _parse_time_value(time_range[0]) if len(time_range) > 0 else None
    end_time = _parse_time_value(time_range[1]) if len(time_range) > 1 else None
    cover_base64 = data.get("cover_base64")
    cover_url = _save_cover_base64(cover_base64)
    if cover_base64 and not cover_url:
        return jsonify({"message": "封面格式错误"}), 400

    result = update_memory_basic(
        user_id=user_id,
        memory_id=memory_id,
        title=title,
        location=location,
        description=description,
        start_time=start_time,
        end_time=end_time,
        cover_url=cover_url,
    )
    if result is None:
        return jsonify(None)
    return jsonify(result), 400


# ========== 成员管理 ==========

@memory_bp.route("/memory/members", methods=["POST"])
def api_get_memory_members():
    data = request.get_json() or {}
    memory_id = int(data.get("MemoryID") or 0)
    result = get_memory_members(memory_id)
    if result is None:
        return jsonify({"message": "未找到回忆"}), 404
    return jsonify(result)


@memory_bp.route("/memory/members/request-add", methods=["POST"])
def api_request_add_members():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    memory_id = int(data.get("MemoryID") or 0)
    members = data.get("members") or []
    result = request_add_members(user_id, memory_id, members)
    if result is None:
        return jsonify(None)
    return jsonify(result), 400


@memory_bp.route("/memory/members/add", methods=["POST"])
def api_add_member_to_memory():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    memory_id = int(data.get("MemoryID") or 0)
    result = add_member_to_memory(user_id, memory_id)
    if result is None:
        return jsonify(None)
    return jsonify(result), 400


@memory_bp.route("/memory/members/add-admins", methods=["POST"])
def api_add_monitors():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    memory_id = int(data.get("MemoryID") or 0)
    members = data.get("members") or []
    result = add_monitors(user_id, memory_id, members)
    if result is None:
        return jsonify(None)
    return jsonify(result), 400


@memory_bp.route("/memory/members/remove", methods=["POST"])
def api_remove_members():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    memory_id = int(data.get("MemoryID") or 0)
    members = data.get("members") or []
    result = remove_members(user_id, memory_id, members)
    if result is None:
        return jsonify(None)
    return jsonify(result), 400


@memory_bp.route("/memory/members/remove-admins", methods=["POST"])
def api_remove_monitors():
    data = request.get_json() or {}
    user_id = int(data.get("UserID") or 0)
    memory_id = int(data.get("MemoryID") or 0)
    members = data.get("members") or []
    result = remove_monitors(user_id, memory_id, members)
    if result is None:
        return jsonify(None)
    return jsonify(result), 400
