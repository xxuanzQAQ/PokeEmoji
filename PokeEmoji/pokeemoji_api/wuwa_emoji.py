"""随机表情接口客户端（api.random-emoji.wuwa.games）。

通过 API Key 鉴权，请求头形如 `Authorization: Bearer <KEY>`：

    GET <base>/random      随机取一张表情，可指定角色（slug 或完整名称）与格式
    GET <base>/characters  列出索引里有对应格式表情的角色

两个端点共用同一个每分钟额度，失败响应是 JSON `{code, message}`，并可能带
`Retry-After`。这里每个请求只发一次、不自动重试：机器人场景下连续重试只会
更快把额度打光，是否重试交给调用方按 HTTP 状态码决定。
"""

import time
from typing import TypeVar

import httpx
import msgspec

from gsuid_core.logger import logger

API_BASE = "https://emoji.wuwa.games/apis/api.random-emoji.wuwa.games/v1alpha1"
RANDOM_PATH = "/random"
CHARACTERS_PATH = "/characters"
USER_AGENT = "GsCore-PokeEmoji/1.0"

FORMAT_ORIGINAL = "original"
FORMAT_WEBP = "webp"
MAX_CHARACTER_LEN = 120

# 角色索引变动很慢（接口侧约 5 分半），缓存一会儿既省额度又省等待
CHARACTER_CACHE_TTL = 600

T = TypeVar("T")


class EmojiCharacter(msgspec.Struct, rename="camel"):
    """本次选中角色的标识与显示名。"""

    slug: str = ""
    name: str = ""


class RandomEmoji(msgspec.Struct, rename="camel"):
    """`/random` 的成功响应。"""

    id: str = ""
    character: EmojiCharacter = msgspec.field(default_factory=EmojiCharacter)
    url: str = ""
    format: str = ""
    animated: bool | None = None
    source_url: str | None = None


class CharacterItem(msgspec.Struct, rename="camel"):
    """`/characters` 里的一项角色。"""

    slug: str = ""
    name: str = ""
    count: int = 0


class CharacterList(msgspec.Struct, rename="camel"):
    items: list[CharacterItem] = msgspec.field(default_factory=list)


class ErrorBody(msgspec.Struct):
    code: str = ""
    message: str = ""


class EmojiAPIError(Exception):
    """接口返回非 200，或本地还没法发起请求时的统一错误。

    `status` 为 HTTP 状态码；未发出请求（缺 Key、网络异常、响应无法解析）时为 0。
    """

    def __init__(
        self,
        status: int,
        code: str = "",
        message: str = "",
        retry_after: float | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.message = message
        self.retry_after = retry_after
        super().__init__(f"HTTP {status} {code}: {message}".strip())


def normalize_format(value: str) -> str:
    """把配置或命令里的格式归一成接口认的 original / webp（值区分大小写）。"""
    return FORMAT_WEBP if value.strip().lower() == FORMAT_WEBP else FORMAT_ORIGINAL


def normalize_character(value: str) -> str:
    """角色参数去空白；空串表示不指定（对应省略 character 参数）。"""
    return value.strip()


def _decode(raw: bytes, type_: type[T]) -> T:
    try:
        return msgspec.json.decode(raw, type=type_)
    except msgspec.DecodeError as exc:
        raise EmojiAPIError(0, "BAD_RESPONSE", "接口返回了无法解析的内容") from exc


def _error_from(response: httpx.Response) -> EmojiAPIError:
    retry_after: float | None = None
    raw_retry = response.headers.get("Retry-After", "").strip()
    if raw_retry:
        try:
            retry_after = float(raw_retry)
        except ValueError:
            retry_after = None

    code = ""
    message = ""
    try:
        body = msgspec.json.decode(response.content, type=ErrorBody)
        code, message = body.code, body.message
    except msgspec.DecodeError:
        message = response.text.strip()

    return EmojiAPIError(response.status_code, code, message, retry_after)


async def request_json(
    path: str,
    params: dict[str, str],
    *,
    api_key: str,
    base_url: str = API_BASE,
    timeout: int = 20,
) -> bytes:
    """发一次 GET，200 返回原始 body，其余情况抛 EmojiAPIError。"""
    key = api_key.strip()
    if not key:
        raise EmojiAPIError(0, "MISSING_API_KEY", "尚未配置 API Key")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": USER_AGENT,
    }
    url = f"{base_url.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            response = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise EmojiAPIError(0, "NETWORK_ERROR", f"请求接口失败: {exc}") from exc

    if response.status_code != 200:
        error = _error_from(response)
        logger.debug(f"[PokeEmoji] {path} 返回 {error.status} {error.code}: {error.message}")
        raise error

    return response.content


async def get_random_emoji(
    *,
    api_key: str,
    base_url: str = API_BASE,
    character: str = "",
    image_format: str = FORMAT_ORIGINAL,
    timeout: int = 20,
) -> RandomEmoji:
    """随机取一张表情；指定角色时只在该角色的对应格式里抽。"""
    name = normalize_character(character)
    if len(name) > MAX_CHARACTER_LEN:
        raise EmojiAPIError(400, "INVALID_CHARACTER", f"角色最长为 {MAX_CHARACTER_LEN} 个字符")

    params = {"format": normalize_format(image_format)}
    if name:
        params["character"] = name

    raw = await request_json(RANDOM_PATH, params, api_key=api_key, base_url=base_url, timeout=timeout)
    return _decode(raw, RandomEmoji)


_character_cache: dict[tuple[str, str], tuple[float, list[CharacterItem]]] = {}


async def get_characters(
    *,
    api_key: str,
    base_url: str = API_BASE,
    image_format: str = FORMAT_ORIGINAL,
    timeout: int = 20,
    use_cache: bool = True,
) -> list[CharacterItem]:
    """列出当前索引里有指定格式表情的角色，带短 TTL 内存缓存。"""
    fmt = normalize_format(image_format)
    cache_key = (base_url, fmt)
    now = time.monotonic()

    cached = _character_cache.get(cache_key)
    if use_cache and cached and now - cached[0] < CHARACTER_CACHE_TTL:
        return cached[1]

    raw = await request_json(CHARACTERS_PATH, {"format": fmt}, api_key=api_key, base_url=base_url, timeout=timeout)
    items = _decode(raw, CharacterList).items
    _character_cache[cache_key] = (now, items)
    return items


def describe_error(error: EmojiAPIError) -> str:
    """把接口错误翻成能直接发给用户的短句。"""
    if error.code == "MISSING_API_KEY":
        return "还没有配置 API Key，请先在网页控制台的 PokeEmoji 插件配置里填好。"
    if error.code in ("NETWORK_ERROR", "BAD_RESPONSE"):
        return "接口暂时连不上，稍后再试试吧。"

    if error.status == 400:
        return "角色或格式不对：一次只能指定一个角色，角色名有重名或写法有误，换个写法再试试。"
    if error.status == 401:
        return "接口鉴权失败：API Key 无效、已过期或已停用，请检查插件配置。"
    if error.status == 404:
        return "这个角色暂时没有该格式的表情，换个角色或格式再试试。"
    if error.status == 429:
        wait = f"{int(error.retry_after)} 秒" if error.retry_after else "一会儿"
        return f"这会儿调用太频繁了，等 {wait} 再试。"
    if error.status == 503:
        return "接口暂时不可用，稍后再试试吧。"
    return f"接口返回了异常（HTTP {error.status}），稍后再试试吧。"
