"""戳一戳 → 回一张表情包。"""

import time
import random

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from ..utils.meta import meta_str
from ..pokeemoji_api import RandomEmoji, EmojiAPIError, get_random_emoji
from ..utils.setting import get_session_character
from ..pokeemoji_config.pokeemoji_config import PokeSettings, load_settings

sv_poke = SV("戳一戳表情包")

# 会话级冷却：key 为 bot+群/私聊，值用 monotonic 时间，避免受系统时钟调整影响
_cooldown: dict[str, float] = {}
_COOLDOWN_MAX_KEYS = 4096


def _check_cooldown(key: str, seconds: int) -> bool:
    if seconds <= 0:
        return True

    now = time.monotonic()
    if key in _cooldown and now - _cooldown[key] < seconds:
        return False

    _cooldown[key] = now
    if len(_cooldown) > _COOLDOWN_MAX_KEYS:
        expire_before = now - seconds * 4
        for stale in [k for k, v in _cooldown.items() if v < expire_before]:
            del _cooldown[stale]
    return True


async def _fetch(settings: PokeSettings, character: str) -> RandomEmoji:
    return await get_random_emoji(
        api_key=settings.api_key,
        base_url=settings.api_base,
        character=character,
        image_format=settings.image_format,
        timeout=settings.request_timeout,
    )


@sv_poke.on_meta("poke")
async def send_poke_emoji(bot: Bot, ev: Event) -> None:
    settings = load_settings()
    if not settings.enable_poke:
        return

    # 私聊只能戳对方，必然是戳机器人；群聊才按 target_id 判断被戳对象
    # 部分平台不给 target_id/bot_self_id，缺字段时放行，避免整条链路失效
    target_id = meta_str(ev, "target_id")
    if settings.only_poke_bot and ev.group_id and target_id and ev.bot_self_id and target_id != ev.bot_self_id:
        return

    if settings.probability < 100 and random.randint(1, 100) > settings.probability:
        return

    session_key = f"{ev.bot_id}:{ev.group_id or ev.user_id}"
    if not _check_cooldown(session_key, settings.cooldown_seconds):
        return

    # 本会话设置优先；用户没设过或管理员关了自助切换时回落到全局默认角色
    character = settings.default_character
    if settings.allow_user_setting:
        character = await get_session_character(ev, settings.default_character)

    try:
        emoji = await _fetch(settings, character)
    except EmojiAPIError as exc:
        if not (character and exc.status == 404):
            logger.warning(f"[PokeEmoji] 没有取到可用表情包: character={character!r} {exc}")
            return
        # 配置的角色抽不到图（改名 / 没有该格式）时回落随机，别让戳一戳没了反应
        logger.warning(f"[PokeEmoji] 角色 {character!r} 抽不到图，回落随机角色: {exc}")
        try:
            emoji = await _fetch(settings, "")
        except EmojiAPIError as retry_exc:
            logger.warning(f"[PokeEmoji] 随机角色也取不到表情包: {retry_exc}")
            return

    # 图片是公开直链，不要把 API Key 一起发过去
    await bot.send(MessageSegment.image(emoji.url))
