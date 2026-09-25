"""Icon abstraction: vẽ icon vector bằng Pillow (lưới 24x24, nét 2px).

- Không tải từ Internet, không thêm dependency (Pillow đã có sẵn).
- Đồng nhất giữa các máy Windows, sắc nét ở mọi mức DPI (vẽ 2x + supersample).
- Kết quả được cache để không dựng lại ảnh nhiều lần.
"""

from __future__ import annotations

import math
from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageDraw

from vietzip.ui.theme import COLOR_TEXT_SECONDARY

_GRID = 24.0
_SUPER = 8  # hệ số supersample


def _hex_to_rgba(color: str) -> tuple[int, int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16), 255


class _Pen:
    """Bút vẽ theo lưới 24 đơn vị, tự scale lên canvas supersample."""

    def __init__(self, px: int, rgba: tuple[int, int, int, int]):
        self.px = px
        self.k = px / _GRID
        self.rgba = rgba
        self.w = max(1, round(2 * self.k))
        self.img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def _p(self, pt):
        return (pt[0] * self.k, pt[1] * self.k)

    def dot(self, pt, r=1.0):
        x, y = self._p(pt)
        rr = r * self.k
        self.d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=self.rgba)

    def line(self, pts, closed=False, width=2.0):
        pts = list(pts) + ([pts[0]] if closed else [])
        px = [self._p(p) for p in pts]
        w = max(1, round(width * self.k))
        self.d.line(px, fill=self.rgba, width=w, joint="curve")
        for p in pts:  # đầu tròn
            self.dot(p, width / 2)

    def circle(self, c, r, fill=False, width=2.0):
        x, y = self._p(c)
        rr = r * self.k
        if fill:
            self.d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=self.rgba)
        else:
            self.d.ellipse(
                (x - rr, y - rr, x + rr, y + rr),
                outline=self.rgba,
                width=max(1, round(width * self.k)),
            )

    def ellipse(self, box, width=2.0):
        x0, y0, x1, y1 = box
        self.d.ellipse(
            (x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k),
            outline=self.rgba,
            width=max(1, round(width * self.k)),
        )

    def rect(self, box, radius=2.0, width=2.0, fill=False):
        x0, y0, x1, y1 = box
        kw = dict(radius=radius * self.k)
        if fill:
            self.d.rounded_rectangle(
                (x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k), fill=self.rgba, **kw
            )
        else:
            self.d.rounded_rectangle(
                (x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k),
                outline=self.rgba,
                width=max(1, round(width * self.k)),
                **kw,
            )

    def arc(self, box, start, end, width=2.0):
        x0, y0, x1, y1 = box
        self.d.arc(
            (x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k),
            start,
            end,
            fill=self.rgba,
            width=max(1, round(width * self.k)),
        )


def _draw(name: str, pen: _Pen) -> None:
    if name == "file":
        pen.line([(6, 3), (14, 3), (19, 8), (19, 21), (6, 21)], closed=True)
        pen.line([(14, 3), (14, 8), (19, 8)])
    elif name == "folder":
        pen.line([(3, 6), (9, 6), (11, 9), (21, 9), (21, 19), (3, 19)], closed=True)
    elif name == "archive":
        pen.rect((4, 3, 20, 21), radius=3)
        pen.line([(12, 3), (12, 9)])
        pen.rect((9.5, 9, 14.5, 15), radius=1.5)
    elif name == "drop":
        pen.line([(4, 15), (4, 20), (20, 20), (20, 15)])
        pen.line([(12, 4), (12, 15)])
        pen.line([(7.5, 10.5), (12, 15), (16.5, 10.5)])
    elif name == "gear":
        pen.circle((12, 12), 3.2)
        pen.circle((12, 12), 7.2)
        for i in range(8):
            a = math.radians(i * 45)
            pen.line(
                [(12 + 7.2 * math.cos(a), 12 + 7.2 * math.sin(a)),
                 (12 + 10 * math.cos(a), 12 + 10 * math.sin(a))],
                width=2.6,
            )
    elif name == "clock":
        pen.circle((12, 12), 9)
        pen.line([(12, 7), (12, 12), (15.5, 14)])
    elif name == "close":
        pen.line([(6, 6), (18, 18)])
        pen.line([(18, 6), (6, 18)])
    elif name == "plus":
        pen.line([(12, 5), (12, 19)])
        pen.line([(5, 12), (19, 12)])
    elif name == "search":
        pen.circle((10.5, 10.5), 6.5)
        pen.line([(15.5, 15.5), (20, 20)])
    elif name == "check":
        pen.line([(5, 12.5), (10, 17.5), (19, 7)], width=2.4)
    elif name == "check_circle":
        pen.circle((12, 12), 9)
        pen.line([(7.5, 12.5), (10.8, 15.8), (16.5, 9)], width=2.2)
    elif name == "warn":
        pen.line([(12, 3.5), (21.5, 20), (2.5, 20)], closed=True)
        pen.line([(12, 10), (12, 14.5)])
        pen.dot((12, 17.3), 1.2)
    elif name == "error":
        pen.circle((12, 12), 9)
        pen.line([(8.5, 8.5), (15.5, 15.5)])
        pen.line([(15.5, 8.5), (8.5, 15.5)])
    elif name == "info":
        pen.circle((12, 12), 9)
        pen.dot((12, 7.8), 1.2)
        pen.line([(12, 11), (12, 16.5)])
    elif name == "more":
        for x in (5, 12, 19):
            pen.dot((x, 12), 1.9)
    elif name == "contrast":
        pen.circle((12, 12), 9)
        pen.d.pieslice(
            (3 * pen.k, 3 * pen.k, 21 * pen.k, 21 * pen.k), 90, 270, fill=pen.rgba
        )
    elif name == "chevron_down":
        pen.line([(6, 9), (12, 15), (18, 9)])
    elif name == "chevron_right":
        pen.line([(9, 6), (15, 12), (9, 18)])
    elif name == "trash":
        pen.line([(4, 7), (20, 7)])
        pen.line([(9, 7), (9, 4), (15, 4), (15, 7)])
        pen.line([(6, 7), (7, 20), (17, 20), (18, 7)])
    elif name == "eye":
        pen.ellipse((2, 6.5, 22, 17.5))
        pen.circle((12, 12), 2.6)
    elif name == "eye_off":
        pen.ellipse((2, 6.5, 22, 17.5))
        pen.circle((12, 12), 2.6)
        pen.line([(4, 20), (20, 4)])
    elif name == "lock":
        pen.rect((5, 11, 19, 21), radius=2.5)
        pen.line([(8, 11), (8, 8)])
        pen.line([(16, 11), (16, 8)])
        pen.arc((8, 3, 16, 13), 180, 360)
    elif name == "open":
        pen.rect((4, 6, 20, 20), radius=2.5)
        pen.line([(12, 3), (12, 13)])
        pen.line([(8, 7), (12, 3), (16, 7)])
    else:  # dự phòng: hình vuông rỗng
        pen.rect((5, 5, 19, 19), radius=2)


ICON_NAMES = (
    "file folder archive drop gear clock close plus search check check_circle warn error "
    "info more contrast chevron_down chevron_right trash eye eye_off lock open"
).split()


@lru_cache(maxsize=512)
def _render(name: str, size: int, color_hex: str) -> Image.Image:
    px = size * 2  # 2x để sắc nét trên màn hình DPI cao
    big = px * _SUPER // 2
    pen = _Pen(big, _hex_to_rgba(color_hex))
    _draw(name, pen)
    return pen.img.resize((px, px), Image.LANCZOS)


_ctk_cache: dict[tuple, ctk.CTkImage] = {}


def get_icon(
    name: str,
    size: int = 18,
    color: tuple[str, str] | str = COLOR_TEXT_SECONDARY,
) -> ctk.CTkImage:
    """Trả về CTkImage (tự đổi màu theo Light/Dark). Được cache theo (name, size, color)."""
    if isinstance(color, str):
        light = dark = color
    else:
        light, dark = color
    key = (name, size, light, dark)
    img = _ctk_cache.get(key)
    if img is None:
        img = ctk.CTkImage(
            light_image=_render(name, size, light),
            dark_image=_render(name, size, dark),
            size=(size, size),
        )
        _ctk_cache[key] = img
    return img
