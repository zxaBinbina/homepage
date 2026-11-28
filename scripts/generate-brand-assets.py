"""Generate brand image assets from the favicon glyph and site palette.

Outputs (all under public/):
  - favicon-16x16.png / favicon-32x32.png   rounded dark tile, matches favicon.svg
  - apple-touch-icon.png (180) / icon-192.png / icon-512.png  full-bleed tiles for PWA & iOS
  - images/share-cover.png (1200x630)       Open Graph / Twitter share cover

Run: python3 scripts/generate-brand-assets.py
Only the Python standard library and Pillow are required; no network access.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

INK = (20, 21, 33)  # #141521 site dark background
ACCENT = (78, 164, 239)  # #4ea4ef sky-blue accent
TEXT_PRIMARY = (244, 246, 250)  # #f4f6fa
TEXT_SECONDARY = (159, 176, 204)
TEXT_MUTED = (124, 133, 152)

FONT_PATH = "/usr/share/fonts/google-noto-sans-mono-cjk-vf-fonts/NotoSansMonoCJK-VF.ttc"
FONT_SC_INDEX = 2  # Noto Sans Mono CJK SC face inside the TTC collection


def font(size: int, weight: int = 400) -> ImageFont.FreeTypeFont:
    loaded = ImageFont.truetype(FONT_PATH, size, index=FONT_SC_INDEX)
    try:
        loaded.set_variation_by_axes([weight])
    except Exception:
        pass  # Fall back to the Regular weight when variations are unavailable.
    return loaded


def rounded_tile(size: int, radius: int | None) -> Image.Image:
    """Draw the favicon tile at `size`; radius None keeps a full-bleed square."""
    scale = 8  # Supersample for smooth strokes, then downscale.
    canvas = size * scale
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    corner = radius * scale if radius is not None else 0
    draw.rounded_rectangle(
        (0, 0, canvas - 1, canvas - 1), radius=corner, fill=(*INK, 255)
    )
    draw_code_glyph(draw, canvas)
    return image.resize((size, size), Image.LANCZOS)


def draw_code_glyph(draw: ImageDraw.Draw, canvas: int, alpha: int = 255) -> None:
    """Replicate the favicon.svg `</>` strokes with round caps."""
    unit = canvas / 64
    stroke = max(1, round(5 * unit))
    points = {
        "left": [(26, 19), (13, 32), (26, 45)],
        "right": [(38, 19), (51, 32), (38, 45)],
        "slash": [(35, 16), (29, 48)],
    }
    color = (*ACCENT, alpha)
    for polyline in points.values():
        scaled = [(x * unit, y * unit) for x, y in polyline]
        draw.line(scaled, fill=color, width=stroke, joint="curve")
        for endpoint in (scaled[0], scaled[-1]):
            radius = stroke / 2
            draw.ellipse(
                (
                    endpoint[0] - radius,
                    endpoint[1] - radius,
                    endpoint[0] + radius,
                    endpoint[1] + radius,
                ),
                fill=color,
            )


def write_icons() -> None:
    rounded_tile(32, 10).save(PUBLIC / "favicon-32x32.png")
    rounded_tile(16, 5).save(PUBLIC / "favicon-16x16.png")
    rounded_tile(180, 0).save(PUBLIC / "apple-touch-icon.png")
    rounded_tile(192, 0).save(PUBLIC / "icon-192.png")
    rounded_tile(512, 0).save(PUBLIC / "icon-512.png")


def vertical_gradient(width: int, height: int, top: tuple, bottom: tuple) -> Image.Image:
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for row in range(height):
        ratio = row / (height - 1)
        color = tuple(round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, row), (width, row)], fill=color)
    return image


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def write_share_cover() -> None:
    width, height = 1200, 630
    cover = vertical_gradient(width, height, (20, 21, 33), (29, 35, 56)).convert("RGBA")
    overlay = Image.new("RGBA", cover.size, (0, 0, 0, 0))
    blocks = ImageDraw.Draw(overlay)

    # A faint grid of rounded squares echoes the Minecraft block motif.
    for row in range(4):
        for column in range(8):
            x = 620 + column * 76
            y = -24 + row * 76
            if x < width and y < height:
                blocks.rounded_rectangle(
                    (x, y, x + 56, y + 56),
                    radius=14,
                    outline=(*ACCENT, 14),
                    width=2,
                )
    # A large faint code glyph anchors the top-right corner.
    glyph_layer = Image.new("RGBA", cover.size, (0, 0, 0, 0))
    draw_code_glyph(ImageDraw.Draw(glyph_layer), 640, alpha=36)
    glyph = glyph_layer.resize((180, 180), Image.LANCZOS)
    overlay.alpha_composite(glyph, (972, 48))
    cover.alpha_composite(overlay)

    draw = ImageDraw.Draw(cover)

    # Avatar card on the left.
    avatar_size = 240
    avatar = Image.open(PUBLIC / "images/avatar.png").convert("RGBA").resize(
        (avatar_size, avatar_size), Image.LANCZOS
    )
    card_x, card_y = 88, 190
    shadow = Image.new("RGBA", cover.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (card_x - 6, card_y - 6, card_x + avatar_size + 6, card_y + avatar_size + 6),
        radius=44,
        fill=(0, 0, 0, 90),
    )
    cover.alpha_composite(shadow)
    cover.paste(avatar, (card_x, card_y), rounded_mask(avatar_size, 40))
    draw.rounded_rectangle(
        (card_x - 1, card_y - 1, card_x + avatar_size + 1, card_y + avatar_size + 1),
        radius=41,
        outline=(*ACCENT, 130),
        width=3,
    )

    text_x = card_x + avatar_size + 72

    def centered(y: int, text: str, size: int, color: tuple, weight: int = 400) -> None:
        face = font(size, weight)
        extent = draw.textlength(text, font=face)
        draw.text((text_x, y), text, font=face, fill=color)

    centered(150, "a彬彬a · 个人主页", 34, (120, 170, 220), 500)
    centered(206, "在代码与方块之间", 92, TEXT_PRIMARY, 700)
    centered(330, "创造一点不一样", 58, TEXT_SECONDARY, 400)
    centered(468, "开发项目 · Minecraft 悠哉世界 · 网页工具与小游戏", 30, TEXT_MUTED)

    # Small floating accents around the title block.
    for x, y, side in ((1064, 356, 26), (1112, 404, 18)):
        draw.rounded_rectangle((x, y, x + side, y + side), radius=7, outline=(*ACCENT, 60), width=2)

    draw.text((88, 566), "zxabinbina.cc.cd", font=font(28), fill=(86, 96, 121))
    cover.convert("RGB").save(PUBLIC / "images" / "share-cover.png", "PNG")


if __name__ == "__main__":
    write_icons()
    write_share_cover()
    print("brand assets generated under public/")
