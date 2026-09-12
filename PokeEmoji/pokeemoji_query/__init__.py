"""取图命令：随机表情 / 表情包分类。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from ..pokeemoji_api import (
    FacetGroup,
    pick_asset,
    pick_image_url,
    resolve_filter,
    get_facet_groups,
)
from ..utils.setting import get_session_filter
from ..pokeemoji_config.pokeemoji_config import load_settings

sv_query = SV("戳表情包")

SORT_ALIASES: dict[str, str] = {
    "随机": "random",
    "随机图": "random",
    "下载榜": "download",
    "下载最多": "download",
    "热门": "download",
    "收藏榜": "favorite",
    "收藏最多": "favorite",
}

HINT_ENTRIES_PER_GROUP = 20


def build_keyword_hint(groups: list[FacetGroup], unknown: str) -> str:
    lines = [f"没有找到「{unknown}」相关的分类。"]
    for group in groups[:2]:
        names = "、".join(entry.name for entry in group.entries[:HINT_ENTRIES_PER_GROUP])
        if names:
            lines.append(f"{group.name}：{names}")
    lines.append("用「表情包分类」可以看全部关键词。")
    return "\n".join(lines)


@sv_query.on_command("随机表情", block=True)
async def send_random_emoji(bot: Bot, ev: Event) -> None:
    settings = load_settings()
    tokens = ev.text.replace("，", " ").replace(",", " ").split()
    sort_mode = settings.sort_mode
    filter_key = settings.default_filter
    has_filter = any(token not in SORT_ALIASES for token in tokens)
    if not has_filter:
        filter_key = await get_session_filter(ev, filter_key)

    groups = await get_facet_groups(timeout=settings.request_timeout) if has_filter else []
    for token in tokens:
        if token in SORT_ALIASES:
            sort_mode = SORT_ALIASES[token]
            continue

        resolved = resolve_filter(token, groups)
        if not resolved:
            await bot.send(build_keyword_hint(groups, token))
            return
        filter_key = resolved

    asset = await pick_asset(
        sort_mode=sort_mode,
        filter_key=filter_key,
        size=settings.candidate_size,
        timeout=settings.request_timeout,
    )
    if asset is None:
        await bot.send("这个分类下暂时没有表情包，换个关键词试试吧。")
        return

    await bot.send(MessageSegment.image(pick_image_url(asset, settings.image_format, settings.auto_webp_bytes)))


@sv_query.on_fullmatch("表情包分类", block=True)
async def list_facets(bot: Bot, ev: Event) -> None:
    settings = load_settings()
    groups = await get_facet_groups(timeout=settings.request_timeout)
    if not groups:
        await bot.send("暂时取不到分类列表，稍后再试试吧。")
        return

    lines = ["可用筛选项（「表情设置 关键词」切换本会话的戳一戳表情）："]
    for group in groups:
        names = "、".join(entry.name for entry in group.entries)
        if names:
            lines.append(f"{group.name}：{names}")
    await bot.send("\n".join(lines))
