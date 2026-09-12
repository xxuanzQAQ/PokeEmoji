"""会话级设置：把「戳一戳发哪类表情」交给用户自己切。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.scope import session_scope
from ..pokeemoji_api import resolve_filter, get_facet_groups
from ..utils.setting import get_session_filter
from ..pokeemoji_query import build_keyword_hint
from ..utils.database.models import PokeEmojiSetting
from ..pokeemoji_config.pokeemoji_config import load_settings

sv_setting = SV("戳表情设置")

# 这些词表示回到全局默认
RESET_WORDS = {"随机", "默认", "取消", "清除", "关闭", "恢复"}


def _scope_label(ev: Event) -> str:
    return "本群" if ev.group_id else "你"


@sv_setting.on_command(("表情设置", "戳一戳设置"), block=True)
async def set_poke_emoji(bot: Bot, ev: Event) -> None:
    settings = load_settings()
    if not settings.allow_user_setting:
        await bot.send("当前没有开放自助切换，请联系管理员在网页控制台里改。")
        return

    scope_id = session_scope(ev)
    label = _scope_label(ev)
    tokens = ev.text.replace("，", " ").replace(",", " ").split()

    if not tokens:
        current = await get_session_filter(ev, settings.default_filter)
        if current:
            await bot.send(f"{label}的戳一戳表情：{current}\n发送「表情设置 随机」可恢复默认。")
        else:
            await bot.send(f"{label}还没设置过戳一戳表情，当前是随机发送。\n发送「表情设置 尤诺」这样切换。")
        return

    if tokens[0] in RESET_WORDS:
        await PokeEmojiSetting.set_filter(ev.bot_id, scope_id, "")
        await bot.send(f"已恢复默认，{label}戳一戳重新随机发送表情。")
        return

    groups = await get_facet_groups(timeout=settings.request_timeout)
    resolved = resolve_filter(tokens[0], groups)
    if not resolved:
        await bot.send(build_keyword_hint(groups, tokens[0]))
        return

    await PokeEmojiSetting.set_filter(ev.bot_id, scope_id, resolved)
    await bot.send(f"已设置，{label}戳一戳会发「{resolved}」的表情包。\n发送「表情设置 随机」可恢复默认。")
