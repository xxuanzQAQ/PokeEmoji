"""表情包数据源：优先接口，接口不可用或没有该角色时回落到本地目录。

对外只暴露三件事：`SourceOptions`（配置快照）、`get_random_emoji` / `get_characters`
（带兜底的取图与取角色列表）、`describe_error`（把失败翻成能直接发给用户的话）。
"""

from __future__ import annotations

from dataclasses import dataclass

from gsuid_core.logger import logger

from . import api, local
from .api import DEFAULT_API_BASE, aclose
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


async def get_random_emoji(options: SourceOptions, character: str = "") -> Emoji:
    """先走接口，接口不可用或没有这个角色时回落到本地目录。"""
    name = normalize_character(character)
    if len(name) > MAX_CHARACTER_LEN:
        raise EmojiSourceError("INVALID_CHARACTER", f"角色名最长为 {MAX_CHARACTER_LEN} 个字符")

    api_error: EmojiSourceError | None = None
    if options.enable_api:
        try:
            return await api.fetch_random_emoji(options.api_base, name, options.timeout)
        except EmojiSourceError as exc:
            api_error = exc
            logger.debug(f"[PokeEmoji] 接口取图失败，回落到本地目录: {exc}")

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
            logger.debug(f"[PokeEmoji] 接口角色索引取不到，列表只显示本地: {exc}")

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
