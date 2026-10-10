"""Compositing: background, line masks -> tinted RGB frames -> MP4 + GIF.

Quality notes
- Line-work is drawn supersampled (Pen.ss) and box-filtered down.
- Ink gets a bevel ("gold-leaf relief") from the gradient of its own
  blurred mask, and casts a soft drop shadow.
- Solid fills carry an engraved hatch, like the cut plates of old folios.
- Bloom is three blurs at different radii.
- Frames stream straight into one ffmpeg process: an H.264 master at full
  size plus a palette-optimised, ordered-dither GIF (ordered dither does not
  crawl between frames the way error diffusion does).
"""
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .palettes import PALETTES
from .pen import Pen


def _hsv(h, s, v):
    """Vectorised HSV -> RGB (all arrays / scalars in 0..1)."""
    h = np.mod(h, 1.0) * 6.0
    i = np.floor(h)
    f = h - i
    p, q, r = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    i = i.astype(int) % 6
    out = np.zeros(np.broadcast(h, s, v).shape + (3,), np.float32)
    for k, (a, b, c) in enumerate(((v, r, p), (q, v, p), (p, v, r), (p, q, v), (r, p, v), (v, p, q))):
        m = i == k
        for ch, src in enumerate((a, b, c)):
            out[..., ch] = np.where(m, src, out[..., ch])
    return out * 255


def _noise(rng, cells, S, blur):
    n = rng.random((cells, cells)).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(im, np.float32) / 255
    return (a - a.mean()) / (a.std() + 1e-6)


def _blur(arr_u8, r):
    return np.asarray(Image.fromarray(arr_u8).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


def _zoom_blur(arr_u8, scales=(1.025, 1.055, 1.09, 1.13, 1.18, 1.24)):
    """Radial streaks from the canvas centre: average of the mask scaled outward."""
    S = arr_u8.shape[0]
    im = Image.fromarray(arr_u8)
    acc = arr_u8.astype(np.float32)
    tot = 1.0
    for i, sc in enumerate(scales):
        n = int(S * sc)
        o = (n - S) // 2
        w = 0.85 ** (i + 1)
        acc += np.asarray(im.resize((n, n), Image.BILINEAR).crop((o, o, o + S, o + S)), np.float32) * w
        tot += w
    return np.clip(acc / tot, 0, 255).astype(np.uint8)


def _light(img, mask_u8, scene, t, front):
    """Add a light layer: soft core, haze and (behind the figures) radial streaks.
    On paper the light becomes a sepia (behind) or vermilion (front) wash."""
    if mask_u8.max() == 0:
        return img
    k = scene.k
    core = _blur(mask_u8, (1.6 if front else 2.6) * k)
    mid = _blur(mask_u8, 6 * k)
    haze = _blur(mask_u8, (10 if front else 18) * k)
    pal = scene.pal
    if scene.paper:
        col = np.array(pal["accent"] if front else pal["faint"], np.float32)
        a = np.clip((core * 0.45 + haze * 0.35) * (0.55 if front else 0.45), 0, 0.6)[..., None]
        return img * (1 - a) + col * a
    gc = scene.glow_color(t)
    lc = gc * 0.6 + 255 * 0.4
    if front:
        amt = core * 0.55 + mid * 0.3 + haze * 0.45
    else:
        amt = core * 0.5 + mid * 0.45 + haze * 0.55 + _blur(_zoom_blur(mask_u8), 3 * k) * 0.7
    img = img + lc * amt[..., None] * 0.95
    return img + 255 * (core ** 2.6)[..., None] * (0.4 if front else 0.22)


class Scene:
    """Per-token static state: background, star field, colour fields."""

    def __init__(self, size, palette_name, rng):
        self.size = S = size
        self.k = k = size / 512
        self.pal = pal = PALETTES[palette_name]
        self.paper = pal["kind"] == "paper"
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / (S - 1)
        self.xx, self.yy = xx, yy
        r = np.hypot(xx - 0.5, yy - 0.5) / 0.7071

        c0, c1 = (np.array(c, np.float32) for c in pal["bg"])
        g = np.clip(r * 1.15, 0, 1)[..., None] ** 1.3
        bg = c0 * (1 - g) + c1 * g

        neb = _noise(rng, 10, S, S / 22) * 0.65 + _noise(rng, 34, S, S / 70) * 0.35
        nc = np.array(pal["nebula"], np.float32)
        if self.paper:
            bg = bg * (1 - 0.045 * neb[..., None])
            fox = Image.new("L", (S, S), 0)
            d = ImageDraw.Draw(fox)
            for _ in range(rng.integers(12, 30)):
                x, y = rng.random(2) * S
                rr = (rng.random() * 6 + 0.5) * k
                d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=int(rng.integers(60, 170)))
            fox = _blur(np.asarray(fox), 2.2 * k)[..., None]
            bg = bg * (1 - fox * 0.35) + np.array((150, 96, 44), np.float32) * fox * 0.2
            # laid-paper chain lines + fibres
            laid = (0.5 + 0.5 * np.cos(2 * math.pi * yy * S / (3.2 * k)))[..., None]
            bg = bg * (1 - 0.018 * laid)
            fib = rng.normal(0, 1, (S, S)).astype(np.float32)
            fib = np.asarray(Image.fromarray(np.clip(fib * 40 + 128, 0, 255).astype(np.uint8))
                             .filter(ImageFilter.BoxBlur(max(1, int(k)))), np.float32) / 255 - 0.5
            bg = bg * (1 + fib[..., None] * 0.07)
        else:
            glow = np.clip(neb, 0, None)[..., None]
            bg = bg + nc * glow * 0.11 * (1 - r[..., None] * 0.5)
            # a faint second colour in the nebula troughs
            bg = bg + np.array(pal["accent"], np.float32) * np.clip(-neb, 0, None)[..., None] * 0.012

        grain = rng.normal(0, 1, (S, S, 1)).astype(np.float32)
        bg = bg + grain * (4.5 if self.paper else 2.6)
        self.bg = bg
        self.vignette = (1 - 0.42 * np.clip(r, 0, 1.2) ** 2.2)[..., None]

        # engraved hatching for solid fills (45°, cross-hatched on paper)
        X, Y = xx * S, yy * S
        period = 4.6 * k
        h1 = np.clip((np.cos(2 * math.pi * (X + Y) / period) - 0.5) / 0.5, 0, 1)
        if self.paper:
            h2 = np.clip((np.cos(2 * math.pi * (X - Y) / (period * 1.6)) - 0.7) / 0.3, 0, 1)
            h1 = np.maximum(h1, h2 * 0.6)
        self.hatch = h1[..., None].astype(np.float32)

        # stars: brightness + twinkle, splatted with a soft kernel scaled to resolution
        self.stars = None
        if pal["stars"]:
            n = int(rng.integers(110, 200) * (0.6 + 0.4 * k))
            self.stars = dict(
                x=rng.integers(3, S - 3, n), y=rng.integers(3, S - 3, n),
                b=rng.random(n) ** 2.4 * 0.95 + 0.05, f=rng.integers(1, 4, n), ph=rng.random(n),
                big=rng.random(n) < 0.07)
            rad = max(1, int(round(k * 0.9)))
            ker = [(dx, dy, math.exp(-(dx * dx + dy * dy) / (0.6 * k * k + 0.3)))
                   for dx in range(-rad, rad + 1) for dy in range(-rad, rad + 1)]
            self.ker = [q for q in ker if q[2] > 0.05]
            L = int(round(3 * k)) + 1
            self.flare = [(d, 0, 0.5 * (1 - abs(d) / (L + 1))) for d in range(-L, L + 1) if d] + \
                         [(0, d, 0.5 * (1 - abs(d) / (L + 1))) for d in range(-L, L + 1) if d]
        self.shade = np.clip(1.05 - yy * 0.75 + (0.5 - np.abs(xx - 0.5)) * 0.25, 0, 1)[..., None]
        self.diag = (xx - yy)

    def star_field(self, t):
        S = self.size
        out = np.zeros((S, S), np.float32)
        st = self.stars
        if st is None:
            return out
        v = st["b"] * (0.55 + 0.45 * np.sin(2 * math.pi * (st["f"] * t + st["ph"])))
        for dx, dy, w in self.ker:
            np.maximum.at(out, (st["y"] + dy, st["x"] + dx), v * w)
        big = st["big"]
        for dx, dy, w in self.flare:
            ys = np.clip(st["y"][big] + dy, 0, S - 1)
            xs = np.clip(st["x"][big] + dx, 0, S - 1)
            np.maximum.at(out, (ys, xs), v[big] * w)
        return out

    def ink_color(self, t):
        pal = self.pal
        if pal["ink"] == "iridescent":
            col = _hsv(self.diag * 0.45 + self.yy * 0.2 + t, 0.55, 1.0) * (0.55 + 0.45 * self.shade)
        else:
            light, dark = (np.array(c, np.float32) for c in pal["ink"])
            col = dark + (light - dark) * self.shade
        if self.paper:
            return col
        c = -1.5 + 3.0 * t  # glint: a diagonal sheen sweeping across once per loop
        g = np.exp(-((self.diag - c) / 0.07) ** 2)[..., None]
        return col + (255 - col) * g * 0.8

    def glow_color(self, t):
        g = self.pal["glow"]
        if g == "iridescent":
            return _hsv(np.float32(t + 0.5), 0.6, 1.0).reshape(3)
        return np.array(g, np.float32)


def composite(scene, masks, t, breath=1.0):
    pal, S, k = scene.pal, scene.size, scene.k
    raw = {n: np.asarray(m) for n, m in masks.items()}
    f = {n: a.astype(np.float32)[..., None] / 255 for n, a in raw.items()}
    img = scene.bg.copy()
    if scene.stars is not None:
        img += np.array(pal["stars"], np.float32) * scene.star_field(t)[..., None]
    faint = np.array(pal["faint"], np.float32)
    if scene.paper:
        img = img * (1 - f["faint"] * 0.45) + faint * f["faint"] * 0.45
    else:
        img = img + faint * f["faint"] * 0.30

    img = _light(img, raw["light"], scene, t, front=False)

    # solid fills, engraved
    img = img * (1 - f["fill"]) + np.array(pal["fill"], np.float32) * f["fill"]
    hk = f["fill"] * scene.hatch * (0.2 if scene.paper else 0.09)
    img = img * (1 - hk) + faint * hk

    lines = np.maximum(raw["ink"], raw["accent"])
    # drop shadow, offset down-right
    sh = _blur(lines, 2.4 * k)
    o = max(1, int(round(2 * k)))
    sh = np.pad(sh, ((o, 0), (o, 0)))[:S, :S][..., None]
    img = img * (1 - (0.5 if scene.paper else 0.55) * sh * (1 - f["ink"]))

    # bloom
    b1 = _blur(lines, S / 110)
    b2 = _blur(lines, S / 30)
    b3 = _blur(lines, S / 9)
    glow = np.clip((b1 * 0.85 + b2 * 1.05 + b3 * 0.7) * pal["glow_k"] * breath, 0, 1)[..., None]
    img = img * (1 - glow) + scene.glow_color(t) * glow

    img = _light(img, raw["flare"], scene, t, front=True)

    # gold-leaf relief: light from the upper left across the blurred ink height-field
    hgt = _blur(raw["ink"], 1.3 * k)
    gy, gx = np.gradient(hgt)
    relief = np.clip(1.0 + (gx + gy) * (2.2 * k) * (0.45 if scene.paper else 1.0), 0.55, 1.55)[..., None]
    ink = np.clip(scene.ink_color(t) * relief, 0, 255)
    img = img * (1 - f["ink"]) + ink * f["ink"]
    img = img * (1 - f["accent"]) + np.array(pal["accent"], np.float32) * f["accent"]
    img = img * scene.vignette
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def iter_frames(token, size, frames, ss=2, draw_fn=None):
    rng = np.random.default_rng(token["seed"])
    scene = Scene(size, token["traits"]["Opus"], rng)
    for i in range(frames):
        t = i / frames
        pen = Pen(size, ss)
        draw_fn(pen, t, token)
        breath = 0.85 + 0.3 * (0.5 + 0.5 * math.sin(2 * math.pi * t))
        yield composite(scene, pen.masks(), t, breath)


def render_frames(token, size, frames, ss=2, draw_fn=None):
    return list(iter_frames(token, size, frames, ss, draw_fn))


class Encoder:
    """One ffmpeg process -> <base>.mp4 (full size) and <base>.gif (gif_size)."""

    def __init__(self, base, size, fps, gif_size=None, crf=16):
        self.size = size
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{size}x{size}", "-r", str(fps), "-i", "-"]
        if gif_size:
            cmd += ["-filter_complex",
                    f"[0:v]split=2[a][b];[b]scale={gif_size}:{gif_size}:flags=lanczos,split[c][d];"
                    "[c]palettegen=max_colors=255:stats_mode=full[p];"
                    "[d][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle[g]",
                    "-map", "[a]"]
        cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-tune", "film", "-movflags", "+faststart", base + ".mp4"]
        if gif_size:
            cmd += ["-map", "[g]", "-loop", "0", base + ".gif"]
        self.gif = base + ".gif" if gif_size else None
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def add(self, im):
        self.p.stdin.write(im.tobytes())

    def close(self, lossy=40):
        self.p.stdin.close()
        if self.p.wait() != 0:
            raise RuntimeError("ffmpeg failed")
        if self.gif and lossy:
            subprocess.run(["gifsicle", "-b", "-O3", f"--lossy={lossy}", self.gif],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
