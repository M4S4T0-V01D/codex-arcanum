"""Supersampled multi-layer pen.

Everything is drawn in *unit* coordinates: origin at canvas centre, y up,
1.0 = UNIT fraction of the canvas. Each layer is an 8-bit mask that the
compositor later tints (ink = metal, accent = second colour, fill = solid
backing that occludes the background, faint = low-contrast backdrop work).
"""
import math
from contextlib import contextmanager
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageFont

LAYERS = ("faint", "light", "fill", "flare", "ink", "accent")  # light = behind fills, flare = in front
UNIT = 0.29  # unit radius as a fraction of canvas width

FONT_DIR = "/usr/share/fonts/noto/"
FONTS = {
    "serif": "NotoSerifDisplay-Medium.ttf",
    "serif_text": "NotoSerif-Medium.ttf",
    "symbols": "NotoSansSymbols-Regular.ttf",
    "symbols2": "NotoSansSymbols2-Regular.ttf",
    "runic": "NotoSansRunic-Regular.ttf",
    "ogham": "NotoSansOgham-Regular.ttf",
    "hiero": "NotoSansEgyptianHieroglyphs-Regular.ttf",
    "hebrew": "NotoSansHebrew-Medium.ttf",
    "deva": "NotoSansDevanagari-Medium.ttf",
}


@lru_cache(maxsize=64)
def font(key, size):
    return ImageFont.truetype(FONT_DIR + FONTS[key], size)


FALLBACK = ("symbols", "symbols2", "math")
FONTS["math"] = "NotoSansMath-Regular.ttf"


@lru_cache(maxsize=None)
def _cmap(key):
    from fontTools.ttLib import TTFont
    return set(TTFont(FONT_DIR + FONTS[key], lazy=True).getBestCmap())


def resolve(text, key):
    """First font (requested key, then FALLBACK) that covers every char."""
    for k in (key,) + FALLBACK:
        cm = _cmap(k)
        if all(ord(c) in cm or c.isspace() or 0x300 <= ord(c) <= 0x36F or 0x900 <= ord(c) <= 0x97F for c in text):
            return k
    return key


@lru_cache(maxsize=4096)
def glyph_mask(text, key, size, angle):
    """Rendered, rotated text as an L image (cached: rings redraw every frame)."""
    f = font(resolve(text, key), size)
    l, t, r, b = f.getbbox(text)
    pad = 2
    im = Image.new("L", (r - l + pad * 2, b - t + pad * 2), 0)
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=255)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return im


def _mul(a, b):
    # 2x3 affine matrices (a, b, c, d, e, f): x' = a x + b y + c ; y' = d x + e y + f
    return (
        a[0] * b[0] + a[1] * b[3], a[0] * b[1] + a[1] * b[4], a[0] * b[2] + a[1] * b[5] + a[2],
        a[3] * b[0] + a[4] * b[3], a[3] * b[1] + a[4] * b[4], a[3] * b[2] + a[4] * b[5] + a[5],
    )


class Pen:
    def __init__(self, size, ss=2):
        self.size, self.ss = size, ss
        self.k = size / 512  # artwork is specified at 512px; everything scales with it
        self.N = N = size * ss
        self.layers = {k: Image.new("L", (N, N), 0) for k in LAYERS}
        self.draw = {k: ImageDraw.Draw(v) for k, v in self.layers.items()}
        u = N * UNIT
        # unit -> pixel: x_px = cx + x*u, y_px = cy - y*u
        self.m = (u, 0.0, N / 2, 0.0, -u, N / 2)
        self.wmul = 1.0
        self.rot_total = 0.0

    # ---- transforms ---------------------------------------------------
    @contextmanager
    def tf(self, dx=0.0, dy=0.0, rot=0.0, s=1.0, sx=None, sy=None, scale_width=False):
        """Push translate -> rotate(deg, CCW) -> scale."""
        saved = (self.m, self.wmul, self.rot_total)
        sx = s if sx is None else sx
        sy = s if sy is None else sy
        c, si = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        local = (c * sx, -si * sy, dx, si * sx, c * sy, dy)
        self.m = _mul(self.m, local)
        self.rot_total += rot
        if scale_width:
            self.wmul *= math.sqrt(abs(sx * sy))
        try:
            yield self
        finally:
            self.m, self.wmul, self.rot_total = saved

    @contextmanager
    def clip(self, pts):
        """Everything drawn inside the block is confined to polygon `pts`."""
        saved, saved_draw = self.layers, self.draw
        self.layers = {k: Image.new("L", (self.N, self.N), 0) for k in LAYERS}
        self.draw = {k: ImageDraw.Draw(v) for k, v in self.layers.items()}
        mask = Image.new("L", (self.N, self.N), 0)
        ImageDraw.Draw(mask).polygon([self.P(*q) for q in pts], fill=255)
        try:
            yield self
        finally:
            drawn = self.layers
            self.layers, self.draw = saved, saved_draw
            any_ink = Image.new("L", mask.size, 0)
            for k in LAYERS:
                any_ink = ImageChops.lighter(any_ink, drawn[k])
            m = ImageChops.multiply(mask, any_ink.point(lambda v: 255 if v else 0))
            for k in LAYERS:
                self.layers[k].paste(drawn[k], (0, 0), m)
            self.draw = {k: ImageDraw.Draw(v) for k, v in self.layers.items()}

    def P(self, x, y):
        m = self.m
        return (m[0] * x + m[1] * y + m[2], m[3] * x + m[4] * y + m[5])

    def scale_px(self):
        m = self.m
        return math.sqrt(abs(m[0] * m[4] - m[1] * m[3]))

    def W(self, w):
        return max(1, int(round(w * self.ss * self.wmul * self.k)))

    # ---- primitives ---------------------------------------------------
    def line(self, pts, w=2.0, layer="ink", v=255, closed=False):
        if len(pts) < 2 or v <= 0:
            return
        pp = [self.P(*p) for p in pts]
        if closed:
            pp.append(pp[0])
        wid = self.W(w)
        self.draw[layer].line(pp, fill=int(v), width=wid, joint="curve")
        if wid > 3 and not closed:  # round caps
            r = wid / 2
            for x, y in (pp[0], pp[-1]):
                self.draw[layer].ellipse((x - r, y - r, x + r, y + r), fill=int(v))

    def poly(self, pts, layer="fill", v=255, occlude=True):
        """Filled polygon. With occlude, erases whatever ink/accent lies below
        first, so later shapes properly cover earlier line-work."""
        pp = [self.P(*p) for p in pts]
        if len(pp) < 3:
            return
        if occlude:
            for k in ("ink", "accent"):
                if k != layer:
                    self.draw[k].polygon(pp, fill=0)
        self.draw[layer].polygon(pp, fill=int(v))

    def erase(self, pts, layers=("ink", "accent", "fill")):
        pp = [self.P(*p) for p in pts]
        for k in layers:
            self.draw[k].polygon(pp, fill=0)

    def circle_pts(self, x, y, r, a0=0.0, a1=360.0, n=None):
        if n is None:
            n = max(16, int(abs(a1 - a0) / 360 * r * self.scale_px() * 0.9))
            n = min(n, 720)
        return [(x + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 y + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

    def circle(self, x, y, r, w=2.0, layer="ink", v=255):
        self.line(self.circle_pts(x, y, r)[:-1], w, layer, v, closed=True)

    def arc(self, x, y, r, a0, a1, w=2.0, layer="ink", v=255):
        self.line(self.circle_pts(x, y, r, a0, a1), w, layer, v)

    def disc(self, x, y, r, layer="fill", v=255, occlude=True):
        self.poly(self.circle_pts(x, y, r)[:-1], layer, v, occlude)

    def ring(self, x, y, r, w=2.0, fill=True, layer="ink", v=255):
        """Outlined disc that hides what is behind it."""
        if fill:
            self.disc(x, y, r, "fill")
        self.circle(x, y, r, w, layer, v)

    def dot(self, x, y, rpx, layer="ink", v=255):
        X, Y = self.P(x, y)
        r = rpx * self.ss * self.k
        self.draw[layer].ellipse((X - r, Y - r, X + r, Y + r), fill=int(v))

    def text(self, s, x, y, size, key="serif", layer="ink", v=255, angle=None, upright=False):
        """Text centred on (x, y). size in output px; angle in degrees (CCW).
        By default text inherits the current rotation."""
        if v <= 0:
            return
        a = 0.0 if upright else self.rot_total
        if angle is not None:
            a += angle
        a = round(a * 2) / 2
        im = glyph_mask(s, key, int(round(size * self.ss * self.k)), a % 360)
        X, Y = self.P(x, y)
        box = (int(round(X - im.width / 2)), int(round(Y - im.height / 2)))
        self.layers[layer].paste(int(v), box, im)

    # ---- light ----------------------------------------------------------
    def ray(self, cx, cy, ang, r0, r1, w0, w1, v=255, layer="light", steps=16, core=True):
        """A beam of light from radius r0 to r1 along `ang` (deg), width w0 -> w1
        (unit coords). Built from nested wedges so it is brightest at its
        source and fades out along its length; the compositor softens it."""
        if v <= 0:
            return
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        x0, y0 = cx + ux * r0, cy + uy * r0
        for k in range(steps):  # longest + dimmest first, shorter + brighter on top
            f = 1 - k / steps
            L = r0 + (r1 - r0) * f
            w = w0 + (w1 - w0) * f
            x1, y1 = cx + ux * L, cy + uy * L
            pts = [(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w / 2, y1 + ny * w / 2),
                   (x1 - nx * w / 2, y1 - ny * w / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)]
            self.draw[layer].polygon([self.P(*q) for q in pts], fill=int(v * (k / steps) ** 1.15))
        if core and w1 > 0.02:  # a bright narrow shaft inside the soft body
            self.ray(cx, cy, ang, r0, r0 + (r1 - r0) * 0.9, w0 * 0.35, w1 * 0.22, v, layer, steps=10, core=False)

    def glow(self, x, y, r, v=255, layer="flare", steps=10):
        """Soft radial light: concentric discs, brightest at the centre."""
        if v <= 0:
            return
        for k in range(steps):
            rr = r * (1 - k / steps)
            self.draw[layer].polygon([self.P(*q) for q in self.circle_pts(x, y, rr, n=48)[:-1]],
                                     fill=int(v * ((k + 1) / steps) ** 1.8))

    def sparkle(self, x, y, size, v=255, rot=0.0, points=4, layer="flare"):
        """A star of light: long and short spikes plus a hot core."""
        for j in range(points * 2):
            L = size if j % 2 == 0 else size * 0.45
            self.ray(x, y, rot + 90 + j * 180 / points, 0, L, size * 0.16, 0.0, v, layer, steps=8)
        self.glow(x, y, size * 0.35, v, layer, steps=6)

    # ---- output -------------------------------------------------------
    def masks(self):
        """Downsample each layer (box filter = antialiasing)."""
        return {k: (im.reduce(self.ss) if self.ss > 1 else im) for k, im in self.layers.items()}


# ---- small geometry helpers ------------------------------------------
TAU = math.tau


def polar(r, deg, cx=0.0, cy=0.0):
    return (cx + r * math.cos(math.radians(deg)), cy + r * math.sin(math.radians(deg)))


def ngon(n, r, rot=90.0, cx=0.0, cy=0.0):
    return [polar(r, rot + 360.0 * i / n, cx, cy) for i in range(n)]


def lerp(a, b, k):
    return a + (b - a) * k


def smooth(e0, e1, x):
    k = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return k * k * (3 - 2 * k)


def wave(t, f=1, ph=0.0):
    """Seamless sine in [0, 1] with integer frequency f over the loop."""
    return 0.5 + 0.5 * math.sin(TAU * (f * t + ph))


def bezier(p0, p1, p2, n=24):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])
            for u in (i / n for i in range(n + 1))]


def bezier3(p0, p1, p2, p3, n=32):
    out = []
    for i in range(n + 1):
        u = i / n
        a, b, c, d = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u * u, u ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def thick(path, widths):
    """Polygon outline of a path with per-point width (for serpents, staves)."""
    n = len(path)
    if not hasattr(widths, "__len__"):
        widths = [widths] * n
    left, right = [], []
    for i in range(n):
        x0, y0 = path[max(0, i - 1)]
        x1, y1 = path[min(n - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        h = widths[i] / 2
        x, y = path[i]
        left.append((x + nx * h, y + ny * h))
        right.append((x - nx * h, y - ny * h))
    return left + right[::-1]


def path_point(path, u):
    """Point at fraction u (0..1) of a polyline's length."""
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]
    total = sum(seg)
    d = max(0.0, min(1.0, u)) * total
    for i, s in enumerate(seg):
        if d <= s or i == len(seg) - 1:
            k = d / s if s else 0
            return (lerp(path[i][0], path[i + 1][0], k), lerp(path[i][1], path[i + 1][1], k))
        d -= s
    return path[-1]


def sub_path(path, u0, u1, n=24):
    return [path_point(path, lerp(u0, u1, i / n)) for i in range(n + 1)]
