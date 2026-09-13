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
> 图源有两路：**优先**调随机表情接口，接口连不上、报错或该角色没有图时，**自动回落**到本地表情包目录，
> 两边都不需要 API Key。建议两份都备好：接口开箱即用，本地目录（用 [wuwa_emoji_crawler.py](https://github.com/xxuanzQAQ/PokeEmoji)
> 这类爬虫备份，默认 `/sd/root_data/wuwa表情包/wuwa_emojis`）保证接口抽风时机器人照样有反应。
> 装好后可到 **WebConsole → 插件配置 → `PokeEmoji`** 调整 `enable_api` / `api_base` / `emoji_dir`
> （也可以用环境变量 `POKEEMOJI_API_BASE` / `POKEEMOJI_EMOJI_DIR`）。

<br/>

## 丨快速上手

装好后在聊天窗口发一条 `ww帮助` 就能拿到一张帮助图。插件名 `PokeEmoji`，前缀 `ww`（`WW` 同效，也可以不带前缀直接发指令），别名 `pokeemoji` / `戳一戳表情`。

### 常用指令

| 触发指令 | 功能说明 |
| :--- | :--- |
| （被戳一戳，元事件） | 自动回一张表情包 |
| `ww随机表情` | 随机角色、随机来一张 |
| `ww随机表情 尤诺` | 指定角色（角色名或接口里的角色 id；本地的 `·`、大小写差异会自动归一） |
| `ww表情包列表` | 列出可用的角色与图片数量，只在本地区有的会标注「仅本地」 |
| `ww表情设置` | 查看本会话当前的戳一戳角色 |
| `ww表情设置 尤诺` | 把本会话切成某个角色 |
| `ww表情设置 随机` | 取消本会话设置，回到全局默认角色 |
| `ww表情包帮助` | 返回一张帮助图 |

<br/>

## 丨功能特色

- **戳一戳自动回图**：走 `poke` 元事件，不需要 @ 机器人。
- **帮助出图**：`ww帮助` 直接返回一张版式化的帮助图，同时挂进 Core 的插件帮助一览；命令前的图标直接复用 XutheringWavesUID 的图标集。
- **接口优先、本地兜底**：先请求接口直链取图（不占机器人带宽、图也更全）；接口不可用时自动读本地目录，站点挂了也不至于没反应。
- **无需鉴权**：两路都不需要 API Key，装上就能用。
- **角色可选**：命令里写角色名（或接口的角色 id）抽指定角色；本地目录改名、大小写、`·` 之类的写法差异会自动归一。
- **会话级偏好**：`表情设置` 的结果落库，群聊按群共享、私聊各记各的，互不干扰。
- **打扰程度可控**：回复概率、同会话冷却、是否只回应戳机器人自己，都能在控制台调。
- **开销小**：接口角色索引缓存 10 分钟、本地目录扫描缓存 1 分钟；走接口时只发一个 GET，走本地时才读盘，10MB 级的大图不会常驻内存。
- **改完即生效**：所有开关与阈值都在 WebConsole 改，不需要重启 Core。

<br/>

## 丨配置项

WebConsole → 插件配置 → `PokeEmoji`。

| 配置键 | 默认 | 说明 |
| :--- | :--- | :--- |
| `enable_api` | `true` | 优先走接口；关掉后只用本地目录 |
| `api_base` | 接口提供方地址 | 接口基础地址，一般无需修改；留空时读环境变量 `POKEEMOJI_API_BASE` |
| `emoji_dir` | `/sd/root_data/wuwa表情包/wuwa_emojis` | 备用图源：本地表情包根目录，一级子目录名即角色名；留空时读环境变量 `POKEEMOJI_EMOJI_DIR` |
| `default_character` | 空 | 默认角色，填角色名（如 `尤诺`）；留空表示随机角色 |
| `request_timeout` | `10` | 接口超时(秒)，超时同样会回落到本地 |
| `enable_poke` | `true` | 是否响应戳一戳 |
| `only_poke_bot` | `true` | 只在被戳对象是机器人自己时回复 |
| `allow_user_setting` | `true` | 允许用户用「表情设置」切换本会话角色 |
| `poke_probability` | `100` | 回复概率(%)，`100` 表示每次都回 |
| `cooldown_seconds` | `10` | 同一会话两次自动回复的最小间隔，`0` 不限制 |

> [!NOTE]
> `emoji_dir` 的目录结构就是爬虫脚本的输出：`<emoji_dir>/<角色>/<表情图片>`，
> 目录里的非图片文件（例如爬虫写的 `.crawler_state.json`）会被忽略。新增或删减角色目录后
> 最多 1 分钟（扫描缓存 TTL）就会反映到 `表情包列表` 里。
>
> 接口的角色索引与本地目录的扫描结果都只在插件进程内缓存（分别是 10 分钟 / 1 分钟），
> 不会落盘；接口返回「没有这个角色」时按兜底处理，直接读本地目录，不打扰用户。

<br/>

## 丨会话级设置

`表情设置` 写入 `pokeemojisetting` 表（`bot_id` + `scope_id` 唯一）：

- 群聊记 `group_<群号>` —— 同一个群里所有人共用一份设置；
- 私聊记 `user_<用户号>` —— 各记各的；
- 用户没设置过，或管理员关掉 `allow_user_setting` 时，一律回落到 `default_character`。

> 字段语义从旧版的「分类筛选」换成了「角色」，但数据库列名仍是 `filter_key`，
> 这样老库升级时不会因为缺列而查不动；旧值不在本地目录里时发图会提示角色不存在，重设一次即可。

<br/>

## 丨数据存储

| 内容 | 位置 |
| :--- | :--- |
| 插件配置 | `data/PokeEmoji/config.json` |
| 会话设置 | SQLite 表 `pokeemojisetting`（默认 `data/GsData.db`） |

接口取图时直接把直链交给适配器；本地兜底时以「读文件 + base64」的形式发送。插件不复制、
不落盘缓存图源文件，只在内存里缓存接口角色索引（TTL 600 秒）与本地角色目录的扫描结果（TTL 60 秒）。

<br/>

## 丨常见问题

- **被戳了没反应**：依次确认 `enable_poke` 是开的、`poke_probability` 没被调低、`cooldown_seconds` 冷却已经过去。
- **接口挂了**：不用管，插件会自动读本地目录；两路都没有图时才会提示，日志里带 `[PokeEmoji]` 前缀的 `debug`/`warning` 会写明原因。
- **提示目录不存在**：`emoji_dir` 没指对，或者那份备份还没下载/被挪走了；日志与聊天提示里都会带上实际路径。
- **群里别人被戳也会回**：把 `only_poke_bot` 打开。
- **一直取不到图**：确认该角色目录里有图片文件（`.gif` / `.png` / `.jpg` / `.webp` 等）；日志里会有 `[PokeEmoji] 没有取到可用表情包` 的提示。
- **刚下的角色没出现在列表里**：扫描结果缓存 60 秒，或者新目录所在层级的 mtime 没变，稍等一下再发 `表情包列表`。

<br/>

## 丨致谢与开源声明

- 表情包数据：[emoji.wuwa.games](https://emoji.wuwa.games/)（另支持本地备份兜底）
- 插件图标取自 emoji.wuwa.games 的站点图标。
- 帮助图的 banner 沿用 [XutheringWavesUID](https://github.com/Loping151/XutheringWavesUID)（[WutheringWavesUID](https://github.com/tyql688/WutheringWavesUID) 的构建版，GPL-3.0-or-later）的素材；命令图标在渲染时直接读取同目录下 XutheringWavesUID 的 `wutheringwaves_help/icon_path`，本插件不再自带一份图标；没装 XW 时命令图标回落到框架自带的图标集。
- 感谢呜哇小站提供表情包资源、接口提供方提供随机表情接口；版权与许可仍归原作者及上游项目所有。
- 本项目采用 [MIT](./LICENSE) 协议开源，仅供学习与交流使用。
