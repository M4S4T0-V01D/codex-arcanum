"""Compositing: background, line masks -> tinted RGB frames -> GIF."""
import math
import subprocess

import numpy as np
from PIL import Image, ImageFilter

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


class Scene:
    """Per-token static state: background, star field, colour fields."""

    def __init__(self, size, palette_name, rng):
        self.size = S = size
        self.pal = pal = PALETTES[palette_name]
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / (S - 1)
        self.xx, self.yy = xx, yy
        r = np.hypot(xx - 0.5, yy - 0.5) / 0.7071
        self.r = r

        c0, c1 = (np.array(c, np.float32) for c in pal["bg"])
        k = np.clip(r * 1.15, 0, 1)[..., None] ** 1.3
        bg = c0 * (1 - k) + c1 * k

        # low-frequency "nebula" / staining
        neb = rng.random((12, 12)).astype(np.float32)
        neb = np.array(Image.fromarray((neb * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC)
                       .filter(ImageFilter.GaussianBlur(S / 24)), np.float32) / 255
        neb = (neb - neb.mean()) * 2.2
        nc = np.array(pal["nebula"], np.float32)
        if pal["kind"] == "paper":
            bg = bg * (1 - 0.10 * neb[..., None])
            # foxing: small rusty stains
            fox = Image.new("L", (S, S), 0)
            from PIL import ImageDraw
            d = ImageDraw.Draw(fox)
            for _ in range(rng.integers(10, 26)):
                x, y = rng.random(2) * S
                rr = rng.random() * S * 0.012 + 1
                d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=int(rng.integers(60, 160)))
            fox = np.array(fox.filter(ImageFilter.GaussianBlur(2.2)), np.float32)[..., None] / 255
            bg = bg * (1 - fox * 0.35) + np.array((150, 96, 44), np.float32) * fox * 0.2
            # paper fibres
            fib = rng.normal(0, 1, (S, S)).astype(np.float32)
            fib = np.array(Image.fromarray(np.clip(fib * 40 + 128, 0, 255).astype(np.uint8))
                           .filter(ImageFilter.BoxBlur(1)), np.float32) / 255 - 0.5
            bg = bg * (1 + fib[..., None] * 0.08)
        else:
            bg = bg + nc * np.clip(neb, 0, None)[..., None] * 0.10 * (1 - r[..., None] * 0.5)

        grain = rng.normal(0, 1, (S, S, 1)).astype(np.float32)
        bg = bg + grain * (5.0 if pal["kind"] == "paper" else 3.0)
        self.bg = bg
        self.vignette = (1 - 0.42 * np.clip(r, 0, 1.2) ** 2.2)[..., None]

        # stars
        self.stars = None
        if pal["stars"]:
            n = int(rng.integers(90, 170))
            self.stars = dict(
                x=rng.integers(1, S - 1, n), y=rng.integers(1, S - 1, n),
                b=rng.random(n) ** 2.2 * 0.95 + 0.05, f=rng.integers(1, 4, n), ph=rng.random(n),
                big=rng.random(n) < 0.08)
        # metal gradient
        self.shade = np.clip(1.05 - yy * 0.75 + (0.5 - np.abs(xx - 0.5)) * 0.25, 0, 1)[..., None]
        self.diag = (xx - yy)  # -1..1, for the travelling glint

    def star_field(self, t):
        S = self.size
        out = np.zeros((S, S), np.float32)
        st = self.stars
        if st is None:
            return out
        v = st["b"] * (0.55 + 0.45 * np.sin(2 * math.pi * (st["f"] * t + st["ph"])))
        out[st["y"], st["x"]] = v
        big = st["big"]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            np.maximum.at(out, (st["y"][big] + dy, st["x"][big] + dx), v[big] * 0.45)
        return out

    def ink_color(self, t):
        pal = self.pal
        if pal["ink"] == "iridescent":
            h = self.diag * 0.45 + self.yy * 0.2 + t
            col = _hsv(h, 0.55, 1.0)
            col = col * (0.55 + 0.45 * self.shade)
        else:
            light, dark = (np.array(c, np.float32) for c in pal["ink"])
            col = dark + (light - dark) * self.shade
        # glint: a diagonal sheen sweeping across once per loop
        c = -1.5 + 3.0 * t
        g = np.exp(-((self.diag - c) / 0.07) ** 2)[..., None]
        if pal["kind"] == "paper":
            return col
        return col + (255 - col) * g * 0.8

    def glow_color(self, t):
        g = self.pal["glow"]
        if g == "iridescent":
            return _hsv(np.float32(t + 0.5), 0.6, 1.0).reshape(3)
        return np.array(g, np.float32)


def composite(scene, masks, t, breath=1.0):
    pal = scene.pal
    f = {k: np.asarray(m, np.float32)[..., None] / 255 for k, m in masks.items()}
    img = scene.bg.copy()
    if scene.stars is not None:
        img += np.array(pal["stars"], np.float32) * scene.star_field(t)[..., None]
    if pal["kind"] == "paper":
        img = img * (1 - f["faint"] * 0.45) + np.array(pal["faint"], np.float32) * f["faint"] * 0.45
    else:
        img = img + np.array(pal["faint"], np.float32) * f["faint"] * 0.30
    img = img * (1 - f["fill"]) + np.array(pal["fill"], np.float32) * f["fill"]

    # bloom from ink + accent
    src = np.maximum(np.asarray(masks["ink"]), np.asarray(masks["accent"]))
    srci = Image.fromarray(src)
    b1 = np.asarray(srci.filter(ImageFilter.GaussianBlur(scene.size / 110)), np.float32) / 255
    b2 = np.asarray(srci.filter(ImageFilter.GaussianBlur(scene.size / 30)), np.float32) / 255
    glow = np.clip((b1 * 0.9 + b2 * 1.1) * pal["glow_k"] * breath, 0, 1)[..., None]
    img = img * (1 - glow) + scene.glow_color(t) * glow

    ink = scene.ink_color(t)
    img = img * (1 - f["ink"]) + ink * f["ink"]
    img = img * (1 - f["accent"]) + np.array(pal["accent"], np.float32) * f["accent"]
    img = img * scene.vignette
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def render_frames(token, size, frames, ss=2, draw_fn=None):
    rng = np.random.default_rng(token["seed"])
    scene = Scene(size, token["traits"]["Opus"], rng)
    out = []
    for i in range(frames):
        t = i / frames
        pen = Pen(size, ss)
        draw_fn(pen, t, token)
        breath = 0.85 + 0.3 * (0.5 + 0.5 * math.sin(2 * math.pi * t))
        out.append(composite(scene, pen.masks(), t, breath))
    return out


def save_gif(frames, path, delay_ms, lossy=30):
    # one global palette for every frame keeps static areas byte-identical,
    # which lets gifsicle's frame-diffing do most of the compression work
    sample = frames[:: max(1, len(frames) // 8)]
    strip = Image.new("RGB", (frames[0].width, frames[0].height * len(sample)))
    for i, fr in enumerate(sample):
        strip.paste(fr, (0, i * fr.height))
    pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT, kmeans=2)
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=delay_ms, loop=0,
              optimize=False, disposal=1)
    subprocess.run(["gifsicle", "-b", "-O3", f"--lossy={lossy}", path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
