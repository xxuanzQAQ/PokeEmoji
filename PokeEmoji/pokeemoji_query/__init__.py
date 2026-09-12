"""取图命令：随机表情 / 表情包列表。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from ..pokeemoji_api import (
    FORMAT_WEBP,
    CharacterItem,
    EmojiAPIError,
    describe_error,
    get_characters,
    get_random_emoji,
)
from ..utils.setting import get_session_character
from ..pokeemoji_config.pokeemoji_config import PokeSettings, load_settings

sv_query = SV("戳表情包")

# 命令里的格式关键词，解析后覆盖配置里的默认格式
FORMAT_ALIASES: dict[str, str] = {
    "webp": FORMAT_WEBP,
    "原图": "original",
    "original": "original",
}


def split_tokens(text: str) -> list[str]:
    """把中英文逗号也当分隔符，方便「随机表情 尤诺，webp」这种写法。"""
    return text.replace("，", " ").replace(",", " ").split()


def build_character_hint(items: list[CharacterItem], unknown: str) -> str:
    lines = [f"没有找到角色「{unknown}」。"]
    if items:
        names = "、".join(item.name for item in items)
        lines.append(f"当前可用角色：{names}")
    lines.append("也可以直接发「表情包列表」查看当前可用的角色。")
    return "\n".join(lines)


async def _not_found_message(settings: PokeSettings, character: str) -> str:
    """404 时区分两种情况：角色不存在，还是这个角色没有当前格式的表情。"""
    try:
        items = await get_characters(
            api_key=settings.api_key,
            base_url=settings.api_base,
            image_format=settings.image_format,
            timeout=settings.request_timeout,
        )
    except EmojiAPIError:
        items = []

    known = any(item.slug == character or item.name == character for item in items)
    if known:
        return f"「{character}」暂时没有 {settings.image_format} 格式的表情，换个格式再试试。"
    return build_character_hint(items, character)


@sv_query.on_command("随机表情", block=True)
async def send_random_emoji(bot: Bot, ev: Event) -> None:
    settings = load_settings()
    image_format = settings.image_format
    character = ""

    for token in split_tokens(ev.text):
        alias = FORMAT_ALIASES.get(token.lower())
        if alias:
            image_format = alias
            continue
        if character:
            await bot.send("一次只能指定一个角色，发「表情包列表」看看可用的角色吧。")
            return
        character = token

    # 命令里没写角色时，用本会话设置（或全局默认角色）
    if not character and settings.allow_user_setting:
        character = await get_session_character(ev, settings.default_character)
    elif not character:
        character = settings.default_character

    try:
        emoji = await get_random_emoji(
            api_key=settings.api_key,
            base_url=settings.api_base,
            character=character,
            image_format=image_format,
            timeout=settings.request_timeout,
        )
    except EmojiAPIError as exc:
        if exc.status == 404 and character:
            await bot.send(await _not_found_message(settings, character))
            return
        await bot.send(describe_error(exc))
        return

    await bot.send(MessageSegment.image(emoji.url))


@sv_query.on_fullmatch(("表情包列表", "表情包分类"), block=True)
async def list_characters(bot: Bot, ev: Event) -> None:
    settings = load_settings()
    try:
        items = await get_characters(
            api_key=settings.api_key,
            base_url=settings.api_base,
            image_format=settings.image_format,
            timeout=settings.request_timeout,
        )
    except EmojiAPIError as exc:
        await bot.send(describe_error(exc))
        return

    if not items:
        await bot.send("接口暂时没有返回可用的角色，稍后再试试吧。")
        return

    names = "、".join(item.name for item in items)
    await bot.send(f"当前可用角色（{len(items)} 个）：\n{names}")
