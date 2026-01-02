# routes/user_routes.py

from __future__ import annotations

import base64
import mimetypes
import os
import uuid

from flask import Blueprint, current_app, jsonify, request

from services.user_services import (
    create_user,
    authenticate,
    get_user,
    get_user_by_name,
    list_users,
    update_signature,
    update_avatar_url,
)


user_bp = Blueprint("user", __name__)

# 保存工具函数
def _save_avatar_base64(avatar_base64: str | None) -> str | None:
    if not avatar_base64:
        return None

    data = avatar_base64.strip()
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
    rel_dir = os.path.join("uploads", "avatars")
    abs_dir = os.path.join(current_app.root_path, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, filename)

    with open(abs_path, "wb") as f:
        f.write(raw)

    return f"/{rel_dir}/{filename}"

# 根据URL链接读取base64
def _load_avatar_base64(avatar_url: str | None) -> str | None:
    if not avatar_url:
        return None
    abs_path = os.path.join(current_app.root_path, avatar_url.lstrip("/"))
    try:
        with open(abs_path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return None




## 用户注册
@user_bp.route("/user/register", methods=["POST"])
def api_register_user():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""
    avatar_base64 = data.get("avatar_base64")
    avatar_url = _save_avatar_base64(avatar_base64)
    signature = data.get("signature") or ""

    if avatar_base64 and not avatar_url:
        return jsonify({"message": "头像格式错误"}), 400

    user = create_user(
        name=name,
        password=password,
        avatar_url=avatar_url,
        signature=signature,
    )
    return jsonify({"UserID": user["id"]})

## 用户登录
@user_bp.route("/user/login", methods=["POST"])
def api_login_user():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""

    user = authenticate(name, password)
    if user is None:
        return jsonify({"ok": False, "message": "用户名或密码错误"}), 401

    return jsonify({
        "ok": True,
        "user": {
            "UserID": user["id"],
            "name": user["name"],
            "avatar_base64": _load_avatar_base64(user["avatar_url"]),
            "signature": user["signature"],
        },
    })

# ID检索
@user_bp.route("/user/<int:user_id>", methods=["GET"])
def api_get_user(user_id: int):
    user = get_user(user_id)
    if user is None:
        return jsonify({"message": "用户不存在"}), 404

    avatar_base64 = _load_avatar_base64(user["avatar_url"])

    return jsonify({
        "UserID": user["id"],
        "name": user["name"],
        "avatar_base64": avatar_base64,
        "signature": user["signature"],
    })

## 名字检索
@user_bp.route("/user/lookup", methods=["POST"])
def api_get_user_by_name():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    user = get_user_by_name(name)
    if user is None:
        return jsonify({"message": "用户不存在"}), 404

    avatar_base64 = _load_avatar_base64(user["avatar_url"])
    return jsonify({
        "UserID": user["id"],
        "name": user["name"],
        "avatar_base64": avatar_base64,
        "signature": user["signature"],
    })


## 更新头像
@user_bp.route("/user/<int:user_id>/avatar", methods=["POST"])
def api_set_user_avatar(user_id: int):
    data = request.get_json() or {}
    avatar_base64 = data.get("avatar_base64")
    avatar_url = _save_avatar_base64(avatar_base64)
    if avatar_base64 and not avatar_url:
        return jsonify({"message": "头像格式错误"}), 400
    user = update_avatar_url(user_id, avatar_url)
    if user is None:
        return jsonify({"message": "用户不存在"}), 404
    avatar_base64 = _load_avatar_base64(user["avatar_url"])
    return jsonify({
        "UserID": user["id"],
        "name": user["name"],
        "avatar_base64": avatar_base64,
        "signature": user["signature"],
    })


## 更新个性签名
@user_bp.route("/user/<int:user_id>/signature", methods=["POST"])
def api_update_user_signature(user_id: int):
    data = request.get_json() or {}
    signature = data.get("signature") or ""
    user = update_signature(user_id, signature)
    if user is None:
        return jsonify({"message": "用户不存在"}), 404
    avatar_base64 = _load_avatar_base64(user["avatar_url"])
    return jsonify({
        "UserID": user["id"],
        "name": user["name"],
        "avatar_base64": avatar_base64,
        "signature": user["signature"],
    })


## 用户列表
@user_bp.route("/user/list", methods=["GET"])
def api_list_users():
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 20))
    users = list_users(offset=offset, limit=limit)
    return jsonify([
        {
            "UserID": u["id"],
            "name": u["name"],
            "avatar_base64": _load_avatar_base64(u["avatar_url"]),
            "signature": u["signature"],
        }
        for u in users
    ])
