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
    """一个可选角色；local_only 表示接口索引里没有、只在本地区有。"""

    name: str
    count: int = 0
    local_only: bool = False
    path: Path | None = None  # 本地角色目录；接口索引里的角色为 None
    role_id: str | None = None  # 接口索引里的角色 id；本地角色为 None


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
