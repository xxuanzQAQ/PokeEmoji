from gsuid_core.models import Event

from .scope import session_scope
from .database.models import PokeEmojiSetting


async def get_session_filter(ev: Event, fallback: str) -> str:
    """取本会话设置的筛选，没设置过就回落到全局默认。"""
    stored = await PokeEmojiSetting.get_filter(ev.bot_id, session_scope(ev))
    return stored or fallback
