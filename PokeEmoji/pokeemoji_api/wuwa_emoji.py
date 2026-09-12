"""emoji.wuwa.games 公开接口客户端。

站点前端用的公开只读端点（Halo 插件 api.emoji.jaspin.top）：

    GET /gallery-feed
        size   1-100，默认 24
        sort   random | download | favorite
        seed   与 cursor 配套，同一次随机分页要带同一个 seed
        cursor 上一页返回的 nextCursor
        filter 可重复，形如 角色/爱弥斯、画师/雾雪（分类名见 facetGroups）
    另有 /archive-catalog、/archive-stats、/packs/{postName} 等端点，本插件只用 gallery-feed。

接口不支持关键词搜索，只能按 facet 精确筛选，因此这里本地维护分类索引。
"""

import time
import random

import httpx
import msgspec

from gsuid_core.logger import logger

API_BASE = "https://emoji.wuwa.games/apis/api.emoji.jaspin.top/v1alpha1"
FEED_PATH = "/gallery-feed"
USER_AGENT = "GsCore-PokeEmoji/1.0"
FACET_CACHE_TTL = 6 * 3600


class EmojiAsset(msgspec.Struct, rename="camel"):
    """gallery-feed 的 items 元素（只声明用得到的字段）。"""

    original_url: str = ""
    preview_url: str = ""
    bytes: int = 0


class FacetEntry(msgspec.Struct, rename="camel"):
    name: str = ""


class FacetGroup(msgspec.Struct, rename="camel"):
    name: str = ""
    entries: list[FacetEntry] = msgspec.field(default_factory=list)


class GalleryFeed(msgspec.Struct, rename="camel"):
    items: list[EmojiAsset] = msgspec.field(default_factory=list)
    facet_groups: list[FacetGroup] = msgspec.field(default_factory=list)


_facet_groups: list[FacetGroup] = []
_facet_ts: float = 0.0


async def request_feed(
    *,
    size: int,
    sort: str,
    filter_key: str = "",
    seed: str = "",
    cursor: str = "",
    timeout: int = 20,
) -> GalleryFeed:
    params: dict[str, str] = {"size": str(size), "sort": sort}
    if filter_key:
        params["filter"] = filter_key
    if seed:
        params["seed"] = seed
    if cursor:
        params["cursor"] = cursor

    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        response = await client.get(f"{API_BASE}{FEED_PATH}", params=params)
        response.raise_for_status()
        return msgspec.json.decode(response.content, type=GalleryFeed)


async def get_facet_groups(*, timeout: int = 20, force: bool = False) -> list[FacetGroup]:
    """分类索引（角色/画师/企划/原设），带内存缓存，随 gallery-feed 一起下发。"""
    global _facet_groups, _facet_ts

    if not force and _facet_groups and time.monotonic() - _facet_ts < FACET_CACHE_TTL:
        return _facet_groups

    feed = await request_feed(size=1, sort="random", timeout=timeout)
    if feed.facet_groups:
        _facet_groups = feed.facet_groups
        _facet_ts = time.monotonic()
        logger.info(f"[PokeEmoji] 分类索引已刷新，共 {len(_facet_groups)} 组")
    return _facet_groups


def resolve_filter(keyword: str, groups: list[FacetGroup]) -> str:
    """把用户输入解析成接口的 filter 值；无法识别时返回空串。"""
    text = keyword.strip()
    if not text:
        return ""

    group_name, separator, entry_name = text.partition("/")
    if separator:
        group_name = group_name.strip()
        entry_name = entry_name.strip()
        for group in groups:
            if group.name == group_name and any(entry.name == entry_name for entry in group.entries):
                return f"{group_name}/{entry_name}"
        return ""

    for group in groups:
        if group.name == text and group.entries:
            return f"{group.name}/{random.choice(group.entries).name}"
        for entry in group.entries:
            if entry.name == text:
                return f"{group.name}/{entry.name}"

    return ""


async def pick_asset(
    *,
    sort_mode: str,
    filter_key: str = "",
    size: int = 30,
    timeout: int = 20,
) -> EmojiAsset | None:
    feed = await request_feed(
        size=size,
        sort=sort_mode,
        filter_key=filter_key,
        timeout=timeout,
    )
    items = [item for item in feed.items if item.original_url or item.preview_url]
    if not items:
        return None
    return random.choice(items)


def pick_image_url(asset: EmojiAsset, image_format: str, auto_webp_bytes: int) -> str:
    """选发送用图片地址；auto 下大图退到 webp 预览，避免动图过大发不出去。"""
    original = asset.original_url or asset.preview_url
    preview = asset.preview_url or asset.original_url

    if image_format == "original":
        return original
    if image_format == "webp":
        return preview
    if asset.bytes and asset.bytes > auto_webp_bytes:
        return preview
    return original
