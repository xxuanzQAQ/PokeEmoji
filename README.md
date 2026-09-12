# PokeEmoji

<p align="center">
  <a href="https://github.com/xxuanzQAQ/PokeEmoji"><img src="./ICON.png" width="160" alt="PokeEmoji ICON"></a>
</p>

<h1 align="center">PokeEmoji</h1>
<h4 align="center">✨ 被戳一戳，就回你一张表情包 ✨</h4>

<div align="center">
  <a href="https://github.com/Genshin-bots/gsuid_core">早柚核心</a> &nbsp;·&nbsp;
  <a href="https://github.com/xxuanzQAQ/PokeEmoji/issues">问题反馈</a>
</div>

<br/>

## 丨安装提醒

> 本插件是 [早柚核心 (GsCore)](https://github.com/Genshin-bots/gsuid_core) 的扩展，需要先部署好 Core 才能使用；安装完成后重启 Core 才会生效。

- 命令安装：`core安装插件PokeEmoji`
- 手动安装：把本仓库 `git clone` 到 `gsuid_core/plugins/PokeEmoji/`，再发 `core重启`

> [!NOTE]
> 表情包数据来自 [emoji.wuwa.games](https://emoji.wuwa.games/) 的公开接口，与站点本身存在一定延迟；接口不可用时插件只会跳过本次回复，不影响 Core 的其它功能。

<br/>

## 丨快速上手

装好后在聊天窗口发一条 `ww帮助` 就能拿到一张帮助图。插件名 `PokeEmoji`，前缀 `ww`（`WW` 同效，也可以不带前缀直接发指令），别名 `pokeemoji` / `戳一戳表情`。

### 常用指令

| 触发指令 | 功能说明 |
| :--- | :--- |
| （被戳一戳，元事件） | 自动回一张表情包 |
| `ww随机表情` | 随机来一张 |
| `ww随机表情 爱弥斯` | 按角色 / 画师 / 企划 / 原设等分类筛选 |
| `ww随机表情 下载榜` | 从下载最多的那批里随机取一张 |
| `ww表情包分类` | 列出全部可用筛选词 |
| `ww表情设置` | 查看本会话当前的戳一戳类别 |
| `ww表情设置 尤诺` | 把本会话切成某个类别 |
| `ww表情设置 随机` | 取消本会话设置，回到全局默认 |
| `ww帮助` | 返回一张帮助图 |

<br/>

## 丨功能特色

- **戳一戳自动回图**：走 `poke` 元事件，不需要 @ 机器人。
- **帮助出图**：`ww帮助` 直接返回一张版式化的帮助图，同时挂进 Core 的插件帮助一览。
- **分类筛选**：支持角色 / 画师 / 企划 / 原设等关键词，也支持下载榜 / 收藏榜取图。
- **会话级偏好**：`表情设置` 的结果落库，群聊按群共享、私聊各记各的，互不干扰。
- **打扰程度可控**：回复概率、同会话冷却、是否只回应戳机器人自己，都能在控制台调。
- **体积自适应**：`auto` 模式下原图过大会改发 webp 预览图，省流量也省发送耗时。
- **改完即生效**：所有开关与阈值都在 WebConsole 改，不需要重启 Core。

<br/>

## 丨配置项

WebConsole → 插件配置 → `PokeEmoji`。

| 配置键 | 默认 | 说明 |
| :--- | :--- | :--- |
| `enable_poke` | `true` | 是否响应戳一戳 |
| `only_poke_bot` | `true` | 只在被戳对象是机器人自己时回复 |
| `allow_user_setting` | `true` | 允许用户用「表情设置」切换本会话类别 |
| `poke_probability` | `100` | 回复概率(%)，`100` 表示每次都回 |
| `cooldown_seconds` | `10` | 同一会话两次自动回复的最小间隔，`0` 不限制 |
| `sort_mode` | `random` | 取图排序：`random` / `download` / `favorite` |
| `default_filter` | 空 | 默认筛选，如 `角色/爱弥斯`；留空表示不筛选 |
| `candidate_size` | `30` | 每次取回的候选数量，再从中随机挑一张 |
| `image_format` | `auto` | `auto` / `original` / `webp` |
| `auto_webp_bytes` | `3145728` | `auto` 下原图超过该体积就改发 webp 预览图 |
| `request_timeout` | `20` | 接口超时(秒) |

<br/>

## 丨会话级设置

`表情设置` 写入 `pokeemojisetting` 表（`bot_id` + `scope_id` 唯一）：

- 群聊记 `group_<群号>` —— 同一个群里所有人共用一份设置；
- 私聊记 `user_<用户号>` —— 各记各的；
- 用户没设置过，或管理员关掉 `allow_user_setting` 时，一律回落到 `default_filter`。

<br/>

## 丨数据存储

| 内容 | 位置 |
| :--- | :--- |
| 插件配置 | `data/PokeEmoji/config.json` |
| 会话设置 | SQLite 表 `pokeemojisetting`（默认 `data/GsData.db`） |

图片以直链形式交给适配器发送，插件本地不缓存图片。

<br/>

## 丨常见问题

- **被戳了没反应**：依次确认 `enable_poke` 是开的、`poke_probability` 没被调低、`cooldown_seconds` 冷却已经过去。
- **群里别人被戳也会回**：把 `only_poke_bot` 打开。
- **一直取不到图**：多为上游接口波动，稍后再试；日志里会有 `[PokeEmoji] 没有取到可用表情包` 的提示。

<br/>

## 丨致谢与开源声明

- 表情包数据与公开接口：[emoji.wuwa.games](https://emoji.wuwa.games/)；接口服务：[api.emoji.jaspin.top](https://api.emoji.jaspin.top/)
- 插件图标取自 emoji.wuwa.games 的站点图标。
- 帮助图的 banner 与命令图标沿用 [XutheringWavesUID](https://github.com/Loping151/XutheringWavesUID)（[WutheringWavesUID](https://github.com/tyql688/WutheringWavesUID) 的构建版，GPL-3.0-or-later）的素材。
- 感谢呜哇小站提供公开的表情包资源与接口；本插件只是 GsCore 侧的第三方调用方，版权与许可仍归原作者及上游项目所有。
- 本项目采用 [MIT](./LICENSE) 协议开源，仅供学习与交流使用。
