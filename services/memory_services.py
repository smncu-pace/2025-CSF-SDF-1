from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from models import db, Memory, User
from models.models import user_memory
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
    time_range: [start_time, end_time]，支持 datetime 或 ISO8601 字符串
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
            role="Supervisor",
        )
    )

    db.session.commit()
    return memory.id


def delete_memory(memory_id: int, user_id: int) -> Optional[dict]:
    """
    删除回忆：仅当 user_id 是该回忆的 Supervisor 才允许删除。
    成功返回 None；失败返回 {"message": "删除失败"}。
    """
    if not memory_id or not user_id:
        return None

    memory = Memory.query.get(memory_id)
    if memory is None:
        return "没有找到相应的回忆"

    role = db.session.execute(
        select(user_memory.c.role).where(
            user_memory.c.user_id == user_id,
            user_memory.c.memory_id == memory_id,
        )
    ).scalar()

    if role != "Supervisor":
        return "您不是这条回忆的超级管理员，无法删除。请联系超级管理员进行删除。"
    try:
        db.session.execute(
            user_memory.delete().where(user_memory.c.memory_id == memory_id)
        )
        db.session.delete(memory)
        db.session.commit()
        return "成功删除"
    except Exception:
        db.session.rollback()
        return "删除失败"