"""PIL 渲染戳一戳统计和表情包列表。"""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageDraw

from gsuid_core.utils.fonts.fonts import core_font
from gsuid_core.utils.image.convert import convert_img

from ..pokeemoji_source.types import CharacterItem, name_key

WIDTH = 960
BG = (245, 247, 251)
CARD = (255, 255, 255)
TEXT = (34, 39, 48)
MUTED = (112, 120, 133)
ACCENT = (89, 112, 218)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _placeholder(name: str, size: int) -> Image.Image:
    image = Image.new("RGB", (size, size), (224, 230, 242))
    draw = ImageDraw.Draw(image)
    font = core_font(max(22, size // 4))
    draw.text((size // 2, size // 2), name[:1] or "?", fill=ACCENT, font=font, anchor="mm")
    return image


def _load_image(value: str | Path | None, size: int, downloaded: bytes | None = None) -> Image.Image:
    try:
        if downloaded is not None:
            image = Image.open(BytesIO(downloaded))
        elif value is not None:
            image = Image.open(value)
        else:
            raise OSError
        image.seek(0)  # 动图取首帧，避免把整段 GIF 嵌入列表图
        image = image.convert("RGB")
        image.thumbnail((size, size))
        canvas = Image.new("RGB", (size, size), (238, 240, 245))
        canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
        return canvas
    except (OSError, ValueError, EOFError):
        return _placeholder("?", size)


async def _download_thumbnails(items: list[CharacterItem]) -> dict[str, bytes]:
    remote = [
        (item.name, item.thumbnail)
        for item in items
        if isinstance(item.thumbnail, str) and item.thumbnail.startswith(("http://", "https://"))
    ]
    if not remote:
        return {}
    result: dict[str, bytes] = {}
    semaphore = asyncio.Semaphore(8)
    timeout = httpx.Timeout(connect=3.0, read=6.0, write=3.0, pool=3.0)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:

        async def fetch(name: str, url: str) -> None:
            async with semaphore:
                try:
                    response = await client.get(url)
                    if response.status_code == 200 and response.content:
                        result[name] = response.content
                except httpx.HTTPError:
                    pass

        await asyncio.gather(*(fetch(name, url) for name, url in remote))
    return result


async def render_character_list(items: list[CharacterItem]) -> bytes:
    """渲染角色卡片；卡片只显示名称和缩略图，不显示数量。"""
    items = list(items)
    cols, card_w, thumb = 4, 220, 150
    gap, margin, header_h, card_h = 16, 24, 94, 214
    rows = max(1, (len(items) + cols - 1) // cols)
    image = Image.new("RGB", (WIDTH, header_h + margin + rows * card_h + (rows - 1) * gap + margin), BG)
    draw = ImageDraw.Draw(image)
    title_font = core_font(34)
    sub_font = core_font(19)
    draw.text((margin, 28), "表情包列表", fill=TEXT, font=title_font)
    draw.text((margin, 70), "选择一个角色，发送「随机表情 角色名」即可抽取", fill=MUTED, font=sub_font)
    downloaded = await _download_thumbnails(items)
    name_font = core_font(23)

    for index, item in enumerate(items):
        row, col = divmod(index, cols)
        x = margin + col * (card_w + gap)
        y = header_h + row * (card_h + gap)
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=16, fill=CARD)
        thumb_img = _load_image(item.thumbnail, thumb, downloaded.get(item.name))
        image.paste(thumb_img, (x + (card_w - thumb) // 2, y + 14))
        label = item.name
        tw, _ = _text_size(draw, label, name_font)
        if tw > card_w - 20:
            while label and _text_size(draw, label + "…", name_font)[0] > card_w - 20:
                label = label[:-1]
            label += "…"
        draw.text((x + card_w // 2, y + thumb + 34), label, fill=TEXT, font=name_font, anchor="mm")
    return await convert_img(image)


async def render_ranking(rows: list[tuple[str, int]], *, max_rows: int = 15) -> bytes:
    merged: dict[str, tuple[str, int]] = {}
    for raw_name, raw_count in rows:
        name = raw_name.strip() or "随机"
        key = name_key(name) or name
        shown, count = merged.get(key, (name, 0))
        merged[key] = (shown, count + max(0, int(raw_count)))
    ranking = sorted(merged.values(), key=lambda item: (-item[1], item[0]))
    total = sum(max(0, count) for _, count in ranking)
    if total <= 0:
        image = Image.new("RGB", (WIDTH, 240), BG)
        draw = ImageDraw.Draw(image)
        draw.text((WIDTH // 2, 90), "戳一戳统计", fill=TEXT, font=core_font(34), anchor="mm")
        draw.text(
            (WIDTH // 2, 150), "还没有戳一戳记录，被戳几次再来看看吧。", fill=MUTED, font=core_font(20), anchor="mm"
        )
        return await convert_img(image)
    visible = ranking[:max_rows]
    row_h, margin, header_h = 62, 28, 124
    image = Image.new("RGB", (WIDTH, header_h + margin + len(visible) * row_h + margin), BG)
    draw = ImageDraw.Draw(image)
    draw.text((margin, 26), "戳一戳统计", fill=TEXT, font=core_font(34))
    draw.text((margin, 75), f"共 {total} 次 · {len(ranking)} 个角色", fill=MUTED, font=core_font(20))
    top = max(1, visible[0][1])
    name_font, count_font = core_font(23), core_font(20)
    for index, (name, count) in enumerate(visible, start=1):
        y = header_h + index * row_h - 20
        draw.text((margin, y), f"{index:>2}. {name}", fill=TEXT, font=name_font, anchor="lm")
        bar_x, bar_y, bar_w, bar_h = 400, y - 10, 380, 18
        draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=9, fill=(225, 229, 239))
        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + max(8, round(bar_w * count / top)), bar_y + bar_h), radius=9, fill=ACCENT
        )
        draw.text(
            (bar_x + bar_w + 18, y), f"{count} 次  {count / total * 100:.1f}%", fill=MUTED, font=count_font, anchor="lm"
        )
    return await convert_img(image)
