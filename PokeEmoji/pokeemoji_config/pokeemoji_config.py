from dataclasses import dataclass

from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsIntConfig,
    GsStrConfig,
    GsBoolConfig,
)
from gsuid_core.utils.plugins_config.gs_config import StringConfig

from .config_default import CONFIG_DEFAULT
from ..utils.resource_path import CONFIG_PATH

CONFIG = StringConfig("PokeEmoji", CONFIG_PATH, CONFIG_DEFAULT)


def _bool(key: str, default: bool) -> bool:
    if key not in CONFIG.config:
        return default
    item: GSC = CONFIG.config[key]
    return item.data if isinstance(item, GsBoolConfig) else default


def _int(key: str, default: int) -> int:
    if key not in CONFIG.config:
        return default
    item: GSC = CONFIG.config[key]
    return item.data if isinstance(item, GsIntConfig) else default


def _bounded_int(key: str, default: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, _int(key, default)))


def _str(key: str, default: str) -> str:
    if key not in CONFIG.config:
        return default
    item: GSC = CONFIG.config[key]
    return item.data if isinstance(item, GsStrConfig) else default


@dataclass(frozen=True)
class PokeSettings:
    """一次调用期间生效的配置快照，避免同一逻辑里反复读配置。"""

    enable_poke: bool
    only_poke_bot: bool
    allow_user_setting: bool
    probability: int
    cooldown_seconds: int
    sort_mode: str
    default_filter: str
    candidate_size: int
    image_format: str
    auto_webp_bytes: int
    request_timeout: int


def load_settings() -> PokeSettings:
    return PokeSettings(
        enable_poke=_bool("enable_poke", True),
        only_poke_bot=_bool("only_poke_bot", True),
        allow_user_setting=_bool("allow_user_setting", True),
        probability=_bounded_int("poke_probability", 100, 0, 100),
        cooldown_seconds=_bounded_int("cooldown_seconds", 10, 0, 600),
        sort_mode=_str("sort_mode", "random"),
        default_filter=_str("default_filter", ""),
        candidate_size=_bounded_int("candidate_size", 30, 1, 100),
        image_format=_str("image_format", "auto"),
        auto_webp_bytes=_bounded_int("auto_webp_bytes", 3145728, 0, 20971520),
        request_timeout=_bounded_int("request_timeout", 20, 1, 120),
    )
