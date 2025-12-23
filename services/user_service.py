# -*- coding: utf-8 -*-
"""
User-related业务逻辑，基于 SQLAlchemy ORM。
"""
from typing import Optional, List, Dict

from models import db
from models.models import User


def _user_to_dict(user: User) -> Dict:
    return {
        "id": user.id,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "signature": user.signature,
    }


def create_user(name: str, password: str, avatar_url: Optional[str] = None, signature: str = "") -> Dict:
    """创建用户，name 唯一。"""
    user = User(name=name, password=password, avatar_url=avatar_url, signature=signature or "")
    db.session.add(user)
    db.session.commit()
    return _user_to_dict(user)


def authenticate(name: str, password: str) -> Optional[Dict]:
    """简单用户名/明文密码校验，匹配则返回用户字典。"""
    user = User.query.filter_by(name=name).first()
    if not user or user.password != password:
        return None
    return _user_to_dict(user)


def get_user(user_id: int) -> Optional[Dict]:
    user = User.query.get(user_id)
    return _user_to_dict(user) if user else None


def get_user_by_name(name: str) -> Optional[Dict]:
    user = User.query.filter_by(name=name).first()
    return _user_to_dict(user) if user else None


def list_users(offset: int = 0, limit: int = 20) -> List[Dict]:
    users = User.query.order_by(User.id.asc()).offset(offset).limit(limit).all()
    return [_user_to_dict(u) for u in users]


def update_signature(user_id: int, signature: str) -> Optional[Dict]:
    user = User.query.get(user_id)
    if not user:
        return None
    user.signature = signature
    db.session.commit()
    return _user_to_dict(user)


def update_avatar_url(user_id: int, avatar_url: str) -> Optional[Dict]:
    user = User.query.get(user_id)
    if not user:
        return None
    user.avatar_url = avatar_url
    db.session.commit()
    return _user_to_dict(user)
