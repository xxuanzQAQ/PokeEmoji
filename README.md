# PokeEmoji

GsCore 插件：被**戳一戳**时回一张表情包，数据来自 [emoji.wuwa.games](https://emoji.wuwa.games/) 的公开接口。

## 功能

- `poke` 元事件触发：被戳时自动回一张表情包（可配概率、冷却、只回应戳机器人自己）。
- 命令取图：`随机表情 [关键词]`，关键词支持角色 / 画师 / 企划 / 原设等分类，也支持「下载榜 / 收藏榜」。
- `表情包分类` 列出全部可用筛选词。
- `表情设置 <关键词>` 让用户自己切换戳一戳发的类别：群聊按群、私聊按人分别记住。
- 全部开关与阈值在 WebConsole 插件配置里改，无需重启。

## 命令

| 命令 | 说明 |
|------|------|
| `戳一戳`（元事件） | 被戳时回一张表情包 |
| `随机表情` | 随机来一张 |
| `随机表情 爱弥斯` | 按分类筛选（角色 / 画师 / 企划 / 原设） |
| `随机表情 下载榜` | 取下载最多的那批里随机一张 |
| `表情包分类` | 列出可用筛选词 |
| `表情设置` | 查看本会话当前的戳一戳表情类别 |
| `表情设置 尤诺` | 把本会话（群 / 私聊）的戳一戳表情切成该类 |
| `表情设置 随机` | 取消本会话设置，回到全局默认筛选 |
| `表情包帮助` | 帮助 |

以上命令都带 `戳` 前缀变体，例如 `戳随机表情`。

## 配置项

| 键 | 默认 | 说明 |
|----|------|------|
| `enable_poke` | `true` | 是否响应戳一戳 |
| `only_poke_bot` | `true` | 只在被戳对象是机器人自己时回复 |
| `allow_user_setting` | `true` | 允许用户用「表情设置」自行切换本会话类别 |
| `poke_probability` | `100` | 回复概率(%) |
| `cooldown_seconds` | `10` | 同一会话冷却，0 表示不限制 |
| `sort_mode` | `random` | 取图排序 |
| `default_filter` | 空 | 默认筛选，如 `角色/爱弥斯` |
| `candidate_size` | `30` | 候选数量，取回后随机挑一张 |
| `image_format` | `auto` | `auto` / `original` / `webp` |
| `auto_webp_bytes` | `3145728` | auto 下的体积阈值 |
| `request_timeout` | `20` | 接口超时(秒) |

## 会话级设置

「表情设置」写入 `pokeemojisetting` 表（`bot_id` + `scope_id` 唯一，群聊 `group_<群号>`、
私聊 `user_<用户号>`），所以同一个群里所有人共享一份设置、私聊各记各的。
用户没设置过、或管理员把 `allow_user_setting` 关掉时，一律回落到 `default_filter`。


## 源网址与致谢

- 表情包数据与公开接口：[emoji.wuwa.games](https://emoji.wuwa.games/)
- 接口服务：[api.emoji.jaspin.top](https://api.emoji.jaspin.top/)
- 插件图标：取自 [emoji.wuwa.games](https://emoji.wuwa.games/) 的站点图标
- 感谢 呜哇小站 提供公开的表情包资源与接口。本插件仅作为 GsCore 的第三方调用方，版权与许可仍归原作者及上游项目所有。
