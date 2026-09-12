from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsIntConfig,
    GsStrConfig,
    GsBoolConfig,
)

CONFIG_DEFAULT: dict[str, GSC] = {
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
        "开启后可用「表情设置 尤诺」切换本会话的戳一戳表情；关闭则只认全局默认筛选",
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
    "sort_mode": GsStrConfig(
        "取图排序",
        "random 随机 / download 下载最多 / favorite 收藏最多",
        "random",
        options=["random", "download", "favorite"],
    ),
    "default_filter": GsStrConfig(
        "默认筛选",
        "形如 角色/爱弥斯、画师/雾雪；留空表示不筛选",
        "",
    ),
    "candidate_size": GsIntConfig(
        "候选数量",
        "每次从接口取回多少张候选，再从中随机挑一张",
        30,
        max_value=100,
    ),
    "image_format": GsStrConfig(
        "发送格式",
        "auto 表示原图超过阈值时改用 webp 预览；original 始终发原图；webp 始终发预览图",
        "auto",
        options=["auto", "original", "webp"],
    ),
    "auto_webp_bytes": GsIntConfig(
        "转预览图阈值(字节)",
        "auto 格式下原图体积超过该值时改用 webp 预览图",
        3145728,
        max_value=20971520,
    ),
    "request_timeout": GsIntConfig(
        "接口超时(秒)",
        "请求表情包接口的超时时间",
        20,
        max_value=120,
    ),
}
