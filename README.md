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

> [!IMPORTANT]
> 表情包数据来自 [emoji.wuwa.games](https://emoji.wuwa.games/) 的随机表情接口，需要 API Key 才能调用。
> 装好后请到 **WebConsole → 插件配置 → `PokeEmoji`** 把 `api_key` 填上（也可以用环境变量 `POKEEMOJI_API_KEY`）。
> 没配 Key 时插件只会提示鉴权失败，不影响 Core 的其它功能。

<br/>

## 丨快速上手

装好后在聊天窗口发一条 `ww帮助` 就能拿到一张帮助图。插件名 `PokeEmoji`，前缀 `ww`（`WW` 同效，也可以不带前缀直接发指令），别名 `pokeemoji` / `戳一戳表情`。

### 常用指令

| 触发指令 | 功能说明 |
| :--- | :--- |
| （被戳一戳，元事件） | 自动回一张表情包 |
| `ww随机表情` | 随机角色、随机来一张 |
| `ww随机表情 尤诺` | 指定角色（slug 或完整名称都行） |
| `ww随机表情 尤诺 webp` | 同时指定角色与图片格式 |
| `ww随机表情 webp` | 只切格式，角色仍走随机/本会话设置 |
| `ww表情包列表` | 列出当前可用的角色 |
| `ww表情设置` | 查看本会话当前的戳一戳角色 |
| `ww表情设置 尤诺` | 把本会话切成某个角色 |
| `ww表情设置 随机` | 取消本会话设置，回到全局默认角色 |
| `ww表情包帮助` | 返回一张帮助图 |

<br/>

## 丨功能特色

- **戳一戳自动回图**：走 `poke` 元事件，不需要 @ 机器人。
- **帮助出图**：`ww帮助` 直接返回一张版式化的帮助图，同时挂进 Core 的插件帮助一览；命令前的图标直接复用 XutheringWavesUID 的图标集。
- **角色与格式可选**：命令里写角色名 / slug 抽指定角色，写 `webp` / `原图` 切图片格式。
- **会话级偏好**：`表情设置` 的结果落库，群聊按群共享、私聊各记各的，互不干扰。
- **打扰程度可控**：回复概率、同会话冷却、是否只回应戳机器人自己，都能在控制台调。
- **额度友好**：接口的角色索引带短 TTL 缓存；取图只在真正要发的时候打一次接口，出错不自动重试。
- **改完即生效**：所有开关与阈值都在 WebConsole 改，不需要重启 Core。

<br/>

## 丨配置项

WebConsole → 插件配置 → `PokeEmoji`。

| 配置键 | 默认 | 说明 |
| :--- | :--- | :--- |
| `api_base` | 接口提供方地址 | 接口基础地址，一般无需修改 |
| `api_key` | 空 | 接口密钥（`secret`，前端隐藏）；留空时读环境变量 `POKEEMOJI_API_KEY` |
| `default_character` | 空 | 默认角色，可填 slug 或完整名称；留空表示随机角色 |
| `image_format` | `original` | `original` 取原图 / `webp` 取 WebP 图 |
| `enable_poke` | `true` | 是否响应戳一戳 |
| `only_poke_bot` | `true` | 只在被戳对象是机器人自己时回复 |
| `allow_user_setting` | `true` | 允许用户用「表情设置」切换本会话角色 |
| `poke_probability` | `100` | 回复概率(%)，`100` 表示每次都回 |
| `cooldown_seconds` | `10` | 同一会话两次自动回复的最小间隔，`0` 不限制 |
| `request_timeout` | `20` | 接口超时(秒) |

> [!NOTE]
> 接口两个端点（随机取图 / 角色索引）共用同一个每分钟额度。插件不会自动重试失败请求；
> 遇到 `429` 会按响应里的 `Retry-After` 提示还要等多久，`401` 则说明 Key 无效或已过期。

<br/>

## 丨会话级设置

`表情设置` 写入 `pokeemojisetting` 表（`bot_id` + `scope_id` 唯一）：

- 群聊记 `group_<群号>` —— 同一个群里所有人共用一份设置；
- 私聊记 `user_<用户号>` —— 各记各的；
- 用户没设置过，或管理员关掉 `allow_user_setting` 时，一律回落到 `default_character`。

> 字段语义从旧版的「分类筛选」换成了「角色」，但数据库列名仍是 `filter_key`，
> 这样老库升级时不会因为缺列而查不动；旧值不是合法角色时接口会报 404，重设一次即可。

<br/>

## 丨数据存储

| 内容 | 位置 |
| :--- | :--- |
| 插件配置 | `data/PokeEmoji/config.json` |
| 会话设置 | SQLite 表 `pokeemojisetting`（默认 `data/GsData.db`） |

图片以直链形式交给适配器发送，插件本地不缓存图片；接口响应也不做落盘缓存。

<br/>

## 丨常见问题

- **被戳了没反应**：依次确认 `enable_poke` 是开的、`poke_probability` 没被调低、`cooldown_seconds` 冷却已经过去。
- **提示鉴权失败**：检查 `api_key` 是否填写完整（`Bearer` 与密钥之间只留一个空格由插件自动处理），以及密钥是否已过期。
- **群里别人被戳也会回**：把 `only_poke_bot` 打开。
- **一直取不到图**：可能该角色没有对应格式的表情，或上游接口波动；日志里会有 `[PokeEmoji] 没有取到可用表情包` 的提示。
- **抽不到刚出的角色**：接口的角色索引与新增表情可能延迟约 5 分半，稍后再试。

<br/>

## 丨致谢与开源声明

- 表情包数据与随机表情接口：[emoji.wuwa.games](https://emoji.wuwa.games/)
- 插件图标取自 emoji.wuwa.games 的站点图标。
- 帮助图的 banner 沿用 [XutheringWavesUID](https://github.com/Loping151/XutheringWavesUID)（[WutheringWavesUID](https://github.com/tyql688/WutheringWavesUID) 的构建版，GPL-3.0-or-later）的素材；命令图标在渲染时直接读取同目录下 XutheringWavesUID 的 `wutheringwaves_help/icon_path`，本插件不再自带一份图标；没装 XW 时命令图标回落到框架自带的图标集。
- 感谢呜哇小站提供表情包资源与接口；本插件只是 GsCore 侧的第三方调用方，版权与许可仍归原作者及上游项目所有。
- 本项目采用 [MIT](./LICENSE) 协议开源，仅供学习与交流使用。
