"""PokeEmoji：戳一戳回复一张表情包（接口优先，本地兜底）。"""

from gsuid_core.sv import Plugins
from gsuid_core.server import on_core_shutdown

Plugins(
    name="PokeEmoji",
    force_prefix=["ww", "WW"],
    allow_empty_prefix=True,
    alias=["pokeemoji", "戳一戳表情"],
)

from . import (  # noqa: E402
    pokeemoji_help,
    pokeemoji_poke,
    pokeemoji_query,
    pokeemoji_config,
    pokeemoji_source,
    pokeemoji_setting,
)
from .pokeemoji_source import aclose  # noqa: E402


@on_core_shutdown
async def _close_shared_http() -> None:
    """core 退出前关掉共享的 HTTP 连接池。"""
    await aclose()
