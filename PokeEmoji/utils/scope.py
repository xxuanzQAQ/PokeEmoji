from gsuid_core.models import Event


def session_scope(ev: Event) -> str:
    """会话键：群聊按群、私聊按人，与冷却口径一致。"""
    if ev.group_id:
        return f"group_{ev.group_id}"
    return f"user_{ev.user_id}"
