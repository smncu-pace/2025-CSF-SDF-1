from __future__ import annotations

import base64
import os
from datetime import datetime
from typing import Iterable, List, Optional

from models import db, Memory, Picture, User, Message
from models.models import user_memory, user_message
from sqlalchemy import select

# 转化成datetime 格式
def _parse_time(value) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None

# 回忆预览信息显示
def _serialize_memory_preview(memory: Memory) -> dict:
    return {
        "title": memory.title,
        "time": memory.start_time.isoformat() if memory.start_time else None,
        "picture": memory.cover_url,
        "MemoryID": memory.id,
    }

# 神秘！
def _avatar_base64(avatar_url: Optional[str]) -> Optional[str]:
    if not avatar_url:
        return None
    if avatar_url.startswith("data:"):
        parts = avatar_url.split(",", 1)
        return parts[1] if len(parts) == 2 else None
    if os.path.isfile(avatar_url):
        with open(avatar_url, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    return None

# 提取出该用户的所有的memory
def _visible_memories_query(user_id: int):
    return (
        Memory.query.join(user_memory, Memory.id == user_memory.c.memory_id)
        .filter(user_memory.c.user_id == user_id)
    )


def query_memories_by_time(user_id: int, time_value) -> List[dict]:
    """
    按开始时间顺序选取 10 条用户可见回忆。
    time_value: datetime | ISO8601 str | None
    """
    time_dt = _parse_time(time_value)
    query = _visible_memories_query(user_id)
    if time_dt is not None:
        query = query.filter(Memory.start_time >= time_dt)

    memories = (
        query.order_by(Memory.start_time.asc())
        .limit(10)
        .all()
    )
    return [_serialize_memory_preview(m) for m in memories]


def _members_of_memory(memory: Memory) -> List[int]:
    return sorted([u.id for u in memory.users])


def query_memories_by_members_exact(user_id: int, members: Iterable[int]) -> List[dict]:
    """
    只包含所有 targetIDs 的回忆（可见用户集合 == targetIDs）。
    """
    target_ids = sorted({int(x) for x in members})
    if not target_ids:
        return []

    memories = _visible_memories_query(user_id).all()
    matched = []
    for memory in memories:
        if _members_of_memory(memory) == target_ids:
            matched.append(memory)

    matched.sort(key=lambda m: m.start_time or datetime.min)
    return [_serialize_memory_preview(m) for m in matched[:10]]


def query_memories_by_members_include(user_id: int, members: Iterable[int]) -> List[dict]:
    """
    包含所有 targetIDs 的回忆（可见用户集合 ⊇ targetIDs）。
    """
    target_set = {int(x) for x in members}
    if not target_set:
        return []

    memories = _visible_memories_query(user_id).all()
    matched = []
    for memory in memories:
        mem_set = set(_members_of_memory(memory))
        if target_set.issubset(mem_set):
            matched.append(memory)

    matched.sort(key=lambda m: m.start_time or datetime.min)
    return [_serialize_memory_preview(m) for m in matched[:10]]


def query_favorite_memories(user_id: int) -> List[dict]:
    """
    按开始时间顺序选取个人收藏。
    """
    memories = (
        _visible_memories_query(user_id)
        .filter(user_memory.c.is_favorite.is_(True))
        .order_by(Memory.start_time.asc())
        .all()
    )
    return [_serialize_memory_preview(m) for m in memories]


def query_memories_on_this_day(user_id: int, time_value) -> List[dict]:
    """
    往年今日查找：与 time-1y 同月同日的回忆。
    """
    time_dt = _parse_time(time_value)
    if time_dt is None:
        return []

    target_date = time_dt.replace(year=time_dt.year - 1)
    memories = _visible_memories_query(user_id).all()
    matched = []
    for memory in memories:
        if not memory.start_time:
            continue
        start = memory.start_time
        if (
            start.month == target_date.month
            and start.day == target_date.day
            and start.year <= target_date.year
        ):
            matched.append(memory)

    matched.sort(key=lambda m: m.start_time or datetime.min)
    return [_serialize_memory_preview(m) for m in matched]


def create_memory(
    user_id: int,
    title: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    location: str | None = None,
    description: str | None = None,
    cover_url: str | None = None,
) -> int:
    """
    新建回忆并绑定用户。
    """
    if not user_id or not title:
        raise ValueError("user_id and title are required")

    user = User.query.get(user_id)
    if user is None:
        raise ValueError("user not found")

    memory = Memory(
        title=title,
        location=location,
        description=description,
        start_time=start_time,
        end_time=end_time,
        creator_id=user_id,
        cover_url=cover_url,
    )
    db.session.add(memory)
    db.session.flush()

    db.session.execute(
        user_memory.insert().values(
            user_id=user_id,
            memory_id=memory.id,
            role="Owner",
        )
    )

    db.session.commit()
    return memory.id


def delete_memory(memory_id: int, user_id: int) -> Optional[dict]:
    """
    删除回忆：仅当 user_id 是该回忆的 Owner 才允许删除。
    成功返回 None；失败返回 {"message": "删除失败"}。
    """
    if not memory_id or not user_id:
        return {"message": "删除失败"}

    memory = Memory.query.get(memory_id)
    if memory is None:
        return {"message": "删除失败"}

    role = db.session.execute(
        select(user_memory.c.role).where(
            user_memory.c.user_id == user_id,
            user_memory.c.memory_id == memory_id,
        )
    ).scalar()

    if role != "Owner":
        return {"message": "您不是此回忆的拥有者，无法删除。"}
    try:
        db.session.execute(
            user_memory.delete().where(user_memory.c.memory_id == memory_id)
        )
        db.session.delete(memory)
        db.session.commit()
        return {"message": "删除成功"}
    except Exception:
        db.session.rollback()
        return {"message": "删除失败"}


def get_memory_detail(memory_id: int) -> Optional[dict]:
    """
    获取回忆详情参数信息。
    """
    memory = Memory.query.get(memory_id)
    if memory is None:
        return None

    owner = User.query.get(memory.creator_id) if memory.creator_id else None
    users_count = db.session.execute(
        select(db.func.count())
        .select_from(user_memory)
        .where(user_memory.c.memory_id == memory_id)
    ).scalar()
    pictures_count = Picture.query.filter_by(memory_id=memory_id).count()

    return {
        "title": memory.title,
        "location": memory.location,
        "description": memory.description,
        "Owner": owner.id if owner else None,
        "Starttime": memory.start_time.isoformat() if memory.start_time else None,
        "Endtime": memory.end_time.isoformat() if memory.end_time else None,
        "usersnumber": int(users_count or 0),
        "picturesnumber": pictures_count
    }


def update_memory_basic(
    user_id: int,
    memory_id: int,
    title: str | None = None,
    location: str | None = None,
    description: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    cover_url: str | None = None,
) -> Optional[dict]:
    """
    修改回忆基本参数，并通知该回忆下所有用户。
    """
    memory = Memory.query.get(memory_id)
    if memory is None:
        return {"message": "编辑失败"}

    role = db.session.execute(
        select(user_memory.c.role).where(
            user_memory.c.user_id == user_id,
            user_memory.c.memory_id == memory_id,
        )
    ).scalar()
    if role != "Owner":
        return {"message": "编辑失败"}

    if title is not None:
        memory.title = title
    if location is not None:
        memory.location = location
    if description is not None:
        memory.description = description
    if start_time is not None:
        memory.start_time = start_time
    if end_time is not None:
        memory.end_time = end_time
    if cover_url is not None:
        memory.cover_url = cover_url

    try:
        actor = User.query.get(user_id)
        actor_name = actor.name if actor else "用户"
        msg_text = f"用户{actor_name}修改了回忆《{memory.title}》的信息，快来看看吧～"
        message = Message(
            text=msg_text,
            type="memory",
            link_id=memory.id,
            title=memory.title,
        )
        db.session.add(message)
        db.session.flush()

        user_ids = (
            db.session.execute(
                select(user_memory.c.user_id).where(
                    user_memory.c.memory_id == memory_id
                )
            )
            .scalars()
            .all()
        )
        for uid in user_ids:
            db.session.execute(
                user_message.insert().values(
                    user_id=uid,
                    message_id=message.id,
                    is_read=False,
                )
            )

        db.session.commit()
        return None
    except Exception:
        db.session.rollback()
        return {"message": "编辑失败"}


def get_memory_members(memory_id: int) -> Optional[dict]:
    """
    查看回忆的人员名单：Owner/monitor/user。
    """
    if not memory_id:
        return None

    rows = db.session.execute(
        select(user_memory.c.user_id, user_memory.c.role).where(
            user_memory.c.memory_id == memory_id
        )
    ).all()
    if not rows:
        return None

    owner_id = None
    monitors: List[int] = []
    users: List[int] = []

    for uid, role in rows:
        if role == "Owner":
            owner_id = uid
        elif role == "monitor":
            monitors.append(uid)
        else:
            users.append(uid)

    return {
        "Owner": owner_id,
        "Editors": monitors,
        "Users": users,
    }



def request_add_members(
    user_id: int,
    memory_id: int,
    members: Iterable[int],
) -> Optional[dict]:
    """
    添加人员（发送请求）：仅允许 monitor 或 owner 角色发起。
    """
    if not memory_id or not user_id:
        return {"message": "参数错误"}

    memory = Memory.query.get(memory_id)
    if memory is None:
        return {"message": "回忆不存在"}

    role = db.session.execute(
        select(user_memory.c.role).where(
            user_memory.c.user_id == user_id,
            user_memory.c.memory_id == memory_id,
        )
    ).scalar()
    if role == "user":
        return {"message": "只有管理员才能添加人员，快去联系ta们吧～"}

    target_ids = {int(x) for x in members}
    if not target_ids:
        return {"message": "成员列表为空"}

    valid_ids = (
        User.query.filter(User.id.in_(target_ids))
        .with_entities(User.id)
        .all()
    )
    valid_ids = {uid for (uid,) in valid_ids}
    if not valid_ids:
        return {"message": "成员不存在"}


    actor = User.query.get(user_id)
    actor_name = actor.name if actor else "用户"
    msg_text = f"{actor_name} 邀请你加入回忆《{memory.title}》，请确认是否加入。"
    message = Message(
        text=msg_text,
        type="memory",
        link_id=memory.id,
        title=memory.title,
    )
    db.session.add(message)
    db.session.flush()

    for uid in valid_ids:
        db.session.execute(
            user_message.insert().values(
                user_id=uid,
                message_id=message.id,
                is_read=False,
            )
        )

    db.session.commit()
    return None


def add_member_to_memory(user_id: int, memory_id: int) -> Optional[dict]:
    """
    添加用户到回忆，并通知其他成员。
    """
    if not memory_id or not user_id:
        return {"message": "参数错误"}

    memory = Memory.query.get(memory_id)
    if memory is None:
        return {"message": "回忆不存在"}

    exists = db.session.execute(
        select(user_memory.c.user_id).where(
            user_memory.c.user_id == user_id,
            user_memory.c.memory_id == memory_id,
        )
    ).scalar()
    if exists:
        return {"message": "用户已在回忆中"}

    db.session.execute(
        user_memory.insert().values(
            user_id=user_id,
            memory_id=memory_id,
            role="user",
        )
    )
    actor = User.query.get(user_id)
    actor_name = actor.name if actor else "用户"
    msg_text = f"{actor_name} 加入了回忆《{memory.title}》，快来看看吧～"
    message = Message(
        text=msg_text,
        type="memory",
        link_id=memory.id,
        title=memory.title,
    )
    db.session.add(message)
    db.session.flush()

    member_ids = (
        db.session.execute(
            select(user_memory.c.user_id).where(
                user_memory.c.memory_id == memory_id,
                user_memory.c.user_id != user_id,
            )
        )
        .scalars()
        .all()
    )
    for uid in member_ids:
        db.session.execute(
            user_message.insert().values(
                user_id=uid,
                message_id=message.id,
                is_read=False,
            )
        )

    db.session.commit()
    return None


def add_monitors(
    user_id: int,
    memory_id: int,
    members: Iterable[int],
) -> Optional[dict]:
    """
    升级成员为管理员（monitor）：仅 Owner 可操作。
    """
    if not memory_id or not user_id:
        return {"message": "参数错误"}

    memory = Memory.query.get(memory_id)
    if memory is None:
        return {"message": "回忆不存在"}

    role = db.session.execute(
        select(user_memory.c.role).where(
            user_memory.c.user_id == user_id,
            user_memory.c.memory_id == memory_id,
        )
    ).scalar()
    if role != "Owner":
        return {"message": "只有 Owner 才能添加管理员"}

    target_ids = {int(x) for x in members}
    if not target_ids:
        return {"message": "成员列表为空"}
    
    actor = User.query.get(user_id)
    actor_name = actor.name if actor else "用户"
    msg_text = f"你已被{actor_name}设为回忆《{memory.title}》的管理员。"
    message = Message(
        text=msg_text,
        type="memory",
        link_id=memory.id,
        title=memory.title,
    )
    db.session.add(message)
    db.session.flush()

    for uid in target_ids:
        db.session.execute(
            user_memory.update()
            .where(
                user_memory.c.user_id == uid,
                user_memory.c.memory_id == memory_id,
            )
            .values(role="monitor")
        )
        db.session.execute(
            user_message.insert().values(
                user_id=uid,
                message_id=message.id,
                is_read=False,
            )
        )

    db.session.commit()
    return None


def remove_members(
    user_id: int,
    memory_id: int,
    members: Iterable[int],
) -> Optional[dict]:
    """
    删除成员：仅 monitor 或 owner 可操作。
    """
    if not memory_id or not user_id:
        return {"message": "参数错误"}

    memory = Memory.query.get(memory_id)
    if memory is None:
        return {"message": "回忆不存在"}

    role = db.session.execute(
        select(user_memory.c.role).where(
            user_memory.c.user_id == user_id,
            user_memory.c.memory_id == memory_id,
        )
    ).scalar()
    if role == "user":
        return {"message": "只有回忆拥有者或管理员才能删除人员"}

    target_ids = {int(x) for x in members}
    if not target_ids:
        return {"message": "成员列表为空"}

    msg_text = f"你已被移出回忆《{memory.title}》。"
    message = Message(
        text=msg_text,
        type="memory",
        link_id=memory.id,
        title=memory.title,
    )
    db.session.add(message)
    db.session.flush()

    db.session.execute(
        user_memory.delete().where(
            user_memory.c.memory_id == memory_id,
            user_memory.c.user_id.in_(target_ids),
        )
    )

    for uid in target_ids:
        db.session.execute(
            user_message.insert().values(
                user_id=uid,
                message_id=message.id,
                is_read=False,
            )
        )

    db.session.commit()
    return None


def remove_monitors(
    user_id: int,
    memory_id: int,
    members: Iterable[int],
) -> Optional[dict]:
    """
    删除管理员（monitor）：仅 Owner 可操作。
    """
    if not memory_id or not user_id:
        return {"message": "参数错误"}

    memory = Memory.query.get(memory_id)
    if memory is None:
        return {"message": "回忆不存在"}

    role = db.session.execute(
        select(user_memory.c.role).where(
            user_memory.c.user_id == user_id,
            user_memory.c.memory_id == memory_id,
        )
    ).scalar()
    if role != "Owner":
        return {"message": "只有 Owner 才能删除管理员"}

    target_ids = {int(x) for x in members}
    if not target_ids:
        return {"message": "成员列表为空"}

    msg_text = f"你已被取消回忆《{memory.title}》的管理员权限。"
    message = Message(
        text=msg_text,
        type="memory",
        link_id=memory.id,
        title=memory.title,
    )
    db.session.add(message)
    db.session.flush()

    db.session.execute(
        user_memory.update()
        .where(
            user_memory.c.memory_id == memory_id,
            user_memory.c.user_id.in_(target_ids),
        )
        .values(role="user")
    )

    for uid in target_ids:
        db.session.execute(
            user_message.insert().values(
                user_id=uid,
                message_id=message.id,
                is_read=False,
            )
        )

    db.session.commit()
    return None
