from gsuid_core.models import Event

from ..pokeemoji_source.types import BotContext


def session_scope(ev: Event) -> str:
    """会话键：群聊按群、私聊按人，与冷却口径一致。"""
    if ev.group_id:
        return f"group_{ev.group_id}"
    return f"user_{ev.user_id}"


def bot_context(ev: Event) -> BotContext:
    """当前事件的 bot 身份：bot_id 是适配器名，bot_self_id 是账号（QQ 号等）。"""
    return BotContext(bot_id=ev.bot_id or "", bot_self_id=ev.bot_self_id or "")
