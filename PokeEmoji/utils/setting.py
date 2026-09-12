from gsuid_core.models import Event

from .scope import session_scope
from .database.models import PokeEmojiSetting


async def get_session_character(ev: Event, fallback: str) -> str:
    """取本会话设置的角色，没设置过就回落到全局默认角色。"""
    stored = await PokeEmojiSetting.get_character(ev.bot_id, session_scope(ev))
    return stored or fallback
