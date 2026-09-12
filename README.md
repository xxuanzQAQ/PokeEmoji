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

## 上游接口备忘（2026-09 实测）

所有接口挂在 `https://emoji.wuwa.games/apis/api.emoji.jaspin.top/v1alpha1`，无需鉴权、无需 Cookie：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/gallery-feed` | **本插件使用**。无限画廊数据流，返回 `total / seed / nextCursor / items / facetGroups` |
| GET | `/archive-catalog` | 144 个表情包（post）的目录，含 `samples / characters / artists / facets` |
| GET | `/archive-stats` | 144 个包的统计（数量、封面、下载/收藏数） |
| GET | `/gallery-index` | 全量资产索引，约 14 MB，前端批量预加载用 |
| GET | `/gallery-ranking` | 7785 条资产的排序数据，约 1.2 MB |
| GET | `/archive-sidebar` | 侧边栏 HTML 片段（不是 JSON） |
| GET | `/packs/{postName}` | 单个包的详情（assets / 归档下载地址 / 统计） |
| POST | `/packs/{postName}/downloads/preflight` | 下载预检，body `{scope, resourceIds, packVersion, format}`，返回直链 |
| PUT/DELETE | `/packs/{postName}/favorites/{resourceId}` | 收藏 / 取消收藏，需 `X-Emoji-Visitor` 头，会写服务端 |

### `/gallery-feed` 的查询参数

| 参数 | 取值 | 说明 |
|------|------|------|
| `size` | 1–100 | 每页条数，默认 24 |
| `sort` | `random` / `download` / `favorite` | 其它值一律按 `random` 处理 |
| `seed` | 字符串 | 随机排序的种子，与 `cursor` 配套才能翻页 |
| `cursor` | `nextCursor` | 不带对应 `seed` 会返回 400 |
| `filter` | `分类/值`，可重复 | 例 `角色/爱弥斯`、`画师/雾雪`；分类名来自 `facetGroups` |
| `scope` + `favoriteId` | `favorites` | 只看收藏，需自带访客 token，插件未使用 |

实测 `q` / `keyword` / `search` 均**不生效**（返回结果与不带该参数一致），所以插件只用 `filter` 做筛选，
分类索引缓存在内存里（TTL 6 小时）。

`items` 里本插件用到的字段：`originalUrl`（原图，多为 gif）、`previewUrl`（动图 webp 预览）和
`bytes`（原图体积，用于选择发送格式）。

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

## 备注

- 图片以 `link://` 直链下发，不经过 Core 中转，省带宽。
- 上游是第三方站点，接口若调整需要同步更新 `PokeEmoji/pokeemoji_api/wuwa_emoji.py`。
- 本插件只读上游的 `gallery-feed`，不写收藏、不触发下载。

## 源网址与致谢

- 表情包数据与公开接口：[emoji.wuwa.games](https://emoji.wuwa.games/)
- 接口服务：[api.emoji.jaspin.top](https://api.emoji.jaspin.top/)
- 感谢 Wuthering Waves Emoji 项目提供公开的表情包资源与接口。本插件仅作为 GsCore 的第三方调用方，版权与许可仍归原作者及上游项目所有。
