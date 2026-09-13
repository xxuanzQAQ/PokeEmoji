"""表情包数据源：优先接口，接口不可用或没有该角色时回落到本地目录。

接口这一路尽量「少一步」：随机取图时插件只是把接口的直链拼出来交给协议端/QQ 自己去
取（`build_random_url`），插件本身不下载图片、也不先取一次 JSON。只有这两种情况才会
真的发请求：要确认某个具名角色接口里有没有（用带缓存的角色索引），以及接口被判为不可
用后的后台复探。接口不可用期间直接读本地目录，复探成功再切回接口。
"""

from __future__ import annotations

import time
import asyncio
from dataclasses import dataclass

from gsuid_core.logger import logger

from . import api, local
from .api import DEFAULT_API_BASE, aclose, build_random_url
from .local import DEFAULT_EMOJI_DIR
from .types import (
    MAX_CHARACTER_LEN,
    Emoji,
    CharacterItem,
    EmojiSourceError,
    normalize_character,
)

__all__ = [
    "DEFAULT_API_BASE",
    "DEFAULT_EMOJI_DIR",
    "MAX_CHARACTER_LEN",
    "CharacterItem",
    "Emoji",
    "EmojiSourceError",
    "SourceOptions",
    "aclose",
    "build_random_url",
    "describe_error",
    "get_characters",
    "get_random_emoji",
    "normalize_character",
]


@dataclass(frozen=True)
class SourceOptions:
    """取图/取列表时用到的数据源配置。"""

    emoji_dir: str = DEFAULT_EMOJI_DIR
    api_base: str = DEFAULT_API_BASE
    enable_api: bool = True
    timeout: float = 10.0


# 接口被判为不可用后，这段时间直接走本地；期间后台每分钟复探一次
API_DOWN_COOLDOWN = 300.0
API_RECHECK_INTERVAL = 60.0

# 错误 kind → 给用户看的一句话（接口类错误只给结论，细节在日志里）
_SHORT: dict[str, str] = {
    "NO_CHARACTER": "接口里没有这个角色",
    "NO_IMAGE": "接口里这个角色没有图",
    "NO_DIR": "本地目录不可用",
    "EMPTY": "没有可用角色",
    "READ_ERROR": "本地读取失败",
    "NETWORK": "接口连不上",
    "API_ERROR": "接口返回异常",
    "INVALID_CHARACTER": "角色名不合法",
}

_api_down_until: float = 0.0
_last_recheck: float = 0.0
_tasks: set[asyncio.Task] = set()


def _short(error: EmojiSourceError) -> str:
    # 接口类错误只给一句结论，细节（HTTP 状态、原始 msg）留在日志里
    if error.kind in ("NETWORK", "API_ERROR", "NO_CHARACTER", "NO_IMAGE", "EMPTY"):
        return _SHORT[error.kind]
    return error.message or _SHORT.get(error.kind, error.kind)


def _combine(
    api_error: EmojiSourceError | None,
    local_error: EmojiSourceError | None,
) -> EmojiSourceError:
    """把两路的失败合成一个能直接给用户看的错误。"""
    if local_error is None:
        return api_error or EmojiSourceError("EMPTY", "没有可用的角色")
    if api_error is None:
        return local_error

    # 本地是最后一层兜底，提示以本地的问题为主，接口的问题附在后面
    if local_error.kind == "NO_CHARACTER" and api_error.kind == "NO_CHARACTER":
        return local_error
    return EmojiSourceError(local_error.kind, f"{local_error.message}（接口：{_short(api_error)}）")


def _api_is_down() -> bool:
    return time.monotonic() < _api_down_until


def _mark_api_down(reason: object) -> None:
    global _api_down_until
    if not _api_is_down():
        logger.warning(f"[PokeEmoji] 接口不可用，暂时改用本地表情包目录，并每分钟后台复探: {reason}")
    _api_down_until = time.monotonic() + API_DOWN_COOLDOWN


def _mark_api_up() -> None:
    global _api_down_until
    if _api_down_until:
        logger.info("[PokeEmoji] 接口已恢复，继续优先走接口直链")
    _api_down_until = 0.0


async def _recheck_api(options: SourceOptions) -> None:
    try:
        await api.fetch_characters(options.api_base, options.timeout, use_cache=False)
    except EmojiSourceError as exc:
        logger.debug(f"[PokeEmoji] 接口复探仍然失败: {exc}")
        return
    _mark_api_up()


def _schedule_recheck(options: SourceOptions) -> None:
    """后台复探接口；最多每分钟一次，且不占用本次回复的时间。"""
    global _last_recheck
    now = time.monotonic()
    if now - _last_recheck < API_RECHECK_INTERVAL:
        return
    _last_recheck = now
    task = asyncio.create_task(_recheck_api(options))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


def _api_emoji(options: SourceOptions, character: str) -> Emoji:
    return Emoji(source="api", character=character, image=build_random_url(options.api_base, character))


def _matches_role(items: list[CharacterItem], wanted: str) -> bool:
    """接口索引里有没有这个角色；支持角色名与索引里的角色 id。"""
    return any(item.name == wanted or (item.role_id and item.role_id == wanted) for item in items)


async def get_random_emoji(options: SourceOptions, character: str = "") -> Emoji:
    """优先给接口直链；接口不可用、或接口里没有这个角色时回落到本地目录。"""
    name = normalize_character(character)
    if len(name) > MAX_CHARACTER_LEN:
        raise EmojiSourceError("INVALID_CHARACTER", f"角色名最长为 {MAX_CHARACTER_LEN} 个字符")

    api_error: EmojiSourceError | None = None
    if options.enable_api:
        if _api_is_down():
            api_error = EmojiSourceError("NETWORK", "接口暂时被判为不可用")
            _schedule_recheck(options)
        elif not name:
            # 随机角色：不用问接口，直接把随机直链交给协议端
            return _api_emoji(options, "")
        else:
            # 指定角色：先用（带缓存的）索引确认接口有这个角色，没有就交给本地兜底
            try:
                items = await api.fetch_characters(options.api_base, options.timeout)
            except EmojiSourceError as exc:
                api_error = exc
                _mark_api_down(exc)
                _schedule_recheck(options)
            else:
                if _matches_role(items, name):
                    return _api_emoji(options, name)
                api_error = EmojiSourceError("NO_CHARACTER", f"接口里没有这个角色（{name}）")

    try:
        return local.random_emoji(options.emoji_dir, name)
    except EmojiSourceError as exc:
        raise _combine(api_error, exc) from exc


async def get_characters(options: SourceOptions) -> list[CharacterItem]:
    """接口角色索引 ∪ 本地目录；两边都取不到时才抛错。"""
    api_items: list[CharacterItem] = []
    local_items: list[CharacterItem] = []
    api_error: EmojiSourceError | None = None
    local_error: EmojiSourceError | None = None

    if options.enable_api:
        try:
            api_items = await api.fetch_characters(options.api_base, options.timeout)
        except EmojiSourceError as exc:
            api_error = exc
            _mark_api_down(exc)
            logger.debug(f"[PokeEmoji] 接口角色索引取不到，列表只显示本地: {exc}")
        else:
            _mark_api_up()

    try:
        local_items = local.list_characters(options.emoji_dir)
    except EmojiSourceError as exc:
        local_error = exc

    if not api_items and not local_items:
        raise _combine(api_error, local_error)

    api_names = {item.name for item in api_items}
    merged = list(api_items)
    merged.extend(item for item in local_items if item.name not in api_names)
    return merged


def describe_error(error: EmojiSourceError) -> str:
    """把取图错误翻成能直接发给用户的短句。"""
    if error.kind == "INVALID_CHARACTER":
        return error.message or "角色名不合法，换个写法再试试。"
    if error.kind == "NO_DIR":
        return f"{error.message}。请在网页控制台的 PokeEmoji 插件配置里把「本地表情包目录」改对。"
    if error.kind == "EMPTY":
        return "接口和本地都没有可用的角色，检查一下插件配置里的接口地址与本地表情包目录。"
    if error.kind == "NO_IMAGE":
        return f"{error.message}，这个角色暂时没有能发的表情。"
    if error.kind == "READ_ERROR":
        return "读取本地表情包失败，检查一下文件权限后再试试吧。"
    if error.kind == "NETWORK":
        return "接口连不上，本地也没取到图，稍后再试试吧。"
    if error.kind == "API_ERROR":
        return "接口返回异常，本地也没取到图，稍后再试试吧。"
    if error.kind == "NO_CHARACTER":
        return f"{error.message}，发「表情包列表」看看当前可用的角色吧。"
    return "表情包读取异常，稍后再试试吧。"
