from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from models import db, Memory, User
from models.models import user_memory

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
