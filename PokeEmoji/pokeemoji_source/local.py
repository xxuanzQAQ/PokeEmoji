"""本地表情包目录（接口不可用时的兜底数据源）。

目录约定（与 wuwa 表情包爬虫的输出一致）：::

    <emoji_dir>/
    ├── 爱弥斯/              # 公共分类：哪个 bot 都能选
    │   ├── 1爱心.gif
    │   └── ...
    ├── 3776946954/         # bot 专属分类：目录名即 bot 标识，只有它能用
    │   ├── 1.gif
    │   └── 打工人/          # 专属目录里再分一层就是专属子分类
    │       └── 加班.gif
    └── 珂莱塔/
        └── ...

一级子目录名即分类名，目录里的图片文件即该分类的表情；隐藏文件和非图片文件
（例如爬虫写下的 `.crawler_state.json`）会被忽略。

一级目录名是「bot 专属目录」时（纯数字的 bot 账号，或 `bot_` / `qq_` 前缀），
该目录连同它下面的子目录都算这个 bot 的专属分类：其他 bot 既不会在列表里看到，
也切不过去，接口里同名的角色也顶不掉它自己的这份。
"""

from __future__ import annotations

import os
import time
import random
from pathlib import Path

from gsuid_core.data_store import get_res_path

from .types import Emoji, BotContext, CharacterItem, EmojiSourceError, name_key

# 默认放在 Core 数据目录下（<数据目录>/PokeEmoji/emojis），跟着部署走，
# 不写死某台机器的绝对路径；可在控制台或环境变量 POKEEMOJI_EMOJI_DIR 里改。
DEFAULT_EMOJI_DIR = str(get_res_path("PokeEmoji/emojis"))

# 目录扫描结果的缓存时长：本地文件变动很慢，扫一次够用一会儿
SCAN_CACHE_TTL = 60.0

IMAGE_SUFFIXES = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".avif"}

# 专属目录的显式前缀（后面跟 bot 标识）；裸目录名是纯数字时也按专属目录处理
OWNER_PREFIXES = ("bot_", "bot-", "qq_", "qq-")
MIN_NUMERIC_OWNER_LEN = 5

# key 为目录路径，value 为 (根目录 mtime, 专属目录 mtime, 扫描时间, 分类列表)
_cache: dict[str, tuple[float, tuple[tuple[str, float], ...], float, list[CharacterItem]]] = {}


def resolve_emoji_dir(emoji_dir: str | Path) -> Path:
    return Path(emoji_dir).expanduser()


def parse_owner(dirname: str) -> str | None:
    """一级目录名指向某个 bot 时返回它的标识（专属目录），否则返回 None。"""
    name = dirname.strip()
    folded = name.casefold()
    for prefix in OWNER_PREFIXES:
        if folded.startswith(prefix) and len(name) > len(prefix):
            return name[len(prefix) :]
    if name.isdigit() and len(name) >= MIN_NUMERIC_OWNER_LEN:
        return name
    return None


def _list_images(folder: Path) -> list[Path]:
    """列出目录里的图片文件；按文件名排序，保证同一目录的行为可复现。"""
    images: list[Path] = []
    try:
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.name.startswith(".") or not entry.is_file():
                    continue
                if os.path.splitext(entry.name)[1].lower() in IMAGE_SUFFIXES:
                    images.append(folder / entry.name)
    except OSError as exc:
        raise EmojiSourceError("READ_ERROR", f"读取目录 {folder} 失败: {exc}") from exc
    images.sort(key=lambda p: p.name)
    return images


def _list_subdirs(folder: Path) -> list[Path]:
    """列出目录下的实体子目录；隐藏目录跳过。"""
    subdirs: list[Path] = []
    try:
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.name.startswith(".") or not entry.is_dir():
                    continue
                subdirs.append(folder / entry.name)
    except OSError as exc:
        raise EmojiSourceError("READ_ERROR", f"读取目录 {folder} 失败: {exc}") from exc
    subdirs.sort(key=lambda p: p.name)
    return subdirs


def _scan_items(root: Path) -> tuple[list[CharacterItem], list[Path]]:
    """扫描一级目录；返回 (全部分类, 专属目录列表)。"""
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name)
    except OSError as exc:
        raise EmojiSourceError("READ_ERROR", f"读取目录 {root} 失败: {exc}") from exc

    items: list[CharacterItem] = []
    owner_dirs: list[Path] = []
    for entry in entries:
        if entry.name.startswith(".") or not entry.is_dir():
            continue

        owner = parse_owner(entry.name)
        if owner is None:
            images = _list_images(entry)
            items.append(
                CharacterItem(
                    name=entry.name,
                    count=len(images),
                    local_only=True,
                    path=entry,
                    thumbnail=images[0] if images else None,
                )
            )
            continue

        owner_dirs.append(entry)
        subdirs = _list_subdirs(entry)
        for sub in subdirs:
            images = _list_images(sub)
            item = CharacterItem(
                name=sub.name,
                count=len(images),
                local_only=True,
                path=sub,
                owner=owner,
                thumbnail=images[0] if images else None,
            )
            items.append(item)
        # 专属目录自己直接放图时，目录名也是这个 bot 的一个分类
        own_images = _list_images(entry)
        own_count = len(own_images)
        if own_count or not subdirs:
            items.append(
                CharacterItem(
                    name=entry.name,
                    count=own_count,
                    local_only=True,
                    path=entry,
                    owner=owner,
                    thumbnail=own_images[0] if own_images else None,
                )
            )
    return items, owner_dirs


def _owner_stamps(root: Path, names: list[str]) -> tuple[tuple[str, float], ...]:
    """重新采集专属目录的 mtime：在专属目录里加/删分类时，根目录的 mtime 不会变。"""
    stamps: list[tuple[str, float]] = []
    for name in names:
        try:
            stamps.append((name, (root / name).stat().st_mtime))
        except OSError:
            stamps.append((name, 0.0))
    return tuple(stamps)


def scan_characters(emoji_dir: str | Path = DEFAULT_EMOJI_DIR, *, use_cache: bool = True) -> list[CharacterItem]:
    """扫描本地目录，返回全部分类（含空目录和别人的专属分类），带短 TTL 缓存。"""
    root = resolve_emoji_dir(emoji_dir)
    if not root.is_dir():
        raise EmojiSourceError("NO_DIR", f"表情包目录不存在：{root}")

    try:
        mtime = root.stat().st_mtime
    except OSError as exc:
        raise EmojiSourceError("READ_ERROR", f"读取目录 {root} 失败: {exc}") from exc

    now = time.monotonic()
    key = str(root)
    cached = _cache.get(key)
    if use_cache and cached and now - cached[2] < SCAN_CACHE_TTL and cached[0] == mtime:
        if _owner_stamps(root, [name for name, _ in cached[1]]) == cached[1]:
            return cached[3]

    items, owner_dirs = _scan_items(root)
    _cache[key] = (mtime, _owner_stamps(root, [folder.name for folder in owner_dirs]), now, items)
    return items


def visible_characters(emoji_dir: str | Path = DEFAULT_EMOJI_DIR, bot: BotContext | None = None) -> list[CharacterItem]:
    """当前 bot 看得见的分类：公共分类 + 自己的专属分类。"""
    viewer = bot or BotContext()
    return [item for item in scan_characters(emoji_dir) if viewer.can_access(item.owner)]


def list_characters(emoji_dir: str | Path = DEFAULT_EMOJI_DIR, bot: BotContext | None = None) -> list[CharacterItem]:
    """本地可用分类；空目录不列入，同名的专属分类盖掉公共分类。"""
    items = [item for item in visible_characters(emoji_dir, bot) if item.count > 0]
    deduped: dict[str, CharacterItem] = {}
    for item in sorted(items, key=lambda item: item.owner is None):  # 专属优先，同名只留专属那份
        deduped.setdefault(name_key(item.name) or item.name, item)
    return sorted(deduped.values(), key=lambda item: item.name)


def _name_matches(candidate: str, wanted: str) -> bool:
    """精确 → 忽略大小写 → 归一形式，三级都算匹配。"""
    if candidate == wanted or candidate.casefold() == wanted.casefold():
        return True
    wanted_key = name_key(wanted)
    return bool(wanted_key) and name_key(candidate) == wanted_key


def _match_character(items: list[CharacterItem], wanted: str) -> CharacterItem | None:
    """先精确匹配，再忽略大小写，最后按归一形式匹配；专属分类优先于同名的公共分类。"""
    ordered = [item for item in items if item.owner is not None]
    ordered.extend(item for item in items if item.owner is None)

    for item in ordered:
        if item.name == wanted:
            return item

    folded = wanted.casefold()
    for item in ordered:
        if item.name.casefold() == folded:
            return item

    wanted_key = name_key(wanted)
    if not wanted_key:
        return None
    for item in ordered:
        if name_key(item.name) == wanted_key:
            return item
    return None


def owned_character(
    emoji_dir: str | Path = DEFAULT_EMOJI_DIR,
    character: str = "",
    bot: BotContext | None = None,
) -> CharacterItem | None:
    """当前 bot 自己的专属分类里有没有这个名字。"""
    if not character:
        return None
    viewer = bot or BotContext()
    items = [item for item in scan_characters(emoji_dir) if item.owner is not None and viewer.can_access(item.owner)]
    return _match_character(items, character)


def foreign_owner(
    emoji_dir: str | Path = DEFAULT_EMOJI_DIR,
    character: str = "",
    bot: BotContext | None = None,
) -> str | None:
    """这个名字是不是别的 bot 的专属分类；是的话返回归属的 bot 标识。

    自己也有同名分类（公共的或自己的专属）时不算被占用，返回 None。
    """
    if not character:
        return None
    viewer = bot or BotContext()
    foreign: str | None = None
    for item in scan_characters(emoji_dir):
        if not _name_matches(item.name, character):
            continue
        if viewer.can_access(item.owner):
            return None
        foreign = item.owner or foreign
    return foreign


def random_emoji(
    emoji_dir: str | Path = DEFAULT_EMOJI_DIR,
    character: str = "",
    bot: BotContext | None = None,
) -> Emoji:
    """随机取一张本地表情；指定分类时只在该分类目录里抽，且只在本 bot 能用的分类里找。"""
    items = visible_characters(emoji_dir, bot)
    if character:
        matched = _match_character(items, character)
        if matched is None:
            raise EmojiSourceError("NO_CHARACTER", f"没有找到角色「{character}」")
        target = matched
    else:
        usable = [item for item in items if item.count > 0]
        if not usable:
            raise EmojiSourceError("EMPTY", f"{resolve_emoji_dir(emoji_dir)} 下没有可用的角色目录")
        target = random.choice(usable)

    if target.path is None:
        raise EmojiSourceError("NO_IMAGE", f"「{target.name}」目录里没有图片")
    images = _list_images(target.path)
    if not images:
        raise EmojiSourceError("NO_IMAGE", f"「{target.name}」目录里没有图片")

    chosen = random.choice(images)
    try:
        size = chosen.stat().st_size
    except OSError as exc:
        raise EmojiSourceError("READ_ERROR", f"读取文件 {chosen} 失败: {exc}") from exc

    return Emoji(source="local", character=target.name, image=chosen, name=chosen.stem, size=size)
