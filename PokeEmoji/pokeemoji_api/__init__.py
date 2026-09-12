"""随机表情接口客户端包。"""

from .wuwa_emoji import (
    API_BASE,
    FORMAT_WEBP,
    FORMAT_ORIGINAL,
    MAX_CHARACTER_LEN,
    RandomEmoji,
    CharacterItem,
    EmojiAPIError,
    EmojiCharacter,
    request_json,
    describe_error,
    get_characters,
    get_random_emoji,
    normalize_format,
    normalize_character,
)

__all__ = [
    "API_BASE",
    "FORMAT_ORIGINAL",
    "FORMAT_WEBP",
    "MAX_CHARACTER_LEN",
    "CharacterItem",
    "EmojiAPIError",
    "EmojiCharacter",
    "RandomEmoji",
    "describe_error",
    "get_characters",
    "get_random_emoji",
    "normalize_character",
    "normalize_format",
    "request_json",
]
