"""随机表情接口客户端（接口优先里的「优先」那一路，地址由 api_base 配置）。

接口只有两个路由：

    GET <base>/         角色索引：data.roles[] 带 id / name / emojiCount / packCount
    GET <base>/random   随机取一张；role=角色名或角色 id，format=json 返回 JSON 结果

响应统一是 `{code, msg, data}`：`code == 0` 才是成功，其它都是业务错误（HTTP 状态
仍是 200，例如角色不存在时返回 `{"code":1,"msg":"没有匹配的表情"}`），所以除 HTTP
状态码外还得看 body 里的 code。`role` 支持精确的角色名或索引里的 id，逗号分隔多个
角色时会在这几个角色里随机。
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from .types import Emoji, CharacterItem, EmojiSourceError

DEFAULT_API_BASE = "https://cdn.anyul.cn/emoji-api"
USER_AGENT = "GsCore-PokeEmoji/1.1"

# 角色索引约 40KB，且站点侧更新很慢（几小时级），缓存一会儿能省下不少流量
CHARACTER_CACHE_TTL = 600.0

# 每次新建 client 都要重做 TCP + TLS 握手，这里做成进程内共享的长连接池：
# client 懒创建（在真正发起请求的事件循环里建），请求之间复用连接与 TLS 会话。
DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)
MAX_CONNECTIONS = 32
MAX_KEEPALIVE_CONNECTIONS = 8

_client: httpx.AsyncClient | None = None
_characters_cache: dict[str, tuple[float, list[CharacterItem]]] = {}


def _get_client() -> httpx.AsyncClient:
    """取共享 client；没建过或已被关掉时现建一个。"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            limits=httpx.Limits(
                max_connections=MAX_CONNECTIONS,
                max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
            ),
        )
    return _client


async def aclose() -> None:
    """关闭共享 client，供插件在 core 退出时调用；重复调用无副作用。"""
    global _client
    client, _client = _client, None
    if client is not None and not client.is_closed:
        await client.aclose()


def _endpoint(api_base: str, path: str) -> str:
    return f"{api_base.strip().rstrip('/')}{path}"


def _absolute(api_base: str, url: str) -> str:
    """接口正常返回绝对直链；万一是相对路径就按接口地址补全。"""
    return str(httpx.URL(_endpoint(api_base, "")).join(url)) if url.startswith("/") else url


def _decode(content: bytes) -> dict[str, Any] | None:
    try:
        payload = json.loads(content)
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


async def _get_data(url: str, params: dict[str, str] | None, timeout: float) -> dict[str, Any]:
    """发一次 GET 并拆开 `{code, msg, data}`，失败统一抛 EmojiSourceError。

    业务错误不一定用 200 回，例如角色不存在时是 HTTP 404 +
    `{"code":1,"msg":"没有匹配的表情"}`；所以先看 body 里的 code/msg，再退回 HTTP 状态码。
    """
    client = _get_client()
    try:
        response = await client.get(url, params=params, timeout=timeout)
    except httpx.HTTPError as exc:
        raise EmojiSourceError("NETWORK", f"请求接口失败: {exc}") from exc

    payload = _decode(response.content)
    if payload is None:
        raise EmojiSourceError("API_ERROR", f"接口返回了无法解析的内容（HTTP {response.status_code}）")

    code = payload.get("code")
    if code != 0:
        message = str(payload.get("msg") or payload.get("message") or f"接口返回 HTTP {response.status_code}")
        if "没有匹配" in message or "不存在" in message:
            raise EmojiSourceError("NO_CHARACTER", f"接口里没有这个角色（{message}）")
        raise EmojiSourceError("API_ERROR", f"{message}（HTTP {response.status_code}）")

    if response.status_code != 200:
        raise EmojiSourceError("API_ERROR", f"接口返回 HTTP {response.status_code}")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise EmojiSourceError("API_ERROR", "接口没有返回数据")
    return data


async def fetch_characters(
    api_base: str = DEFAULT_API_BASE,
    timeout: float = 10.0,
    *,
    use_cache: bool = True,
) -> list[CharacterItem]:
    """角色索引；带短 TTL 内存缓存。"""
    now = time.monotonic()
    cached = _characters_cache.get(api_base)
    if use_cache and cached and now - cached[0] < CHARACTER_CACHE_TTL:
        return cached[1]

    data = await _get_data(_endpoint(api_base, "/"), None, timeout)
    roles = data.get("roles")
    if not isinstance(roles, list):
        raise EmojiSourceError("API_ERROR", "接口的角色索引格式不对")

    items: list[CharacterItem] = []
    for role in roles:
        if not isinstance(role, dict):
            continue
        name = str(role.get("name") or "").strip()
        if not name:
            continue
        count = role.get("emojiCount")
        items.append(CharacterItem(name=name, count=count if isinstance(count, int) else 0))

    if not items:
        raise EmojiSourceError("EMPTY", "接口没有返回任何角色")

    _characters_cache[api_base] = (now, items)
    return items


async def fetch_random_emoji(
    api_base: str = DEFAULT_API_BASE,
    character: str = "",
    timeout: float = 10.0,
) -> Emoji:
    """随机取一张表情；指定角色时只在该角色里抽。"""
    params = {"format": "json"}
    if character:
        params["role"] = character

    data = await _get_data(_endpoint(api_base, "/random"), params, timeout)
    url = str(data.get("url") or "").strip()
    if not url:
        raise EmojiSourceError("API_ERROR", "接口没有返回图片地址")

    return Emoji(
        source="api",
        character=str(data.get("role") or character or ""),
        image=_absolute(api_base, url),
        name=str(data.get("name") or ""),
    )
