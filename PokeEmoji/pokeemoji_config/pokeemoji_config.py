import os
from dataclasses import dataclass

from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsIntConfig,
    GsStrConfig,
    GsBoolConfig,
)
from gsuid_core.utils.plugins_config.gs_config import StringConfig

from ..pokeemoji_api import API_BASE, normalize_format
from .config_default import CONFIG_DEFAULT
from ..utils.resource_path import CONFIG_PATH

# 不想把密钥写进配置文件时，可以用环境变量兜底（方便容器化部署）
API_KEY_ENV = "POKEEMOJI_API_KEY"

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
    api_key: str
    api_base: str
    default_character: str
    image_format: str
    request_timeout: int


def load_settings() -> PokeSettings:
    return PokeSettings(
        enable_poke=_bool("enable_poke", True),
        only_poke_bot=_bool("only_poke_bot", True),
        allow_user_setting=_bool("allow_user_setting", True),
        probability=_bounded_int("poke_probability", 100, 0, 100),
        cooldown_seconds=_bounded_int("cooldown_seconds", 10, 0, 600),
        api_key=_str("api_key", "").strip() or os.environ.get(API_KEY_ENV, "").strip(),
        api_base=_str("api_base", API_BASE).strip() or API_BASE,
        default_character=_str("default_character", "").strip(),
        image_format=normalize_format(_str("image_format", "original")),
        request_timeout=_bounded_int("request_timeout", 20, 1, 120),
    )
