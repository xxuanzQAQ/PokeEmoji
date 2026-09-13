from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsIntConfig,
    GsStrConfig,
    GsBoolConfig,
)

from ..pokeemoji_source import DEFAULT_API_BASE, DEFAULT_EMOJI_DIR

CONFIG_DEFAULT: dict[str, GSC] = {
    "enable_api": GsBoolConfig(
        "优先用接口",
        "开启后优先调用随机表情接口；接口不可用或该角色没有图时，自动回落到本地目录",
        True,
    ),
    "api_base": GsStrConfig(
        "接口地址",
        "随机表情接口的基础地址，由接口提供方给出；一般无需修改",
        DEFAULT_API_BASE,
    ),
    "emoji_dir": GsStrConfig(
        "本地表情包目录",
        "备用图源（可选）：本地表情包根目录，一级子目录名即角色名；默认在数据目录的 PokeEmoji/emojis 下，留空时读环境变量 POKEEMOJI_EMOJI_DIR",
        DEFAULT_EMOJI_DIR,
    ),
    "default_character": GsStrConfig(
        "默认角色",
        "默认抽哪个角色的表情，填角色名即可（如 尤诺）；留空表示随机角色",
        "",
    ),
    "request_timeout": GsIntConfig(
        "接口超时(秒)",
        "请求接口的超时时间；超时或被限流都会回落到本地目录",
        10,
        max_value=120,
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
}
