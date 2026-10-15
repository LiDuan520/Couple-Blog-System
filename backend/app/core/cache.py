"""
统一缓存失效接口

按 couple 维度失效：
- cache:blog:list:couple:<id>:*   博客列表
- cache:timeline:couple:<id>:*   时间轴
- cache:dashboard:couple:<id>:*  仪表盘
- cache:blog:list:<author_id>:*  v1 旧版（兼容）
"""
from typing import List, Optional
from app.core.redis_client import get_redis


def invalidate_couple_caches(
    couple_id: Optional[int],
    patterns: Optional[List[str]] = None,
    author_ids: Optional[List[int]] = None,
) -> int:
    """失效某 couple 维度的所有缓存

    Args:
        couple_id: 主 couple 标识（v2 维度）
        patterns: 自定义 pattern 列表（可选）
        author_ids: 兼容 v1 时也清掉这些 author 的旧缓存

    Returns:
        删除的 key 数
    """
    r = get_redis()
    final_patterns: List[str] = []
    if patterns:
        final_patterns.extend(patterns)
    if couple_id is not None:
        final_patterns.extend([
            f"cache:blog:list:couple:{couple_id}:*",
            f"cache:timeline:couple:{couple_id}:*",
            f"cache:dashboard:couple:{couple_id}:*",
        ])
    if author_ids:
        for aid in author_ids:
            final_patterns.append(f"cache:blog:list:{aid}:*")
    if not final_patterns:
        return 0
    count = 0
    for pattern in final_patterns:
        for key in r.scan_iter(pattern):
            r.delete(key)
            count += 1
    return count
