"""两个数据源（接口 / 本地目录）共用的数据结构与错误类型。"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

# 角色名长度上限：接口与本地目录都不该用到这么长的名字，防一下超长输入
MAX_CHARACTER_LEN = 120

# 角色名比对用的装饰字符（陆·赫斯 / 陆赫斯 这类写法差异）
_IGNORED_CHARS = str.maketrans("", "", "·・ ._-")


@dataclass(frozen=True)
class CharacterItem:
    """一个可选角色；local_only 表示接口索引里没有、只在本地区有。

    owner 是本地「专属目录」归属的 bot 标识：非 None 时只有这个 bot 能选到它，
    其他 bot 既看不到也切不进去。
    """

    name: str
    count: int = 0
    local_only: bool = False
    path: Path | None = None  # 本地角色目录；接口索引里的角色为 None
    role_id: str | None = None  # 接口索引里的角色 id；本地角色为 None
    owner: str | None = None  # 专属目录归属的 bot；公共角色为 None
    thumbnail: str | Path | None = None  # 列表展示用缩略图（本地首图或接口封面）


@dataclass(frozen=True)
class BotContext:
    """当前会话所属的 bot：bot_id 是适配器名（onebot 等），bot_self_id 是账号（QQ 号等）。

    本地专属目录用目录名标归属，两个标识都认，方便按账号（推荐）或按适配器归档。
    """

    bot_id: str = ""
    bot_self_id: str = ""

    @property
    def ids(self) -> frozenset[str]:
        return frozenset(id_key(value) for value in (self.bot_id, self.bot_self_id) if value.strip())

    def can_access(self, owner: str | None) -> bool:
        """公共分类谁都能用；专属分类只认归属者。"""
        return owner is None or id_key(owner) in self.ids


def id_key(value: str) -> str:
    """bot 标识的比对形式：去空白、忽略大小写。"""
    return value.strip().casefold()


@dataclass(frozen=True)
class Emoji:
    """抽中的一张表情。"""

    source: str  # api / local
    character: str
    image: str | Path  # 接口直链（str）或本地文件路径（Path）
    name: str = ""
    size: int = 0  # 本地文件的字节数；接口取图时未知，为 0

    @property
    def is_remote(self) -> bool:
        return isinstance(self.image, str)


class EmojiSourceError(Exception):
    """取图失败；kind 决定给用户的提示。

    kind 取值：
        NO_CHARACTER      角色不存在（接口没有匹配，本地也没有这个目录）
        NO_IMAGE          角色存在但一张图都没有
        NO_DIR            本地表情包目录不存在或读不了
        EMPTY             本地目录里没有任何角色
        INVALID_CHARACTER 角色名不合法
        READ_ERROR        本地文件读取失败
        NETWORK           接口连不上（超时、DNS、TLS 等）
        API_ERROR         接口返回了非成功结果（HTTP 非 200、body 解析失败等）
    """

    def __init__(self, kind: str, message: str = "") -> None:
        self.kind = kind
        self.message = message
        super().__init__(f"{kind}: {message}" if message else kind)


def normalize_character(value: str) -> str:
    """角色名去空白；空串表示不指定角色（随机）。"""
    return value.strip()


def name_key(name: str) -> str:
    """角色名归一形式：去掉「·」、空格一类的装饰字符，忽略大小写。"""
    return name.translate(_IGNORED_CHARS).casefold()
