"""会话级设置：把「戳一戳发哪个角色」交给用户自己切。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.scope import session_scope
from ..utils.setting import get_session_character
from ..pokeemoji_query import split_tokens
from ..pokeemoji_source import EmojiSourceError, get_characters
from ..utils.database.models import PokeEmojiSetting
from ..pokeemoji_config.pokeemoji_config import PokeSettings, load_settings

sv_setting = SV("戳表情设置")

# 这些词表示回到全局默认
RESET_WORDS = {"随机", "默认", "取消", "清除", "关闭", "恢复"}


def _scope_label(ev: Event) -> str:
    return "本群" if ev.group_id else "你"


async def _is_known_character(settings: PokeSettings, character: str) -> bool | None:
    """接口索引或本地目录里有没有这个名字；两边都取不到时返回 None（不误报）。"""
    try:
        items = await get_characters(settings.source)
    except EmojiSourceError:
        return None
    return any(item.name == character for item in items)


@sv_setting.on_command(("表情设置", "戳一戳设置"), block=True)
async def set_poke_emoji(bot: Bot, ev: Event) -> None:
    settings = load_settings()
    if not settings.allow_user_setting:
        await bot.send("当前没有开放自助切换，请联系管理员在网页控制台里改。")
        return

    scope_id = session_scope(ev)
    label = _scope_label(ev)
    tokens = split_tokens(ev.text)

    if not tokens:
        current = await get_session_character(ev, settings.default_character)
        if current:
            await bot.send(f"{label}的戳一戳表情：{current}\n发送「表情设置 随机」可恢复默认。")
        else:
            await bot.send(f"{label}还没设置过戳一戳表情，当前是随机角色。\n发送「表情设置 尤诺」这样切换。")
        return

    if tokens[0] in RESET_WORDS:
        await PokeEmojiSetting.set_character(ev.bot_id, scope_id, "")
        await bot.send(f"已恢复默认，{label}戳一戳重新随机发角色。")
        return

    character = tokens[0]
    await PokeEmojiSetting.set_character(ev.bot_id, scope_id, character)
    # 角色列表可能滞后于接口/本地的变动，所以列表里没有也照存，只提醒一句
    note = ""
    if await _is_known_character(settings, character) is False:
        note = "\n注意：接口与本地目录里暂时都没有这个名字，拼错的话会抽不到图。"
    await bot.send(f"已设置，{label}戳一戳会发「{character}」的表情包。{note}\n发送「表情设置 随机」可恢复默认。")
