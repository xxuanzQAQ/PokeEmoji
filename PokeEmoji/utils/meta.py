from collections.abc import Mapping

from gsuid_core.models import Event


def meta_str(ev: Event, key: str) -> str:
    """读 meta 事件里的字符串字段；缺失或非字符串时安全归一为空串。"""
    data: Mapping[str, object] = ev.meta_event_data
    if key not in data:
        return ""
    value = data[key]
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)
