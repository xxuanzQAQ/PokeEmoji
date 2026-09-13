"""取图命令：随机表情 / 表情包列表。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from ..utils.scope import bot_context
from ..utils.render import render_character_list
from ..pokeemoji_stat import record_draw
from ..pokeemoji_source import (
    BotContext,
    CharacterItem,
    EmojiSourceError,
    describe_error,
    get_characters,
    get_random_emoji,
    find_foreign_owner,
)
from ..pokeemoji_config.pokeemoji_config import PokeSettings, load_settings

sv_query = SV("戳表情包")

# 接口/本地都只有一份原图，没有 webp/原图之分；旧命令里的格式关键词直接忽略，
# 免得「随机表情 尤诺 webp」这类写惯了的老命令被当成两个角色报错。
IGNORED_TOKENS = {"webp", "original", "原图", "gif", "png"}


def split_tokens(text: str) -> list[str]:
    """把中英文逗号也当分隔符，方便「随机表情 尤诺, webp」这种写法。"""
    return text.replace("，", " ").replace(",", " ").split()


def build_character_hint(items: list[CharacterItem], unknown: str) -> str:
    lines = [f"没有找到角色「{unknown}」。"]
    if items:
        names = "、".join(item.name for item in items)
        lines.append(f"当前可用角色：{names}")
    lines.append("也可以直接发「表情包列表」查看当前可用的角色。")
    return "\n".join(lines)


def _format_character(item: CharacterItem) -> str:
    """接口里没有、只在本地区有的角色标一下，方便排查兜底来源。"""
    if item.owner:
        return f"{item.name}({item.count}·专属)"
    return f"{item.name}({item.count}·仅本地)" if item.local_only else f"{item.name}({item.count})"


async def _available_characters(settings: PokeSettings, bot: BotContext) -> list[CharacterItem]:
    """取角色列表；接口和本地都取不到时返回空列表，由调用方决定怎么提示。"""
    try:
        return await get_characters(settings.source, bot)
    except EmojiSourceError:
        return []


@sv_query.on_command("随机表情", block=True)
async def send_random_emoji(bot: Bot, ev: Event) -> None:
    settings = load_settings()
    viewer = bot_context(ev)
    character = ""

    for token in split_tokens(ev.text):
        if token.lower() in IGNORED_TOKENS:
            continue
        if character:
            await bot.send("一次只能指定一个角色，发「表情包列表」看看可用的角色吧。")
            return
        character = token

    try:
        emoji = await get_random_emoji(settings.source, character, viewer)
    except EmojiSourceError as exc:
        if exc.kind == "NO_CHARACTER" and character:
            foreign = find_foreign_owner(settings.source, character, viewer)
            if foreign:
                await bot.send(f"「{character}」是 bot {foreign} 的专属分类，当前 bot 用不了。")
                return
            await bot.send(build_character_hint(await _available_characters(settings, viewer), character))
            return
        await bot.send(describe_error(exc))
        return

    await bot.send(MessageSegment.image(emoji.image))
    # 手动抽图跟戳一戳共用一个榜单：接口直链不带角色名时回落到本次指定的角色
    await record_draw(ev.bot_id, emoji.character or character)


@sv_query.on_fullmatch(("表情包列表", "表情包分类"), block=True)
async def list_characters(bot: Bot, ev: Event) -> None:
    settings = load_settings()
    try:
        items = await get_characters(settings.source, bot_context(ev))
    except EmojiSourceError as exc:
        await bot.send(describe_error(exc))
        return

    await bot.send(MessageSegment.image(await render_character_list(items)))
