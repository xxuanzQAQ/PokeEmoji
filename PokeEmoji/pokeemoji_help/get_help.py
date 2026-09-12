"""用框架的 get_new_help 渲染插件帮助图。"""

import json
from pathlib import Path

from PIL import Image

from gsuid_core.sv import get_plugin_available_prefix
from gsuid_core.help.model import PluginSV, PluginHelp
from gsuid_core.help.draw_new_plugin_help import get_new_help

from ..version import PokeEmoji_version
from ..utils.resource_path import ICON_PATH

HELP_DATA = Path(__file__).parent / "help.json"
BANNER_BG = Path(__file__).parent / "texture2d" / "banner_bg.jpg"


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


def _plugin_sv(raw: object) -> PluginSV:
    if not isinstance(raw, dict):
        raise ValueError("help.json 的 data 元素必须是对象")
    return PluginSV(
        name=_text(raw.get("name"), "name"),
        desc=_text(raw.get("desc"), "desc"),
        eg=_text(raw.get("eg"), "eg"),
        highlight=0,
        need_ck=_flag(raw.get("need_ck", False), "need_ck"),
        need_sk=_flag(raw.get("need_sk", False), "need_sk"),
        need_admin=_flag(raw.get("need_admin", False), "need_admin"),
    )


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
        enable_cache=True,
    )
