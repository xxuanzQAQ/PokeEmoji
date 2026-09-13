"""本地表情包目录（接口不可用时的兜底数据源）。

目录约定（与 wuwa 表情包爬虫的输出一致）：::

    <emoji_dir>/
    ├── 爱弥斯/
    │   ├── 1爱心.gif
    │   └── ...
    └── 珂莱塔/
        └── ...

一级子目录名即角色名，子目录里的图片文件即该角色的表情；隐藏文件和非图片文件
（例如爬虫写下的 `.crawler_state.json`）会被忽略。
"""

from __future__ import annotations

import os
import time
import random
from pathlib import Path

from .types import Emoji, CharacterItem, EmojiSourceError, name_key

# 鸣潮表情包爬虫（wuwa_emoji_crawler.py）的默认输出目录，可在控制台里改
DEFAULT_EMOJI_DIR = "/sd/root_data/wuwa表情包/wuwa_emojis"

# 目录扫描结果的缓存时长：本地文件变动很慢，扫一次够用一会儿
SCAN_CACHE_TTL = 60.0

IMAGE_SUFFIXES = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".avif"}

# key 为目录路径，value 为 (目录 mtime, 扫描时间, 角色列表)
_cache: dict[str, tuple[float, float, list[CharacterItem]]] = {}


def resolve_emoji_dir(emoji_dir: str | Path) -> Path:
    return Path(emoji_dir).expanduser()


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


def _scan_characters(root: Path) -> list[CharacterItem]:
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name)
    except OSError as exc:
        raise EmojiSourceError("READ_ERROR", f"读取目录 {root} 失败: {exc}") from exc

    items: list[CharacterItem] = []
    for entry in entries:
        if entry.name.startswith(".") or not entry.is_dir():
            continue
        items.append(CharacterItem(name=entry.name, count=len(_list_images(entry)), local_only=True, path=entry))
    return items


def scan_characters(emoji_dir: str | Path = DEFAULT_EMOJI_DIR, *, use_cache: bool = True) -> list[CharacterItem]:
    """扫描本地目录，返回全部角色（含没有图片的空目录），带短 TTL 缓存。"""
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
    if use_cache and cached and cached[0] == mtime and now - cached[1] < SCAN_CACHE_TTL:
        return cached[2]

    items = _scan_characters(root)
    _cache[key] = (mtime, now, items)
    return items


def list_characters(emoji_dir: str | Path = DEFAULT_EMOJI_DIR) -> list[CharacterItem]:
    """本地可用角色；爬虫还没下到图的空目录不列入。"""
    return [item for item in scan_characters(emoji_dir) if item.count > 0]


def _match_character(items: list[CharacterItem], wanted: str) -> CharacterItem | None:
    """先精确匹配，再忽略大小写，最后按归一形式匹配。"""
    for item in items:
        if item.name == wanted:
            return item

    folded = wanted.casefold()
    for item in items:
        if item.name.casefold() == folded:
            return item

    wanted_key = name_key(wanted)
    if not wanted_key:
        return None
    for item in items:
        if name_key(item.name) == wanted_key:
            return item
    return None


def random_emoji(emoji_dir: str | Path = DEFAULT_EMOJI_DIR, character: str = "") -> Emoji:
    """随机取一张本地表情；指定角色时只在该角色目录里抽。"""
    items = scan_characters(emoji_dir)
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
