import os
from dataclasses import dataclass

from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsIntConfig,
    GsStrConfig,
    GsBoolConfig,
)
from gsuid_core.utils.plugins_config.gs_config import StringConfig

from .config_default import CONFIG_DEFAULT
from ..pokeemoji_source import DEFAULT_API_BASE, DEFAULT_EMOJI_DIR, SourceOptions
from ..utils.resource_path import CONFIG_PATH

# 不想把地址/路径写进配置文件时，可以用环境变量兜底（方便容器化部署）
API_BASE_ENV = "POKEEMOJI_API_BASE"
EMOJI_DIR_ENV = "POKEEMOJI_EMOJI_DIR"

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


def _str_or_env(key: str, default: str, env: str) -> str:
    return _str(key, default).strip() or os.environ.get(env, "").strip() or default


def _api_base() -> str:
    # 旧版配置里可能还留着已下线的站点接口地址，这种值直接用新默认值
    value = _str_or_env("api_base", DEFAULT_API_BASE, API_BASE_ENV)
    return DEFAULT_API_BASE if "emoji.wuwa.games" in value.lower() else value


@dataclass(frozen=True)
class PokeSettings:
    """一次调用期间生效的配置快照，避免同一逻辑里反复读配置。"""

    enable_poke: bool
    only_poke_bot: bool
    allow_user_setting: bool
    probability: int
    cooldown_seconds: int
    enable_api: bool
    api_base: str
    emoji_dir: str
    request_timeout: int
    default_character: str

    @property
    def source(self) -> SourceOptions:
        """交给 pokeemoji_source 的数据源配置：接口优先、本地兜底。"""
        return SourceOptions(
            emoji_dir=self.emoji_dir,
            api_base=self.api_base,
            enable_api=self.enable_api,
            timeout=float(self.request_timeout),
        )


def load_settings() -> PokeSettings:
    return PokeSettings(
        enable_poke=_bool("enable_poke", True),
        only_poke_bot=_bool("only_poke_bot", True),
        allow_user_setting=_bool("allow_user_setting", True),
        probability=_bounded_int("poke_probability", 100, 0, 100),
        cooldown_seconds=_bounded_int("cooldown_seconds", 10, 0, 600),
        enable_api=_bool("enable_api", True),
        api_base=_api_base(),
        emoji_dir=_str_or_env("emoji_dir", DEFAULT_EMOJI_DIR, EMOJI_DIR_ENV),
        request_timeout=_bounded_int("request_timeout", 10, 1, 120),
        default_character=_str("default_character", "").strip(),
    )
