"""用框架的 get_new_help 渲染插件帮助图。"""

import json
from typing import Any, cast
from pathlib import Path

from PIL import Image

from gsuid_core.sv import get_plugin_available_prefix
from gsuid_core.help.model import PluginSV, PluginHelp
from gsuid_core.help.draw_new_plugin_help import ICON_PATH as DEFAULT_ICON_PATH, get_new_help

from ..version import PokeEmoji_version
from ..utils.resource_path import ICON_PATH, PLUGIN_DIR

HELP_DATA = Path(__file__).parent / "help.json"
BANNER_BG = Path(__file__).parent / "texture2d" / "banner_bg.jpg"

# 命令图标不另存一份：装了 XutheringWavesUID 就借用它的图标集，没装则回落到框架自带图标。
# 键是本插件 help.json 里的命令名，值是 XW 的图标文件名（不含扩展名）。
XW_ICON_CANDIDATES = (
    # 常见布局：plugins/XutheringWavesUID/XutheringWavesUID/wutheringwaves_help/icon_path
    PLUGIN_DIR.parent / "XutheringWavesUID" / "XutheringWavesUID" / "wutheringwaves_help" / "icon_path",
    PLUGIN_DIR.parent / "XutheringWavesUID" / "wutheringwaves_help" / "icon_path",
)
COMMAND_ICONS: dict[str, str] = {
    "随机表情": "抽卡",
    "指定角色": "角色",
    "表情包列表": "收藏图鉴",
    "表情设置": "设置体力背景",
    "切换角色": "切换",
    "清除设置": "删除",
    "戳一戳统计": "练度总排行",
}


def _banner_bg() -> Image.Image | None:
    """没带自带 banner 时回落到框架默认底图。"""
    return Image.open(BANNER_BG) if BANNER_BG.exists() else None


def _text(raw: object, field: str) -> str:
    if not isinstance(raw, str):
        raise ValueError(f"help.json 的 {field} 必须是字符串")
    return raw


def _flag(raw: object, field: str) -> bool:
    if not isinstance(raw, bool):
        raise ValueError(f"help.json 的 {field} 必须是布尔值")
    return raw


_icon_dir_cache: Path | None = None


def icon_dir() -> Path:
    """命令图标的搜索目录：优先 XW 图标集，找不到就回落到框架默认图标目录。"""
    global _icon_dir_cache
    if _icon_dir_cache is None:
        _icon_dir_cache = next((path for path in XW_ICON_CANDIDATES if path.is_dir()), DEFAULT_ICON_PATH)
    return _icon_dir_cache


def _command_icon(name: str) -> Path | None:
    """命令图标指向 wwuid 的图标文件；没装 wwuid（或图标缺失）时返回 None 交给框架兜底。"""
    stem = COMMAND_ICONS.get(name)
    if not stem:
        return None
    icon = icon_dir() / f"{stem}.png"
    return icon if icon.exists() else None


def _plugin_sv(raw: object) -> PluginSV:
    if not isinstance(raw, dict):
        raise ValueError("help.json 的 data 元素必须是对象")

    name = _text(raw.get("name"), "name")
    sv: dict[str, Any] = {
        "name": name,
        "desc": _text(raw.get("desc"), "desc"),
        "eg": _text(raw.get("eg"), "eg"),
        "highlight": 0,
        "need_ck": _flag(raw.get("need_ck", False), "need_ck"),
        "need_sk": _flag(raw.get("need_sk", False), "need_sk"),
        "need_admin": _flag(raw.get("need_admin", False), "need_admin"),
    }
    # 渲染器支持额外的 icon 键，直接给图标文件路径，省得靠文件名去猜
    icon = _command_icon(name)
    if icon is not None:
        sv["icon"] = str(icon)
    return cast(PluginSV, sv)


def load_help_data() -> dict[str, PluginHelp]:
    raw: object = json.loads(HELP_DATA.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("help.json 顶层必须是对象")

    data: dict[str, PluginHelp] = {}
    for group, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"help.json 分组 {group} 必须是对象")
        items = value.get("data")
        if not isinstance(items, list):
            raise ValueError(f"help.json 分组 {group} 的 data 必须是数组")
        data[str(group)] = PluginHelp(
            desc=_text(value.get("desc"), f"{group}.desc"),
            data=[_plugin_sv(item) for item in items],
        )
    return data


async def get_help() -> bytes | str:
    return await get_new_help(
        plugin_name="PokeEmoji",
        plugin_info={f"v{PokeEmoji_version}": ""},
        plugin_icon=Image.open(ICON_PATH),
        plugin_help=load_help_data(),
        plugin_prefix=get_plugin_available_prefix("PokeEmoji"),
        help_mode="dark",
        banner_bg=_banner_bg(),
        banner_sub_text="被戳一戳，就回你一张表情包",
        icon_path=icon_dir(),
        enable_cache=True,
    )
