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

- 环境要求：Core 使用的 Python 需 ≥ 3.11；依赖 `httpx`、`pillow`（Core 开启「自动安装依赖」时会自动装好，也可以手动 `pip install httpx pillow`）。
- 手动安装：把本仓库 `git clone` 到 Core 安装目录下的 `gsuid_core/plugins/`（和外层其它插件同级，目录名保持 `PokeEmoji`），再发 `core重启`；WebConsole → 插件配置里能看到 `PokeEmoji` 即为装好。

> [!IMPORTANT]
> 图源有两路：**优先**调随机表情接口，接口连不上、报错或该角色没有图时，**自动回落**到本地表情包目录，
> 两边都不需要 API Key，装上就能用。接口开箱即用；本地目录是可选备份，默认在 Core 数据目录的
> `PokeEmoji/emojis` 下，想用自己的表情包再改配置即可。

<br/>

## 丨快速上手

装好后在聊天窗口发一条 `ww表情包帮助` 就能拿到一张帮助图。插件名 `PokeEmoji`，前缀 `ww`（`WW` 同效，也可以不带前缀直接发指令），别名 `pokeemoji` / `戳一戳表情`。

> 前缀 `ww` 与 [XutheringWavesUID](https://github.com/Loping151/XutheringWavesUID) 相同，两边命令词不重叠，可以共存；本插件 `allow_empty_prefix=True`，不带前缀直接发「随机表情」这类命令也能触发。

### 常用指令

| 触发指令 | 功能说明 |
| :--- | :--- |
| （被戳一戳，元事件） | 自动回一张表情包 |
| `ww随机表情` | 随机角色、随机来一张 |
| `ww随机表情 尤诺` | 指定角色（角色名或接口里的角色 id；本地的 `·`、大小写差异会自动归一） |
| `ww表情包列表` | 以图片卡片列出可用角色与对应缩略图，只在本地区有的标注「仅本地」、本 bot 专属的标注「专属」 |
| `ww表情设置` | 查看本会话当前的戳一戳角色 |
| `ww表情设置 尤诺` | 把本会话切成某个角色 |
| `ww表情设置 随机` | 取消本会话设置，回到全局默认角色 |
| `ww戳一戳统计` | 以图片卡片展示按角色排名的出图次数（戳一戳 + 随机表情） |
| `ww表情包帮助` | 返回一张帮助图 |

<br/>

## 丨功能特色

- **戳一戳自动回图**：走 `poke` 元事件，不需要 @ 机器人。
- **帮助出图**：`ww表情包帮助` 直接返回一张版式化的帮助图，同时挂进 Core 的插件帮助一览.
- **接口优先、本地兜底**：接口这一路只把直链交给协议端/QQ 去取（插件不下载、不中转）；接口不可用时自动读本地目录，站点挂了也不至于没反应。
- **无需鉴权**：两路都不需要 API Key，装上就能用。
- **角色可选**：命令里写角色名（或接口的角色 id）抽指定角色；本地目录改名、大小写、`·` 之类的写法差异会自动归一。
- **会话级偏好**：`表情设置` 的结果落库，群聊按群共享、私聊各记各的，互不干扰。
- **bot 专属分类**：本地目录里用 bot 标识命名的分类只有那个 bot 能用，其他 bot 列表看不到、也切不过去。
- **出图统计**：戳一戳自动回图、`随机表情` 手动抽图，每次成功出一张都按角色记一笔；`戳一戳统计` 给出按角色排名的榜单（总次数、各角色次数、占比与条形图），随机角色归到「随机」名下。
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
| `emoji_dir` | 数据目录 `PokeEmoji/emojis` | 备用图源（可选）：本地表情包根目录，一级子目录名即角色名（bot 标识命名的目录是专属分类，见下节）；留空时读环境变量 `POKEEMOJI_EMOJI_DIR` |
| `default_character` | 空 | 默认角色，填角色名（如 `尤诺`）；留空表示随机角色 |
| `request_timeout` | `10` | 接口超时(秒)，超时同样会回落到本地 |
| `enable_poke` | `true` | 是否响应戳一戳 |
| `only_poke_bot` | `true` | 只在被戳对象是机器人自己时回复 |
| `allow_user_setting` | `true` | 允许用户用「表情设置」切换本会话角色 |
| `poke_probability` | `100` | 回复概率(%)，`100` 表示每次都回 |
| `cooldown_seconds` | `10` | 同一会话两次自动回复的最小间隔，`0` 不限制 |

<br/>

## 丨会话级设置

`表情设置` 写入 `pokeemojisetting` 表（`bot_id` + `scope_id` 唯一）：

- 群聊记 `group_<群号>` —— 同一个群里所有人共用一份设置；
- 私聊记 `user_<用户号>` —— 各记各的；
- 用户没设置过，或管理员关掉 `allow_user_setting` 时，一律回落到 `default_character`。

<br/>

## 丨bot 专属分类

想让某个 bot 独享一份表情包时，在 `emoji_dir` 下按它的标识建目录，这份分类就只有它能用：
其他 bot 的 `表情包列表` 里看不到，`表情设置` / `随机表情` 指定同一个名字也会被挡下来
（提示「是 bot xxx 的专属分类」），抽随机图时同样不会抽到别人的专属目录。

```
<emoji_dir>/
├── 爱弥斯/              # 公共分类：所有 bot 都能用
├── 3776946954/         # bot 专属分类：只有 bot 3776946954 能用
│   ├── 1.gif           #   直接放图 → 这一层就是一个分类，名字即目录名
│   └── 打工人/          #   再分一层 → 每个子目录是一个分类，名字更好写
│       └── 加班.gif
└── 珂莱塔/
```

目录名的识别规则（不区分大小写）：

- 纯数字且不少于 5 位 —— 按 bot 账号（`bot_self_id`，例如 QQ 号）算，推荐这种；
- `bot_` / `bot-` / `qq_` / `qq-` 前缀 —— 前缀后面就是 bot 标识，账号不是数字时用这种；
- 其余目录名一律当公共分类。

归属比对同时认 `bot_id`（适配器名，如 `onebot`）与 `bot_self_id`（账号），所以按账号命名最精确：
同一适配器下的其他账号用不了这份分类。专属目录里若出现与公共分类同名的分类（例如上面再放一个
`3776946954/尤诺/`），对这个 bot 来说专属的那份优先，接口里同名的角色也不会顶掉它。

<br/>

## 丨数据存储

| 内容 | 位置 |
| :--- | :--- |
| 插件配置 | `data/PokeEmoji/config.json` |
| 会话设置 | SQLite 表 `pokeemojisetting`（默认 `data/GsData.db`） |
| 戳一戳统计 | SQLite 表 `pokeemojistat`（默认 `data/GsData.db`） |

接口取图时直接把直链交给适配器；本地兜底时以「读文件 + base64」的形式发送。插件不复制、
不落盘缓存图源文件，只在内存里缓存接口角色索引（TTL 600 秒）与本地角色目录的扫描结果（TTL 60 秒）。

<br/>

## 丨常见问题

- **被戳了没反应**：依次确认 `enable_poke` 是开的、`poke_probability` 没被调低、`cooldown_seconds` 冷却已经过去。
- **发表情慢 / 想让协议端自己取图**：Core 的「发送图片方式」默认是 `base64`，会把接口直链先下载回来再转 base64 发出去（大图还会撞上内部 12 秒下载超时导致这条消息直接失败）。在 WebConsole → 配置里把 OneBot 的发送方式改成 `link`，接口图就会以链接形式直接交给协议端；本地兜底的图是本机文件，仍走 base64，不受影响。
- **接口挂了**：不用管，插件会自动读本地目录；两路都没有图时才会提示，日志里带 `[PokeEmoji]` 前缀的 `debug`/`warning` 会写明原因。
- **想用自己的表情包**：把图片按「`emoji_dir`/角色名/xxx.gif」放好，或在 WebConsole 里把 `emoji_dir` 指到自己的目录；默认目录是数据目录下的 `PokeEmoji/emojis`，空目录不会报错，只是本地兜底没有图。
- **群里别人被戳也会回**：把 `only_poke_bot` 打开。
- **一直取不到图**：确认该角色目录里有图片文件（`.gif` / `.png` / `.jpg` / `.webp` 等）；日志里会有 `[PokeEmoji] 没有取到可用表情包` 的提示。
- **刚下的角色没出现在列表里**：扫描结果缓存 60 秒，或者新目录所在层级的 mtime 没变，稍等一下再发 `表情包列表`。
- **切不过某个分类**：如果提示「是 bot xxx 的专属分类」，说明这个目录名是那个 bot 的标识；改名成普通角色名，或者换成由那个 bot 自己来用。

<br/>

## 丨致谢与开源声明

- 表情包数据：[emoji.wuwa.games](https://emoji.wuwa.games/)（另支持本地备份兜底）
- 帮助图的 banner 与命令图标素材来自 [XutheringWavesUID](https://github.com/Loping151/XutheringWavesUID)（[WutheringWavesUID](https://github.com/tyql688/WutheringWavesUID) 的构建版，GPL-3.0-or-later）：命令图标在渲染时直接读它的 `wutheringwaves_help/icon_path`，本插件不再自带一份，没装 XW 时回落到 Core 自带的图标集
- 感谢呜哇小站提供表情包资源、接口提供方提供随机表情接口；版权与许可仍归原作者及上游项目所有。
- 本项目采用 [MIT](./LICENSE) 协议开源，仅供学习与交流使用。

<br/>

## 丨许可说明

- **代码**：以 [MIT](./LICENSE) 开源。
- **帮助图素材**：`PokeEmoji/pokeemoji_help/texture2d/banner_bg.jpg` 沿用 XutheringWavesUID（GPL-3.0-or-later）的素材，二次分发请一并遵守该素材的许可，或替换成自己的图。
- **表情包图片**：来自 [emoji.wuwa.games](https://emoji.wuwa.games/)，版权归原作者所有；本仓库不打包任何表情包图片。
