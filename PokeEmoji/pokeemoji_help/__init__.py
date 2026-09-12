"""帮助注册：挂到全局帮助一览，并提供一个文本帮助命令。"""

from PIL import Image

from gsuid_core.sv import SV, get_plugin_available_prefix
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.help.utils import register_help

from ..utils.resource_path import ICON_PATH

sv_help = SV("戳表情包帮助")

HELP_TEXT = "\n".join(
    [
        "【戳一戳表情包】",
        "被戳一戳时会回一张表情包，也可以直接命令我取图：",
        "· 随机表情 —— 随机来一张",
        "· 随机表情 爱弥斯 —— 按角色 / 画师 / 企划筛选",
        "· 随机表情 下载榜 —— 取下载最多的那批",
        "· 表情包分类 —— 查看可用的筛选词",
        "· 表情设置 尤诺 —— 把本会话戳一戳的表情切成某个类别",
        "· 表情设置 随机 —— 取消本会话设置，恢复全局默认",
        "· 表情包帮助 —— 本帮助",
        f"（命令都可以加「{get_plugin_available_prefix('PokeEmoji')}」前缀，例如 "
        f"{get_plugin_available_prefix('PokeEmoji')}随机表情）",
    ]
)


@sv_help.on_fullmatch("表情包帮助", block=True)
async def send_help(bot: Bot, ev: Event) -> None:
    await bot.send(HELP_TEXT)


register_help(
    "PokeEmoji",
    f"{get_plugin_available_prefix('PokeEmoji')}表情包帮助",
    Image.open(ICON_PATH),
)
