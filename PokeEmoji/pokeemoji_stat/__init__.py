"""戳一戳统计：按角色排名，给出总次数与每个角色的次数。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.database.models import PokeEmojiStat
from ..pokeemoji_source.types import name_key

sv_stat = SV("戳表情统计")

# 接口走随机直链时不知道具体角色，这类戳一戳统一记到这个名下
RANDOM_LABEL = "随机"

# 聊天窗口放不下太长的榜单，只列前 N 名，其余合并成一行
MAX_ROWS = 15
BAR_BLOCKS = 10


def _merge(rows: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """合并同一个角色的多行（不同 bot、不同写法），次数高的在前。"""
    merged: dict[str, tuple[str, int]] = {}
    for character, count in rows:
        name = character.strip() or RANDOM_LABEL
        key = name_key(name) or name
        shown, total = merged.get(key, (name, 0))
        merged[key] = (shown, total + count)
    return sorted(merged.values(), key=lambda item: (-item[1], item[0]))


def _bar(count: int, top: int) -> str:
    """按最高次数等比缩放的进度条，最少给一格，让上榜的角色都看得见。"""
    if top <= 0:
        return ""
    return "█" * max(1, round(count / top * BAR_BLOCKS))


def format_ranking(rows: list[tuple[str, int]]) -> str:
    ranking = _merge(rows)
    total = sum(count for _, count in ranking)
    if total <= 0:
        return "还没有戳一戳记录，被戳几次再来看看吧。"

    lines = [f"戳一戳统计（共 {total} 次，{len(ranking)} 个角色）"]
    top_count = ranking[0][1]
    for rank, (name, count) in enumerate(ranking[:MAX_ROWS], start=1):
        lines.append(f"{rank}. {name} {_bar(count, top_count)} {count} 次（{count / total * 100:.1f}%）")

    rest = ranking[MAX_ROWS:]
    if rest:
        lines.append(f"…… 其余 {len(rest)} 个角色共 {sum(count for _, count in rest)} 次")
    lines.append("戳一戳、随机表情成功出图都计入。")
    return "\n".join(lines)


async def record_draw(bot_id: str, character: str = "") -> None:
    """记一次出图（戳一戳自动回图 / 随机表情手动抽图）；写失败只写日志，不影响发图。"""
    name = character.strip() or RANDOM_LABEL
    try:
        await PokeEmojiStat.add_count(bot_id, name)
    except Exception as exc:
        logger.warning(f"[PokeEmoji] 出图统计写入失败: character={name!r} {exc}")


@sv_stat.on_command(("戳一戳统计", "戳表情统计", "戳一戳排行"), block=True)
async def show_poke_stat(bot: Bot, ev: Event) -> None:
    try:
        rows = await PokeEmojiStat.get_counters()
    except Exception as exc:
        logger.warning(f"[PokeEmoji] 戳一戳统计读取失败: {exc}")
        await bot.send("读取戳一戳统计失败，稍后再试试吧。")
        return

    await bot.send(format_ranking(rows))
