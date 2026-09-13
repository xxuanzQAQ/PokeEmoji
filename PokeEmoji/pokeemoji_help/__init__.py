"""帮助注册：挂到全局帮助一览，并提供帮助图命令。"""

from PIL import Image

from gsuid_core.sv import SV, get_plugin_available_prefix
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.help.utils import register_help

from .get_help import get_help
from ..utils.resource_path import ICON_PATH

sv_help = SV("戳表情包帮助")


@sv_help.on_fullmatch("表情包帮助", block=True)
async def send_help_img(bot: Bot, ev: Event) -> None:
    await bot.send(await get_help())


register_help(
    "PokeEmoji",
    f"{get_plugin_available_prefix('PokeEmoji')}表情包帮助",
    Image.open(ICON_PATH),
)
