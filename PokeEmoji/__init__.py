"""PokeEmoji：戳一戳回复一张表情包（emoji.wuwa.games 公开接口）。"""

from gsuid_core.sv import Plugins

Plugins(
    name="PokeEmoji",
    force_prefix=["戳"],
    allow_empty_prefix=True,
    alias=["pokeemoji", "戳一戳表情"],
)

from . import (  # noqa: E402
    pokeemoji_api,
    pokeemoji_help,
    pokeemoji_poke,
    pokeemoji_query,
    pokeemoji_config,
    pokeemoji_setting,
)
