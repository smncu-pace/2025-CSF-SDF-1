from typing import List, Any


def paginate_sorted(items: List[Any], l: int, r: int) -> List[Any]:
    """
    按你说的“第 [l,r] 条”：
    这里采用 **1-based 闭区间**，更符合“第几条”的语感。
    """
    if l < 1 or r < l:
        return []
    # 转 0-based
    start = l - 1
    end = r       # Python 切片右开区间
    return items[start:end]
