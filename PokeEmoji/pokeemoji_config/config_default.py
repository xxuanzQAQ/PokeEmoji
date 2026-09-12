from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsIntConfig,
    GsStrConfig,
    GsBoolConfig,
)

from ..pokeemoji_api import API_BASE

CONFIG_DEFAULT: dict[str, GSC] = {
    "api_base": GsStrConfig(
        "接口地址",
        "随机表情接口的基础地址，由接口提供方给出；一般无需修改",
        API_BASE,
    ),
    "api_key": GsStrConfig(
        "API Key",
        "接口密钥，形如 re_xxx.yyy，以 Bearer 方式放在请求头；留空时改用环境变量 POKEEMOJI_API_KEY",
        "",
        secret=True,
    ),
    "default_character": GsStrConfig(
        "默认角色",
        "默认抽哪个角色的表情，填角色名即可；留空表示随机角色",
        "",
    ),
    "image_format": GsStrConfig(
        "图片格式",
        "original 取原图；webp 取 WebP 图（接口不即时转换，webp 不代表一定是动图）",
        "original",
        options=["original", "webp"],
    ),
    "enable_poke": GsBoolConfig(
        "响应戳一戳",
        "被戳一戳时是否自动回复一张表情包",
        True,
    ),
    "only_poke_bot": GsBoolConfig(
        "只回应戳机器人",
        "开启后仅当被戳对象是机器人自己时回复；关闭后群里任何人被戳都会回复",
        True,
    ),
    "allow_user_setting": GsBoolConfig(
        "允许用户自助切换",
        "开启后可用「表情设置 尤诺」切换本会话的戳一戳角色；关闭则只认全局默认角色",
        True,
    ),
    "poke_probability": GsIntConfig(
        "回复概率(%)",
        "被戳一戳时回复的概率，100 表示每次都回",
        100,
        max_value=100,
    ),
    "cooldown_seconds": GsIntConfig(
        "冷却时间(秒)",
        "同一会话两次自动回复之间的最小间隔，0 表示不限制",
        10,
        max_value=600,
    ),
    "request_timeout": GsIntConfig(
        "接口超时(秒)",
        "请求表情包接口的超时时间",
        20,
        max_value=120,
    ),
}
