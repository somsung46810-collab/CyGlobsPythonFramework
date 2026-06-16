from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install Pillow first: pip install pillow") from exc

FRAMEBUFFER_PATH = Path("cyglobs_fast_and_furious_framebuffer.txt")
OUTPUT_PATH = Path("cyglobs_fast_and_furious_scene.png")

Color = Tuple[int, int, int]

BG: Color = (6, 8, 18)
GRID: Color = (24, 58, 92)
BLUE: Color = (40, 185, 255)
BLUE_GLOW: Color = (70, 220, 255)
RED: Color = (255, 55, 45)
GREEN: Color = (70, 255, 120)
WHITE: Color = (230, 245, 255)
YELLOW: Color = (255, 210, 90)


def ensure_framebuffer() -> str:
    """Read the CyGlobs framebuffer, generating it when the source script is available."""
    if FRAMEBUFFER_PATH.exists():
        return FRAMEBUFFER_PATH.read_text(encoding="utf-8")

    try:
        from fast_street_race_pipeline import build_fast_race_scene
    except ImportError as exc:
        raise SystemExit(
            "Missing cyglobs_fast_and_furious_framebuffer.txt. "
            "Run fast_street_race_pipeline.py first, or run this script from the example folder."
        ) from exc

    scene = build_fast_race_scene(radius=0.62)
    text = scene.render_ascii()
    FRAMEBUFFER_PATH.write_text(text, encoding="utf-8")
    return text


def parse_points(framebuffer: str) -> dict[str, list[tuple[int, int]]]:
    points = {"#": [], "R": [], "G": [], ".": []}
    lines = framebuffer.splitlines()
    max_width = max((len(line) for line in lines), default=1)
    height = max(len(lines), 1)
    for y, line in enumerate(lines):
        for x, ch in enumerate(line):
            if ch in points:
                sx = int(70 + (x / max_width) * 1160)
                sy = int(90 + (y / height) * 420)
                points[ch].append((sx, sy))
    return points


def draw_polyline_points(draw: ImageDraw.ImageDraw, points: Iterable[tuple[int, int]], color: Color, radius: int = 2) -> None:
    for x, y in points:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def draw_wire_car(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, color: Color) -> None:
    body = [
        (cx - int(120 * scale), cy),
        (cx - int(75 * scale), cy - int(45 * scale)),
        (cx + int(45 * scale), cy - int(55 * scale)),
        (cx + int(125 * scale), cy - int(5 * scale)),
        (cx + int(100 * scale), cy + int(35 * scale)),
        (cx - int(105 * scale), cy + int(35 * scale)),
    ]
    draw.line(body + [body[0]], fill=color, width=max(2, int(4 * scale)))
    cabin = [
        (cx - int(45 * scale), cy - int(43 * scale)),
        (cx - int(5 * scale), cy - int(78 * scale)),
        (cx + int(50 * scale), cy - int(50 * scale)),
    ]
    draw.line(cabin, fill=color, width=max(2, int(3 * scale)))
    for wx in (cx - int(70 * scale), cx + int(75 * scale)):
        draw.ellipse((wx - int(22 * scale), cy + int(20 * scale), wx + int(22 * scale), cy + int(64 * scale)), outline=color, width=max(2, int(4 * scale)))
        draw.ellipse((wx - int(7 * scale), cy + int(35 * scale), wx + int(7 * scale), cy + int(49 * scale)), outline=BLUE_GLOW, width=2)
    for offset in range(0, 36, 12):
        draw.line((cx - int(135 * scale) - offset, cy + int(8 * scale), cx - int(210 * scale) - offset, cy + int(8 * scale)), fill=YELLOW, width=2)


def draw_cube(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: Color, dashed: bool = False) -> None:
    x1, y1, x2, y2 = box
    dx, dy = 34, -28
    front = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
    back = [(x1 + dx, y1 + dy), (x2 + dx, y1 + dy), (x2 + dx, y2 + dy), (x1 + dx, y2 + dy), (x1 + dx, y1 + dy)]
    segments = list(zip(front, front[1:])) + list(zip(back, back[1:])) + [((x1, y1), (x1 + dx, y1 + dy)), ((x2, y1), (x2 + dx, y1 + dy)), ((x2, y2), (x2 + dx, y2 + dy)), ((x1, y2), (x1 + dx, y2 + dy))]
    for a, b in segments:
        if dashed:
            dash_line(draw, a, b, color, width=3)
        else:
            draw.line((*a, *b), fill=color, width=3)


def dash_line(draw: ImageDraw.ImageDraw, a: tuple[int, int], b: tuple[int, int], color: Color, width: int = 2, dash: int = 12) -> None:
    ax, ay = a
    bx, by = b
    steps = max(abs(bx - ax), abs(by - ay), 1)
    for start in range(0, steps, dash * 2):
        end = min(start + dash, steps)
        p1 = (int(ax + (bx - ax) * start / steps), int(ay + (by - ay) * start / steps))
        p2 = (int(ax + (bx - ax) * end / steps), int(ay + (by - ay) * end / steps))
        draw.line((*p1, *p2), fill=color, width=width)


def draw_scene(framebuffer: str) -> Image.Image:
    img = Image.new("RGB", (1280, 720), BG)
    draw = ImageDraw.Draw(img)

    # Horizon and street perspective.
    draw.rectangle((0, 0, 1280, 360), fill=(5, 8, 22))
    draw.polygon([(0, 720), (510, 330), (770, 330), (1280, 720)], fill=(18, 20, 28))
    for i in range(18):
        y = 350 + i * 23
        draw.line((0, y, 1280, y + i * 5), fill=GRID, width=1)
    for x in range(-500, 1800, 110):
        draw.line((640, 330, x, 720), fill=GRID, width=1)
    for y in range(380, 720, 72):
        draw.line((628, y, 652, y), fill=YELLOW, width=5)

    # City light bars.
    for x, h in [(80, 210), (160, 140), (230, 260), (990, 180), (1080, 250), (1160, 150)]:
        draw.rectangle((x, 330 - h, x + 42, 330), outline=BLUE, width=2)
        for wy in range(330 - h + 14, 320, 26):
            draw.line((x + 8, wy, x + 34, wy), fill=(35, 115, 160), width=1)

    points = parse_points(framebuffer)
    draw_polyline_points(draw, points["."], GRID, 1)
    draw_polyline_points(draw, points["R"], RED, 2)
    draw_polyline_points(draw, points["G"], GREEN, 2)
    draw_polyline_points(draw, points["#"], BLUE_GLOW, 2)

    # Cinematic object interpretation from the framebuffer symbols.
    draw_cube(draw, (330, 445, 610, 600), RED, dashed=False)
    draw_wire_car(draw, 470, 545, 1.0, BLUE)
    draw_wire_car(draw, 800, 500, 0.74, BLUE_GLOW)
    draw_cube(draw, (780, 390, 1030, 545), GREEN, dashed=True)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 24)
        small = ImageFont.truetype("DejaVuSans.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
        small = ImageFont.load_default()

    draw.text((42, 34), "CyGlobs Fast and Furious Example", fill=WHITE, font=font)
    draw.text((42, 66), "blue wireframe -> red restraint cube -> green dashed MVP checkpoint", fill=BLUE_GLOW, font=small)
    draw.text((42, 90), "source: cyglobs_fast_and_furious_framebuffer.txt | radius=.62 | clip-space pipeline", fill=GREEN, font=small)
    return img


def main() -> None:
    framebuffer = ensure_framebuffer()
    img = draw_scene(framebuffer)
    img.save(OUTPUT_PATH)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
