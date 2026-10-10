"""The Seven Hierophants: hand-composed one-of-one plates.

Each fills the whole plate (no rolled halo, ring, frame or motto), uses its
own palette, and sits inside the ornate Hierophant frame. They are
registered as sigils with weight 0, so they are never rolled; traits.py
places them at fixed token ids.
"""
import math
import random

from .layers import _units
from .pen import TAU, bezier, bezier3, lerp, polar, thick, wave
from .sigils import SIGILS, _normals, crescent, eye, lotus_petal, serpent_run, sigil, snake_head_top

# token id -> sigil key
ONE_OF_ONE = {7: "ra", 42: "tablet", 108: "aum", 144: "ophanim", 333: "yggdrasil", 432: "phoenix", 777: "sunstone"}

HIERO = "𓀀𓀁𓀭𓁐𓁟𓂀𓂋𓂝𓃀𓃭𓃹𓄿𓅃𓅓𓅱𓆄𓆑𓆓𓆣𓇋𓇌𓇯𓇳𓈖𓉐𓊃𓊖𓊪𓊹𓊽𓋴𓋹𓌀𓍑𓎛𓏏𓏤𓐍𓂻𓆎𓅂𓁹𓇼𓋞"
FUTHARK = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"


def one(key, name, tradition, palette, lore):
    reg = sigil(key, name, tradition, 0, lore, rings=())

    def wrap(fn):
        reg(fn)
        SIGILS[key].update(one=True, palette=palette)
        return fn
    return wrap


# ---- shared craft ---------------------------------------------------------------
def fine_rays(p, c, n, r0, r1, v, t, w=0.022, wobble=0.1, layer="light", short=0.7):
    """A crisp glory of many thin rays (long and short alternating)."""
    for i in range(n):
        a = 90 + 360 * i / n
        long = i % 2 == 0
        L = r1 * (1 if long else short) + wobble * wave(t, 2, i * 0.37)
        p.ray(*c, a, r0, L, 0.006, w * (1.0 if long else 0.6), int(v * (0.5 + 0.5 * wave(t, 1, -i / n))), layer, steps=10, core=False)


def cell(p, pts, tint=0, lw=1.2, v=255):
    """A cloisonné cell: dark ground, optional coloured inlay, gold wire."""
    p.poly(pts, "fill")
    if tint:
        p.poly(pts, "accent", tint, occlude=False)
    p.line(pts, lw, "accent", 0, closed=True)  # keep the inlay off the wire
    p.line(pts, lw, "ink", v, closed=True)


def gild(p, pts, v=70, lw=1.4):
    """A solid gold shape with a bright outline."""
    p.poly(pts, "fill")
    p.poly(pts, "ink", v, occlude=False)
    p.line(pts, lw, closed=True)


def ellipse(cx, cy, rx, ry, rot=0.0, n=40):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + rx * math.cos(a) * c - ry * math.sin(a) * s, cy + rx * math.cos(a) * s + ry * math.sin(a) * c)
            for a in (TAU * k / n for k in range(n))]


def hierophant_frame(p, t, title):
    e1, e2, e3 = _units(p, 0.474), _units(p, 0.456), _units(p, 0.44)
    sq = lambda e: [(-e, -e), (e, -e), (e, e), (-e, e)]  # noqa: E731
    p.line(sq(e1), 1.4, "ink", 230, closed=True)
    p.line(sq(e2), 3.0, "ink", 255, closed=True)
    p.line(sq(e3), 0.8, "ink", 170, closed=True)
    m = (e1 + e2) / 2
    for i in range(60):
        f = i / 60
        for (x0, y0), (x1, y1) in zip(sq(m), sq(m)[1:] + sq(m)[:1]):
            p.dot(lerp(x0, x1, f), lerp(y0, y1, f), 0.9, "ink", 190)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        c = (sx * e2, sy * e2)
        p.disc(*c, 0.11, "fill")
        p.circle(*c, 0.11, 2.0)
        p.circle(*c, 0.085, 0.8, "ink", 180)
        for j in range(12):
            p.line([polar(0.03, 30 * j, *c), polar(0.075 if j % 2 else 0.06, 30 * j, *c)], 0.8, "ink", 220)
        p.sparkle(*c, 0.09, int(150 + 105 * wave(t, 1, k / 4)), rot=45)
    for sx in (1, -1):
        dia = [(sx * e2, 0.09), (sx * e2 + 0.05, 0), (sx * e2, -0.09), (sx * e2 - 0.05, 0)]
        p.poly(dia, "fill")
        p.line(dia, 1.4, closed=True)
    w, y = 0.66, e2
    cart = [(-w, y - 0.06), (w, y - 0.06), (w + 0.05, y), (w, y + 0.06), (-w, y + 0.06), (-w - 0.05, y)]
    p.poly(cart, "fill")
    p.line(cart, 1.4, closed=True)
    p.text(title, 0, y, 12, "serif", "ink", 255, upright=True)
    cart2 = [(x, -yy) for x, yy in cart]
    p.poly(cart2, "fill")
    p.line(cart2, 1.4, closed=True)
    p.text("HIEROPHANT · ONE OF ONE", 0, -y, 10, "serif", "accent", 255, upright=True)


def feather(p, root, a, L, wmax, barbs=True, flame=0.0, t=0.0, bend=-5, tint=0):
    path = bezier(root, polar(L * 0.55, a + bend, *root), polar(L, a, *root), 22)
    ws = [wmax * math.sin(math.pi * min(1.0, 0.1 + 0.9 * (i / 22) ** 0.85)) ** 0.5 * (1 - 0.2 * i / 22) + 0.002 for i in range(23)]
    f = thick(path, ws)
    p.poly(f, "fill")
    p.poly(f, "ink", 46, occlude=False)
    if tint:
        p.poly(thick(path[6:], [w * 0.5 for w in ws[6:]]), "accent", tint, occlude=False)
    p.line(f, 1.0, closed=True)
    p.line(path[2:-3], 0.7, "ink", 200)
    if barbs:
        for j in range(4, 20, 2):
            (x0, y0), (x1, y1) = path[j], path[j + 1]
            dl = math.hypot(x1 - x0, y1 - y0) or 1
            tx, ty = (x1 - x0) / dl, (y1 - y0) / dl
            for sg in (1, -1):
                w = ws[j] * 0.46
                p.line([(x0, y0), (x0 - ty * sg * w + tx * w * 1.1, y0 + tx * sg * w + ty * w * 1.1)], 0.45, "ink", 130)
    if flame:
        tip = path[-1]
        h = flame * (0.65 + 0.35 * math.sin(TAU * (t * 3 + L * 7)))
        p.ray(*tip, a + bend * 0.5, 0.0, h, wmax * 1.1, 0.0, 240, "flare", steps=8, core=False)
    return path


def bird_wing(p, raise_deg, span, t, flap=0.0, flame=0.0, tint=0):
    """A bird's wing drawn to the right of the origin (the shoulder), its arm
    raised `raise_deg` above horizontal. Mirror with p.tf(sx=-1)."""
    a = raise_deg + flap
    E = polar(span * 0.3, a)
    W = polar(span * 0.26, a + 22, *E)
    arm = bezier((0, 0), E, W, 24)
    hand = a + 22
    for j in range(10):  # primaries, fanned from the wrist, outermost longest
        root = polar(0.012 * j, hand - 180, *W)
        feather(p, root, hand + 8 - j * 8.5, span * (0.6 - 0.022 * j), span * 0.07, flame=flame, t=t + j * 0.07, bend=-6, tint=tint)
    for k in range(11):  # secondaries hang from the forearm, tertials near the body
        u = 0.98 - k * 0.075
        feather(p, arm[int(u * 24)], a - 100 + 18 * u, span * (0.36 - 0.08 * (1 - u)), span * 0.075,
                flame=flame * 0.6, t=t + k * 0.11, bend=6, tint=tint)
    for row, (n, L, w) in enumerate(((13, 0.2, 0.06), (15, 0.12, 0.05))):  # coverts
        for k in range(n):
            u = 1.0 - (k + 0.5 * row) / n
            feather(p, arm[min(24, int(u * 24))], a - 95 + 25 * u + (8 if row else 0), span * L, span * w, barbs=False, bend=8)
    band = thick(arm, [span * lerp(0.08, 0.035, i / 24) for i in range(25)])
    gild(p, band, 60, 1.2)
    nm = _normals(arm)
    for i in range(2, 23, 2):
        (x, y), n_ = arm[i], nm[i]
        d = math.degrees(math.atan2(n_[3], n_[2]))
        p.arc(x, y, span * 0.016, d - 80, d + 80, 0.5, "ink", 160)
    return W


# ===================================================================================
#  I · THE EYE OF RA
# ===================================================================================
def egypt_wing(p, L, t, tints=(170, 0, 95)):
    """One wing of the winged sun disc, root at the origin, extending to +x:
    rows of coverts, secondaries and long primaries in cloisonné."""
    top = lambda x: 0.12 - 0.06 * (x / L) ** 1.8  # noqa: E731
    b1 = lambda x: top(x) - 0.07 * (1 - 0.35 * x / L)  # noqa: E731
    b2 = lambda x: b1(x) - 0.085 * (1 - 0.35 * x / L)  # noqa: E731
    bot = lambda x: -0.37 + 0.27 * (x / L) ** 0.85  # noqa: E731
    n = 16
    for i in range(n):  # primaries
        x0, x1 = L * i / n, L * (i + 1) / n
        sl = 0.03 + 0.07 * i / n
        xm = (x0 + x1) / 2
        yb = bot(xm)
        pts = [(x0, b2(x0)), (x1, b2(x1)), (x1 + sl, yb + 0.03)] + \
            [(xm + sl + (x1 - x0) / 2 * math.cos(q), yb + 0.03 - (x1 - x0) * 0.55 * math.sin(q)) for q in (math.pi * k / 8 for k in range(1, 8))] + \
            [(x0 + sl, yb + 0.03)]
        cell(p, pts, tints[i % 3], 1.0)
        p.line([(xm, b2(xm) - 0.02), (xm + sl, yb + 0.01)], 0.5, "ink", 150)
    m = 22
    for i in range(m):  # secondaries
        x0, x1 = L * i / m, L * (i + 1) / m
        xm = (x0 + x1) / 2
        pts = [(x0, b1(x0)), (x1, b1(x1)), (x1, b2(x1) - 0.01)] + \
            [(xm + (x1 - x0) / 2 * math.cos(q), b2(xm) - 0.01 - (x1 - x0) * 0.45 * math.sin(q)) for q in (math.pi * k / 6 for k in range(1, 6))] + \
            [(x0, b2(x0) - 0.01)]
        cell(p, pts, tints[(i + 1) % 3], 0.9)
    k = 30
    for i in range(k):  # coverts: rows of scales
        x0, x1 = L * i / k, L * (i + 1) / k
        xm = (x0 + x1) / 2
        pts = [(x0, top(x0)), (x1, top(x1))] + [(xm + (x1 - x0) / 2 * math.cos(q), b1(xm) + 0.005 - (x1 - x0) * 0.5 * math.sin(q))
                                                 for q in (math.pi * j / 6 for j in range(0, 7))]
        cell(p, pts, tints[(i + 2) % 3], 0.8)
    p.line([(x, top(x)) for x in (L * j / 30 for j in range(31))], 2.0)


def uraeus(p, t, glow=True):
    """A rearing cobra in profile facing +x, its coil at the origin."""
    coil = bezier3((-0.16, -0.3), (0.02, -0.44), (0.18, -0.3), (0.1, -0.1), 30) + bezier((0.1, -0.1), (0.06, -0.02), (0.08, 0.06), 10)[1:]
    serpent_run(p, coil, [lerp(0.025, 0.07, (i / len(coil)) ** 0.7) for i in range(len(coil))], flow=-2 * t)
    hood = bezier3((0.11, -0.04), (-0.03, 0.02), (-0.04, 0.17), (0.06, 0.24), 14) + bezier3((0.06, 0.24), (0.14, 0.27), (0.17, 0.16), (0.12, -0.04), 14)[1:]
    cell(p, hood, 90, 1.3)
    for k in range(6):  # ventral bands down the front of the hood
        y = 0.18 - k * 0.035
        p.line([(0.1, y), (0.155 - 0.004 * k, y - 0.01)], 0.8, "ink", 210)
    head = [(0.07, 0.21), (0.12, 0.255), (0.2, 0.255), (0.25, 0.232), (0.24, 0.212), (0.18, 0.2), (0.11, 0.19)]
    cell(p, head, 0, 1.2)
    p.dot(0.185, 0.233, 1.5, "accent", 255)
    p.disc(0.12, 0.34, 0.06, "ink")
    p.circle(0.12, 0.34, 0.06, 1.2, "flare", 200)
    if glow:
        p.glow(0.12, 0.34, 0.16, int(170 + 70 * wave(t, 2)))


def uraeus_front(p, x, y, s, t, k):
    """A frontal cobra, hood spread, crowned with a sun disc, for the frieze."""
    tail = bezier3((x, y), (x + s * 0.25, y - s * 0.12), (x - s * 0.25, y - s * 0.28), (x + s * 0.05, y - s * 0.36), 12)
    p.poly(thick(tail, [lerp(s * 0.16, s * 0.03, i / 12) for i in range(13)]), "ink", 160, occlude=False)
    hood = bezier3((x - s * 0.08, y), (x - s * 0.3, y + s * 0.3), (x - s * 0.32, y + s * 0.85), (x, y + s * 1.0), 12) + \
        bezier3((x, y + s * 1.0), (x + s * 0.32, y + s * 0.85), (x + s * 0.3, y + s * 0.3), (x + s * 0.08, y), 12)[1:]
    cell(p, hood, 120 if k % 2 else 70, 1.0)
    for j in range(5):
        yy = y + s * (0.18 + 0.13 * j)
        p.line([(x - s * 0.07, yy), (x + s * 0.07, yy)], 0.6, "ink", 200)
    head = ellipse(x, y + s * 1.03, s * 0.09, s * 0.07)
    cell(p, head, 0, 0.9)
    p.dot(x - s * 0.035, y + s * 1.04, 0.9, "accent")
    p.dot(x + s * 0.035, y + s * 1.04, 0.9, "accent")
    p.disc(x, y + s * 1.3, s * 0.17, "ink")
    p.glow(x, y + s * 1.3, s * 0.5, int(90 + 90 * wave(t, 1, k / 13)))


def aten_hand(p, end, ang, s, holding):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    p.disc(*end, s * 0.5, "ink", 230, occlude=False)
    for k in range(4):
        off = (k - 1.5) * s * 0.28
        b = (end[0] + nx * off, end[1] + ny * off)
        p.line([b, (b[0] + ux * s * 1.1, b[1] + uy * s * 1.1)], 0.8, "ink", 220)
    if holding:
        p.text("𓋹", end[0] + ux * s * 2.4, end[1] + uy * s * 2.4, 15, "hiero", "ink", 245, upright=True)


@one("ra", "The Eye of Ra", "Egyptian Mysteries", "Solar Lapis",
     "The burning Eye of Ra: the sun-disc winged by Horus of Behdet and girded by twin uraei, its rays falling as hands that offer life, above a wall of the sacred writing")
def ra(p, t, v):
    scan = 1.85 - 3.7 * t  # the temple wall, read by a passing light
    for ci, x in enumerate([-1.52 + 0.16 * i for i in range(20)]):
        p.line([(x - 0.08, 1.45), (x - 0.08, -1.0)], 0.5, "ink", 40)
        for ri, y in enumerate([1.36 - 0.155 * j for j in range(16)]):
            ch = HIERO[(ci * 7 + ri * 13 + ci * ri) % len(HIERO)]
            p.text(ch, x, y, 12, "hiero", "ink", 52, upright=True)
            lit = math.exp(-((y - scan) / 0.22) ** 2)
            if lit > 0.06:
                p.text(ch, x, y, 12, "hiero", "accent", int(130 * lit), upright=True)
    sun = (0, 0.36)
    fine_rays(p, sun, 72, 0.4, 2.2, 150, t)
    p.glow(*sun, 1.0, 140, "light")
    for i in range(11):  # the Aten's rays, ending in hands
        a = 228 + i * 8.4
        end = polar(1.5 - 0.12 * abs(i - 5) / 5, a, *sun)
        p.ray(*sun, a, 0.4, math.dist(sun, end), 0.012, 0.03, 160, "light", steps=8, core=False)
        p.line([polar(0.4, a, *sun), end], 0.7, "ink", 170)
        aten_hand(p, end, a, 0.035, i % 2 == 0)
    flap = 0.03 * math.sin(TAU * t)
    for side in (1, -1):
        with p.tf(dx=side * 0.34, dy=sun[1] + 0.06, sx=side, sy=1 + flap):
            egypt_wing(p, 1.12, t)
    for side in (1, -1):
        with p.tf(dx=side * 0.42, dy=sun[1] - 0.12, sx=side):
            uraeus(p, t)
    p.glow(*sun, 0.6, 120, "light")  # the disc of beaten gold, the right eye inlaid in it
    disc = p.circle_pts(*sun, 0.36)[:-1]
    p.poly(disc, "fill")
    p.poly(disc, "ink", 105, occlude=False)
    for r, w_, vv in ((0.36, 3.0, 255), (0.335, 0.8, 200), (0.29, 1.6, 230)):
        p.circle(*sun, r, w_, "ink", vv)
    p.poly(p.circle_pts(*sun, 0.285)[:-1], "fill", 200, occlude=False)
    for i in range(48):
        a = 7.5 * i + 7.5 * t
        p.line([polar(0.295, a, *sun), polar(0.33, a, *sun)], 0.8, "ink", 210)
    with p.tf(dx=sun[0] - 0.01, dy=sun[1] - 0.03, sx=-0.3, sy=0.3):
        cell(p, thick(bezier3((-0.8, 0.42), (-0.3, 0.66), (0.35, 0.66), (0.84, 0.44), 40), [lerp(0.13, 0.07, i / 40) for i in range(41)]), 0, 2.6)
        up = bezier3((-0.6, 0.05), (-0.3, 0.38), (0.25, 0.35), (0.58, 0.03), 40)
        lo = bezier3((-0.6, 0.05), (-0.25, -0.2), (0.25, -0.18), (0.58, 0.03), 40)
        p.poly(up + lo[::-1], "fill")
        p.poly(up + lo[::-1], "accent", 60, occlude=False)
        lx = 0.04 * math.sin(TAU * t)
        p.disc(lx, 0.07, 0.17, "accent", 235, occlude=False)
        p.disc(lx, 0.07, 0.08, "fill", 255, occlude=False)
        p.dot(lx - 0.05, 0.12, 2.0, "ink", 255)
        p.line(up, 4.4)
        p.line(lo, 4.0)
        cell(p, thick(bezier((0.5, 0.05), (0.76, 0.1), (0.98, 0.04), 20), [lerp(0.08, 0.04, i / 20) for i in range(21)]), 0, 2.4)
        cell(p, thick(bezier((-0.08, -0.16), (-0.1, -0.4), (-0.18, -0.7), 20), [lerp(0.08, 0.05, i / 20) for i in range(21)]), 0, 2.4)
        spiral = bezier3((0.12, -0.15), (0.14, -0.4), (0.27, -0.46), (0.40, -0.46), 20) + \
            [polar(lerp(0.16, 0.035, i / 50), 90 - 450 * i / 50, 0.4, -0.62) for i in range(1, 51)]
        cell(p, thick(spiral, [lerp(0.065, 0.03, i / len(spiral)) for i in range(len(spiral))]), 0, 2.4)
    p.glow(*sun, 0.22, int(150 + 80 * wave(t, 2)))
    for side in (1, -1):  # the name of Ra in cartouches either side
        x = side * 1.22
        car = p.circle_pts(x, 1.17, 0.11, 0, 180, 12) + p.circle_pts(x, 0.67, 0.11, 180, 360, 12)
        p.poly(car, "fill")
        p.line(car, 1.6, closed=True)
        p.line([(x - 0.1, 0.52), (x + 0.1, 0.52)], 2.0)
        for j, ch in enumerate("𓂋𓂝𓇳"):
            for dx, dy in ((0, 0), (0.006, 0), (0, 0.006), (0.006, 0.006)):
                p.text(ch, x + dx - 0.003, 1.12 - 0.2 * j + dy - 0.003, 26, "hiero", "ink", 255, upright=True)
            p.glow(x, 1.12 - 0.2 * j, 0.09, 110)
    p.line([(-1.46, -0.98), (1.46, -0.98)], 1.6)  # a frieze of uraei crowned with the sun
    p.line([(-1.46, -1.02), (1.46, -1.02)], 0.7, "ink", 200)
    for k in range(15):
        uraeus_front(p, -1.33 + 0.19 * k, -1.32, 0.22, t, k)
    p.line([(-1.46, -1.38), (1.46, -1.38)], 1.6)
    hierophant_frame(p, t, "THE EYE OF RA")


# ===================================================================================
#  II · THE EMERALD TABLET
# ===================================================================================
TABULA = ["VERVM SINE MENDACIO CERTVM ET VERISSIMVM",
          "QVOD EST INFERIVS EST SICVT QVOD EST SVPERIVS",
          "ET QVOD EST SVPERIVS EST SICVT QVOD EST INFERIVS",
          "AD PERPETRANDA MIRACVLA REI VNIVS",
          "ET SICVT OMNES RES FVERVNT AB VNO",
          "MEDIATIONE VNIVS SIC OMNES RES NATAE FVERVNT",
          "AB HAC VNA RE ADAPTATIONE",
          "PATER EIVS EST SOL · MATER EIVS LVNA",
          "PORTAVIT ILLVD VENTVS IN VENTRE SVO",
          "NVTRIX EIVS TERRA EST",
          "PATER OMNIS TELESMI TOTIVS MVNDI EST HIC",
          "VIS EIVS INTEGRA EST SI VERSA FVERIT IN TERRAM"]


def ecut(w, h, c, cy=0.0):
    """An emerald-cut outline: a rectangle with chamfered corners."""
    return [(-w + c, cy + h), (w - c, cy + h), (w, cy + h - c), (w, cy - h + c), (w - c, cy - h), (-w + c, cy - h), (-w, cy - h + c), (-w, cy + h - c)]


@one("tablet", "The Emerald Tablet", "Hermeticism", "Smaragdine",
     "The Tabula Smaragdina itself, found in the hands of Hermes in his tomb: every word of the Great Work cut into a single emerald")
def tablet(p, t, v):
    cy = -0.04
    fine_rays(p, (0, cy), 64, 0.9, 2.2, 130, t)
    p.glow(0, cy, 1.5, 110, "light")
    sol, luna = (-1.18, 1.12), (1.18, 1.12)  # the father and the mother
    fine_rays(p, sol, 24, 0.1, 0.36, 230, t, w=0.03, wobble=0.03, layer="flare")
    for i in range(16):  # the sun's own rays, straight and flaming by turns
        a = 22.5 * i + 45 * t
        if i % 2:
            gild(p, [polar(0.13, a - 6, *sol), polar(0.22, a, *sol), polar(0.13, a + 6, *sol)], 140, 0.8)
        else:
            p.line([polar(0.13 + 0.09 * k / 10, a + 7 * math.sin(k / 10 * TAU), *sol) for k in range(11)], 1.0)
    p.disc(*sol, 0.11, "ink")
    p.circle(*sol, 0.135, 1.0, "ink", 200)
    p.glow(*sol, 0.3, 230)
    p.disc(*luna, 0.12, "fill")
    p.circle(*luna, 0.12, 1.2)
    crescent(p, *luna, 0.115, 0, 0.5, "ink")
    p.glow(*luna, 0.26, 150)
    light = 135 + 50 * math.sin(TAU * t)  # the light that plays across the facets
    outer, mid, table = ecut(1.0, 1.24, 0.26, cy), ecut(0.91, 1.15, 0.23, cy), ecut(0.8, 1.04, 0.19, cy)
    gild(p, ecut(1.06, 1.3, 0.28, cy), 120, 2.6)
    p.line(ecut(1.03, 1.27, 0.27, cy), 0.8, "ink", 200, closed=True)
    for ring_a, ring_b in ((outer, mid), (mid, table)):  # the step facets
        for i in range(8):
            a0, a1, b1, b0 = ring_a[i], ring_a[(i + 1) % 8], ring_b[(i + 1) % 8], ring_b[i]
            ang = math.degrees(math.atan2((a0[1] + a1[1]) / 2 - cy, (a0[0] + a1[0]) / 2))
            lit = max(0.0, math.cos(math.radians(ang - light)))
            p.poly([a0, a1, b1, b0], "fill")
            p.poly([a0, a1, b1, b0], "accent", int(45 + 105 * lit ** 2), occlude=False)
            p.line([a0, a1, b1, b0], 0.8, "ink", 170, closed=True)
    p.poly(table, "fill")
    p.poly(table, "accent", 55, occlude=False)
    p.line(table, 1.2, "ink", 230, closed=True)
    for q in outer:  # claw prongs
        p.disc(*q, 0.035, "ink")
        p.circle(*q, 0.035, 0.8, "ink", 255)
    with p.clip(outer):  # a sweep of light through the stone
        x = lerp(-2.2, 2.2, t)
        p.poly([(x - 0.12, 1.6), (x + 0.12, 1.6), (x - 0.6, -1.6), (x - 0.84, -1.6)], "flare", 45, occlude=False)
        p.poly([(x + 0.25, 1.6), (x + 0.3, 1.6), (x - 0.3, -1.6), (x - 0.35, -1.6)], "flare", 70, occlude=False)
    p.text("TABVLA SMARAGDINA", 0, cy + 0.88, 12, "serif", "ink", 255, upright=True)
    p.line([(-0.52, cy + 0.8), (0.52, cy + 0.8)], 0.7, "ink", 200)
    p.text("☉", -0.62, cy + 0.88, 14, "symbols", "ink", 255, upright=True)
    p.text("☽", 0.62, cy + 0.88, 14, "symbols", "ink", 255, upright=True)
    lit_line = t * (len(TABULA) + 3) - 1.5
    for i, line in enumerate(TABULA):
        y = cy + 0.69 - i * 0.104
        p.text(line, 0, y, 8.4, "serif", "ink", 245, upright=True)
        lit = math.exp(-((i - lit_line) / 0.8) ** 2)
        if lit > 0.05:
            p.text(line, 0, y, 8.4, "serif", "flare", int(150 * lit), upright=True)
    p.line([(-0.52, cy - 0.6), (0.52, cy - 0.6)], 0.7, "ink", 200)
    p.text("HERMES TRISMEGISTVS", 0, cy - 0.7, 11, "serif", "ink", 255, upright=True)
    p.text("☿", 0, cy - 0.86, 18, "symbols", "ink", 255, upright=True)
    p.glow(0, cy - 0.86, 0.12, int(120 + 80 * wave(t, 2)))
    for i, q in enumerate(table):
        p.sparkle(*q, 0.07, int(240 * max(0.0, math.sin(TAU * (t + i / 8)))), rot=45)
    for i in range(16):
        u = (t + i / 16) % 1
        x = lerp(-1.4, 1.4, (i * 0.618) % 1) + 0.05 * math.sin(TAU * (u + i * 0.3))
        p.sparkle(x, lerp(-1.4, 1.4, u), 0.03, int(200 * math.sin(math.pi * u)), rot=45)
    hierophant_frame(p, t, "THE EMERALD TABLET")


# ===================================================================================
#  III · AUM
# ===================================================================================
GAYATRI = "ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्"


def petal_shape(base_l, base_r, tip, bulge=0.35):
    (x0, y0), (x1, y1), (tx, ty) = base_l, base_r, tip
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = tx - mx, ty - my
    w = math.hypot(x1 - x0, y1 - y0)
    nx, ny = (x1 - x0) / w, (y1 - y0) / w
    c1 = (x0 - nx * w * bulge + dx * 0.45, y0 - ny * w * bulge + dy * 0.45)
    c2 = (x1 + nx * w * bulge + dx * 0.45, y1 + ny * w * bulge + dy * 0.45)
    return bezier3(base_l, c1, (tx - nx * w * 0.12, ty - ny * w * 0.12), tip, 14) + \
        bezier3(tip, (tx + nx * w * 0.12, ty + ny * w * 0.12), c2, base_r, 14)[1:]


@one("aum", "AUM, the Pranava", "Vedic Mysteries", "Saffron Night",
     "The sacred syllable from which the Vedas say the worlds were sounded into being, enthroned on the lotus and ringed by the Gayatri and a mala of one hundred and eight beads")
def aum(p, t, v):
    c = (0, 0.2)
    fine_rays(p, c, 96, 0.6, 2.2, 140, t)
    p.glow(*c, 1.2, 120, "light")
    for i in range(32):  # the outer lotus of thirty-two petals
        a = 90 + 11.25 * i + 11.25 * t
        pet = lotus_petal(1.0, 1.22, a, 5.0)
        p.poly(pet, "fill")
        p.poly(pet, "accent", 30, occlude=False)
        p.line(pet, 0.9, "ink", 220)
    for i in range(16):
        a = 90 + 22.5 * i - 22.5 * t + 11.25
        cell(p, lotus_petal(0.78, 1.0, a, 10.0), 70, 1.1)
        p.line([polar(0.8, a), polar(0.96, a)], 0.5, "ink", 150)
    for r, w_ in ((0.78, 1.4), (1.23, 1.0), (1.26, 0.6)):
        p.circle(0, 0, r, w_, "ink", 220)
    for i in range(108):  # the mala; a light counts the beads, one quarter-round per loop
        a = 90 - i * 360 / 108
        guru = i % 27 == 0
        p.dot(*polar(1.31, a), 2.6 if guru else 1.6, "accent" if guru else "ink", 255)
        d = (t * 27 - i) % 27
        d = min(d, 27 - d)  # a soft light gliding from bead to bead
        if d < 1.5:
            p.dot(*polar(1.31, a), 2.4, "flare", int(230 * (1 - d / 1.5)))
    words = GAYATRI.split()
    for i, w in enumerate(words):
        a = 90 - 360 * (i + 0.5) / len(words)
        p.text(w, *polar(1.42, a), 12.5, "deva", "ink", 240, angle=a - 90)
    halo = p.circle_pts(*c, 0.66)[:-1]  # the disc the syllable sits in
    p.poly(halo, "fill")
    p.poly(halo, "accent", 28, occlude=False)
    for i in range(72):
        p.line([polar(0.1, 5 * i, *c), polar(0.64, 5 * i, *c)], 0.5, "ink", 45)
    p.circle(*c, 0.66, 2.4)
    p.circle(*c, 0.62, 0.7, "ink", 190)
    for i in range(36):
        p.dot(*polar(0.64, 10 * i + 10 * t, *c), 1.1, "ink", 230)
    ty = -0.58  # the lotus throne: reflexed lower petals, a beaded band, upturned upper petals
    for i in range(9):
        x = (i - 4) * 0.13
        base_y = ty - 0.12 + 0.012 * (i - 4) ** 2
        cell(p, petal_shape((x - 0.07, base_y), (x + 0.07, base_y), (x * 1.18, base_y - 0.24 + 0.01 * abs(i - 4))), 50 + 15 * (i % 2), 1.1)
    gild(p, [(-0.62, ty - 0.13), (0.62, ty - 0.13), (0.66, ty - 0.06), (-0.66, ty - 0.06)], 110, 1.2)
    for i in range(23):
        p.dot(-0.6 + 0.0545 * i, ty - 0.095, 1.5, "fill", 255)
    for row, (n, sp_, h, yo) in enumerate(((11, 0.12, 0.3, 0.0), (9, 0.125, 0.36, 0.02))):
        for i in range(n):
            x = (i - (n - 1) / 2) * sp_
            base_y = ty - 0.06 + yo
            tip = (x * 1.25, base_y + h - 0.025 * abs(i - (n - 1) / 2))
            cell(p, petal_shape((x - 0.072, base_y), (x + 0.072, base_y), tip, 0.3), 45 + 30 * row, 1.1)
            p.line(bezier((x, base_y + 0.02), (x * 1.1, base_y + h * 0.5), tip, 10)[:-2], 0.5, "ink", 160)
    p.text("ॐ", c[0], c[1] + 0.02, 214, "deva", "flare", int(35 + 30 * wave(t, 2)), upright=True)
    p.text("ॐ", c[0], c[1] - 0.02, 208, "deva", "ink", 255, upright=True)
    p.sparkle(0.16, c[1] + 0.36, 0.14, int(200 + 55 * wave(t, 2)), rot=90 * t)
    p.glow(0.16, c[1] + 0.36, 0.09, 255)
    hierophant_frame(p, t, "AUM · THE PRANAVA")


# ===================================================================================
#  IV · THE OPHANIM
# ===================================================================================
def _rot(vv, ax, ay, az):
    x, y, z = vv
    for a, (i, j) in ((ax, (1, 2)), (ay, (0, 2)), (az, (0, 1))):
        c, s = math.cos(a), math.sin(a)
        w = [x, y, z]
        w[i], w[j] = c * w[i] - s * w[j], s * w[i] + c * w[j]
        x, y, z = w
    return x, y, z


@one("ophanim", "The Ophanim", "Merkabah Mysticism", "Seraph Fire",
     "The wheels within wheels that Ezekiel saw beside the living creatures by the river Chebar: their rims were high and dreadful, and full of eyes round about")
def ophanim(p, t, v):
    fine_rays(p, (0, 0), 72, 0.3, 2.2, 150, t)
    p.glow(0, 0, 1.3, 160, "light")
    flap = 4 * math.sin(TAU * t)
    # six wings: with twain he covered his face, with twain his feet, with twain he did fly
    for raise_deg, span, sh, fl in ((-62, 1.0, (0.1, -0.12), 0.0), (66, 1.08, (0.1, 0.14), 0.0), (14, 1.32, (0.12, 0.02), 1.0)):
        for side in (1, -1):
            with p.tf(dx=side * sh[0], dy=sh[1], sx=side):
                bird_wing(p, raise_deg, span, t, flap * fl, flame=0.06 * fl, tint=40)
    rings = [(0.98, lambda u: (0.25, TAU * u, 0.0)), (0.8, lambda u: (TAU * u + 1.2, 0.6, 0.3)), (0.62, lambda u: (1.0, -TAU * u, TAU * u))]
    items = []
    for ri, (R, rot) in enumerate(rings):
        ax, ay, az = rot(t)
        bw, N = 0.1, 120
        po = [_rot((math.cos(a) * (R + bw / 2), math.sin(a) * (R + bw / 2), 0.0), ax, ay, az) for a in (TAU * k / N for k in range(N + 1))]
        pi_ = [_rot((math.cos(a) * (R - bw / 2), math.sin(a) * (R - bw / 2), 0.0), ax, ay, az) for a in (TAU * k / N for k in range(N + 1))]
        for k in range(N):
            items.append(((po[k][2] + po[k + 1][2]) / 2, "band", (po[k], po[k + 1], pi_[k + 1], pi_[k])))
        ne = 11
        for k in range(ne):
            a = TAU * k / ne
            q = _rot((math.cos(a) * R, math.sin(a) * R, 0.0), ax, ay, az)
            q2 = _rot((math.cos(a + 0.05) * R, math.sin(a + 0.05) * R, 0.0), ax, ay, az)
            items.append((q[2] + 0.001, "eye", (q, math.degrees(math.atan2(q2[1] - q[1], q2[0] - q[0])), ri * ne + k)))
    for z, kind, d in sorted(items, key=lambda it: (round(it[0], 4), it[1], str(it[2])[:40])):  # stable paint order
        k = (z + 1.05) / 2.1
        if kind == "band":
            quad = [q[:2] for q in d]
            p.poly(quad, "fill")
            p.poly(quad, "ink", int(lerp(40, 150, k)), occlude=False)
            p.line([quad[0], quad[1]], lerp(0.7, 1.6, k), "ink", int(lerp(90, 255, k)))
            p.line([quad[2], quad[3]], lerp(0.7, 1.6, k), "ink", int(lerp(90, 255, k)))
        else:
            q, ang, idx = d
            if z < -0.2:
                continue
            blink = max(0.0, 1 - abs(((t * 2 + idx * 0.37) % 1) - 0.5) / 0.05)
            with p.tf(dx=q[0], dy=q[1], rot=ang, s=0.6 + 0.4 * k):
                p.disc(0, 0, 0.075, "fill")
                p.circle(0, 0, 0.075, 1.0, "ink", 220)
                eye(p, 0, 0, 0.13, 0.07, t, blink, (0, 0), 1.0, lashes=False)
                p.glow(0, 0, 0.1, int(110 * k))
    for i in range(16):  # the burning heart, and the great eye within it
        a = 90 + i * 22.5 + 8 * math.sin(TAU * (t + i * 0.2))
        h = 0.32 + 0.12 * math.sin(TAU * (3 * t + i * 0.3))
        p.ray(0, 0, a, 0.1, h, 0.1, 0.0, 220, "flare", steps=8, core=False)
    p.glow(0, 0, 0.5, 255, "light")
    p.disc(0, 0, 0.2, "fill")
    p.circle(0, 0, 0.2, 2.0)
    p.circle(0, 0, 0.23, 0.8, "ink", 200)
    eye(p, 0, 0, 0.32, 0.16, t, max(0.0, 1 - abs(t - 0.5) / 0.04), (math.sin(TAU * t), 0.3 * math.sin(2 * TAU * t)), 1.6)
    p.glow(0, 0, 0.22, int(150 + 80 * wave(t, 2)))
    for i in range(3):  # Holy, holy, holy
        a = 245 + 25 * i
        p.text("קדוש", *polar(1.42, a), 17, "hebrew", "accent", 240, angle=a + 90)
        if i < 2:
            p.sparkle(*polar(1.42, a + 12.5), 0.04, 220)
    hierophant_frame(p, t, "THE OPHANIM")


# ===================================================================================
#  V · YGGDRASIL
# ===================================================================================
def _branch(p, x, y, ang, L, w, depth, rng, t, sway, tips, tint, spread=26):
    a = ang + sway * math.sin(TAU * t + depth * 0.7 + x * 3) * (1 / (depth + 1))
    ex, ey = polar(L, a, x, y)
    bend = rng.uniform(-0.12, 0.12) * L
    cx, cy = (x + ex) / 2 - math.sin(math.radians(a)) * bend, (y + ey) / 2 + math.cos(math.radians(a)) * bend
    path = bezier((x, y), (cx, cy), (ex, ey), 8)
    seg = thick(path, [lerp(w, w * 0.7, i / 8) for i in range(9)])
    p.poly(seg, "fill")
    p.poly(seg, "ink", tint, occlude=False)
    if w > 0.03:
        p.line(path[1:-1], 0.5, "ink", 90)
    if depth == 0:
        tips.append((ex, ey, a))
        return
    kids = 3 if rng.random() < 0.4 else 2
    for k in range(kids):
        off = (k - (kids - 1) / 2) * spread + rng.uniform(-9, 9)
        _branch(p, ex, ey, a + off, L * rng.uniform(0.68, 0.82), w * 0.66, depth - 1, rng, t, sway, tips, tint, spread)


@one("yggdrasil", "Yggdrasil, the World Tree", "Norse Mysteries", "World Ash",
     "The ash that holds the nine worlds in its branches and roots, where Odin hung nine nights to win the runes, with the serpent of Midgard coiled about its waist")
def yggdrasil(p, t, v):
    for k in range(3):  # aurora
        base = 1.05 + 0.13 * k
        pts = [(x, base + 0.1 * math.sin(TAU * (t + x * 0.5 + k * 0.3)) + 0.04 * math.sin(TAU * (2 * t + x * 1.3)))
               for x in [lerp(-1.5, 1.5, i / 60) for i in range(61)]]
        p.poly(thick(pts, [0.12 * (0.5 + 0.5 * math.sin(math.pi * i / 60)) for i in range(61)]), "light", int(40 + 25 * wave(t, 1, k / 3)), occlude=False)
    for i, ch in enumerate(FUTHARK * 2):
        a = 90 - 360 * i / 48
        p.text(ch, *polar(1.5, a), 12, "runic", "ink", 170, angle=a - 90)
    p.circle(0, 0, 1.43, 0.7, "ink", 150)
    p.circle(0, 0, 1.57, 0.7, "ink", 150)
    p.glow(0, 0.72, 0.9, 120, "light")
    p.glow(0, -0.85, 0.6, 70, "light")
    rng = random.Random(3331)  # three great roots to the three wells
    base = (0, -0.46)
    wells = [("URD", (-0.85, -0.98)), ("HVERGELMIR", (0.0, -1.1)), ("MIMIR", (0.85, -0.98))]
    tips = []
    for name, wq in wells:
        root = bezier3(base, (wq[0] * 0.3, base[1] - 0.12), (wq[0] * 0.8, wq[1] + 0.32), (wq[0], wq[1] + 0.08), 24)
        seg = thick(root, [lerp(0.13, 0.03, (i / 24) ** 0.8) for i in range(25)])
        p.poly(seg, "fill")
        p.poly(seg, "ink", 150, occlude=False)
        p.line(root[1:-2], 0.6, "ink", 90)
        for j in (6, 12, 17):
            _branch(p, *root[j], -90 + rng.uniform(-60, 60), 0.16, 0.03, 2, rng, t, 0.0, tips, 140, 34)
        pool = ellipse(wq[0], wq[1], 0.2, 0.065)
        p.poly(pool, "fill")
        p.poly(pool, "accent", 70, occlude=False)
        p.line(pool, 1.4, closed=True)
        for r in range(3):
            u = (t + r / 3) % 1
            p.line(ellipse(wq[0], wq[1], 0.2 * u, 0.065 * u), 0.6, "accent", int(220 * (1 - u) * min(1.0, u * 6)), closed=True)
        p.text(name, wq[0], wq[1] - 0.12, 7.5, "serif", "ink", 200, upright=True)
    for x, y, a in tips:
        p.dot(x, y, 1.1, "accent", 160)
    nid = [(0.27 * math.cos(math.radians(a)), -1.1 + 0.1 * math.sin(math.radians(a))) for a in range(150, -170, -8)] + \
        bezier((0.27 * math.cos(math.radians(-170)), -1.1 + 0.1 * math.sin(math.radians(-170))), (-0.3, -0.98), (-0.12, -0.86), 10)[1:]
    serpent_run(p, nid, [lerp(0.008, 0.04, (i / len(nid)) ** 0.7) for i in range(len(nid))], flow=-3 * t)  # Níðhöggr round Hvergelmir
    snake_head_top(p, *nid[-1], 40, 0.04, t)
    trunk = bezier3((-0.2, -0.5), (-0.12, -0.25), (-0.11, 0.05), (-0.09, 0.22), 16) + bezier3((0.09, 0.22), (0.11, 0.05), (0.12, -0.25), (0.2, -0.5), 16)
    p.poly(trunk, "fill")
    p.poly(trunk, "ink", 160, occlude=False)
    p.line(trunk, 1.4, closed=True)
    for i in range(7):
        x = -0.12 + 0.04 * i
        p.line(bezier((x * 1.4, -0.48), (x + 0.02 * math.sin(i * 2.1), -0.12), (x * 0.8, 0.2), 12), 0.6, "ink", 80)
    rng = random.Random(3332)  # the crown
    tips = []
    for ang in (160, 136, 113, 90, 67, 44, 20):
        _branch(p, 0.0, 0.2, ang, 0.3 if ang in (160, 20) else 0.32, 0.075, 4, rng, t, 2.0, tips, 160, 24)
    leaf_rng = random.Random(3333)
    for i, (x, y, a) in enumerate(tips):
        for j in range(6):
            la = a + leaf_rng.uniform(-70, 70)
            q = polar(leaf_rng.uniform(0.01, 0.07), la, x, y)
            shimmer = 0.5 + 0.5 * math.sin(TAU * (t + (i * 0.13 + j * 0.3) % 1))
            p.poly(ellipse(q[0], q[1], 0.026, 0.009, la, 10), "accent", int(80 + 150 * shimmer), occlude=False)
        if i % 9 == 0:
            p.glow(x, y, 0.07, int(90 * wave(t, 1, i * 0.21)))
    c = (0, -0.16)  # Jörmungandr round Midgard
    ell = [(0.6 * math.cos(a), c[1] + 0.12 * math.sin(a)) for a in (TAU * k / 160 for k in range(161))]
    dep = [-math.sin(TAU * k / 160) for k in range(161)]
    run, sgn, runs = [ell[0]], dep[0] > 0, []
    for q, d in zip(ell[1:], dep[1:]):
        run.append(q)
        if (d > 0) != sgn:
            runs.append((sgn, run))
            run, sgn = [q], d > 0
    runs.append((sgn, run))
    worlds = [("ASGARD", (0, 0.98)), ("ALFHEIM", (-0.7, 0.86)), ("VANAHEIM", (0.7, 0.86)), ("JOTUNHEIM", (-1.12, 0.32)),
              ("MUSPELHEIM", (1.12, 0.32)), ("MIDGARD", c), ("SVARTALFHEIM", (-1.08, -0.5)), ("NIFLHEIM", (1.08, -0.5)), ("HELHEIM", (-0.32, -1.32))]
    for i, (name, q) in enumerate(worlds):
        if name == "MIDGARD":
            for front, r in runs:
                if not front:
                    serpent_run(p, r, [0.06] * len(r), front=False)
        lit = 0.6 + 0.4 * wave(t, 1, i / 9)
        p.glow(*q, 0.2, int(200 * lit))
        p.disc(*q, 0.06, "fill")
        p.circle(*q, 0.06, 1.6)
        p.circle(*q, 0.08, 0.6, "ink", 180)
        p.text(FUTHARK[(i * 3) % len(FUTHARK)], *q, 12, "runic", "accent", 255, upright=True)
        lab = (q[0], q[1] - 0.12) if name not in ("HELHEIM", "MIDGARD") else ((q[0] - 0.3, q[1]) if name == "HELHEIM" else (q[0], q[1] - 0.2))
        pw = 0.012 * len(name) + 0.05
        plaque = [(lab[0] - pw, lab[1] - 0.035), (lab[0] + pw, lab[1] - 0.035), (lab[0] + pw + 0.025, lab[1]), (lab[0] + pw, lab[1] + 0.035),
                  (lab[0] - pw, lab[1] + 0.035), (lab[0] - pw - 0.025, lab[1])]
        p.poly(plaque, "fill")
        p.line(plaque, 0.7, "ink", 200, closed=True)
        p.text(name, *lab, 7.5, "serif", "ink", 245, upright=True)
        if name == "MIDGARD":
            for front, r in runs:
                if front:
                    serpent_run(p, r, [0.06] * len(r), flow=-4 * t)
            snake_head_top(p, *ell[3], 150, 0.06, t)
    with p.tf(dy=1.24, s=0.27):  # the eagle on the topmost bough
        for side in (1, -1):
            with p.tf(dx=side * 0.08, sx=side):
                bird_wing(p, 28, 1.0, t, 5 * math.sin(TAU * t), tint=30)
        gild(p, ellipse(0, -0.1, 0.11, 0.24), 90, 1.2)
        gild(p, [(0.0, 0.13), (0.07, 0.2), (0.1, 0.3), (0.0, 0.36), (-0.08, 0.3), (-0.07, 0.2)], 90, 1.2)
        p.poly([(0.06, 0.3), (0.15, 0.3), (0.1, 0.25)], "ink", occlude=False)
        p.dot(0.03, 0.3, 1.4, "accent")
    hierophant_frame(p, t, "YGGDRASIL")


# ===================================================================================
#  VI · THE PHOENIX
# ===================================================================================
def flame_tongue(p, x, y0, h, w, sway, layer, vv):
    tip = (x + sway * 1.4, y0 + h)
    fl = bezier3((x - w, y0), (x - w * 1.3, y0 + h * 0.35), (x + sway - w * 0.5, y0 + h * 0.7), tip, 12) + \
        bezier3(tip, (x + sway + w * 0.8, y0 + h * 0.6), (x + w * 1.2, y0 + h * 0.3), (x + w, y0), 12)[1:]
    p.poly(fl, layer, vv, occlude=False)


@one("phoenix", "The Phoenix", "Alchemy & Egypt", "Phoenix Flame",
     "The Bennu, the bird of Heliopolis, that burns upon its nest of spices and rises again from its own ashes: the alchemists' sign of the reddened Stone")
def phoenix(p, t, v):
    sun = (0, 0.62)
    fine_rays(p, sun, 72, 0.5, 2.2, 160, t)
    p.glow(*sun, 0.9, 200, "light")
    p.circle(*sun, 0.5, 1.2, "ink", 170)
    p.circle(*sun, 0.54, 0.6, "ink", 120)
    rise = 0.03 * math.sin(TAU * t)
    for k in range(7):  # the tail: long plumes sweeping down and out around the fire
        sgn = (k - 3) / 3
        tip = (sgn * 1.05 + 0.04 * math.sin(TAU * (t + k * 0.2)), -0.62 - 0.4 * (1 - abs(sgn)) ** 1.5 + 0.12 * abs(sgn))
        plume = bezier3((sgn * 0.05, -0.36 + rise), (sgn * 0.12, -0.78), (sgn * 0.75 + 0.06 * math.sin(TAU * t + k), -0.92 + 0.1 * abs(sgn)), tip, 34)
        ws = [0.03 + 0.1 * math.sin(math.pi * min(1.0, (i / 34) ** 1.3 * 1.05)) ** 0.7 for i in range(35)]
        shape = thick(plume, ws)
        p.poly(shape, "fill")
        p.poly(shape, "ink", 50, occlude=False)
        p.poly(thick(plume[6:], [w * 0.45 for w in ws[6:]]), "accent", 80, occlude=False)
        p.line(shape, 0.9, closed=True)
        p.line(plume[2:-3], 0.6, "ink", 200)
        for j in range(3, 32, 2):  # barbs fanning off the shaft
            (x0, y0), (x1, y1) = plume[j], plume[j + 1]
            dl = math.hypot(x1 - x0, y1 - y0) or 1
            for sg in (1, -1):
                w = ws[j] * 0.5
                p.line([(x0, y0), (x0 - (y1 - y0) / dl * sg * w + (x1 - x0) / dl * w * 0.8, y0 + (x1 - x0) / dl * sg * w + (y1 - y0) / dl * w * 0.8)], 0.45, "ink", 140)
        q = plume[27]  # the eye of the plume
        p.poly(ellipse(q[0], q[1], 0.07, 0.05, math.degrees(math.atan2(plume[28][1] - q[1], plume[28][0] - q[0]))), "fill")
        p.circle(*q, 0.05, 1.1)
        p.disc(*q, 0.035, "accent", 240, occlude=False)
        p.disc(*q, 0.016, "fill", 255, occlude=False)
        p.glow(*q, 0.11, int(150 + 80 * wave(t, 2, k / 7)))
        p.ray(*plume[-1], math.degrees(math.atan2(plume[-1][1] - plume[-3][1], plume[-1][0] - plume[-3][0])), 0, 0.14, 0.06, 0, 230, "flare", steps=8, core=False)
    flap = 7 * math.sin(TAU * t)  # the wings, raised to the sun, every feather tipped with flame
    for side in (1, -1):
        with p.tf(dx=side * 0.12, dy=0.18 + rise, sx=side):
            bird_wing(p, 46, 1.3, t, flap, flame=0.1, tint=45)
    with p.tf(dy=rise):
        body = bezier3((0.0, 0.34), (0.2, 0.3), (0.2, -0.15), (0.0, -0.42), 20) + bezier3((0.0, -0.42), (-0.2, -0.15), (-0.2, 0.3), (0.0, 0.34), 20)[1:]
        gild(p, body, 80, 1.4)
        for r in range(7):  # breast feathers
            n = 5 - abs(r - 2) // 2
            for k in range(n):
                x = (k - (n - 1) / 2) * 0.055 + (0.027 if r % 2 else 0)
                p.arc(x, 0.24 - r * 0.085, 0.03, 200, 340, 0.6, "ink", 190)
        for side in (1, -1):  # talons drawn up beneath
            p.line([(side * 0.05, -0.38), (side * 0.09, -0.48), (side * 0.06, -0.52)], 1.2, "ink", 230)
            p.line([(side * 0.09, -0.48), (side * 0.13, -0.5)], 1.0, "ink", 230)
        neck = bezier3((0.0, 0.3), (0.06, 0.45), (-0.02, 0.58), (0.06, 0.7), 20)
        gild(p, thick(neck, [lerp(0.15, 0.085, i / 20) for i in range(21)]), 80, 1.2)
        for j in range(3, 18, 3):
            p.arc(*neck[j], 0.03, 200, 340, 0.6, "ink", 170)
        head = bezier3((0.0, 0.68), (0.02, 0.8), (0.16, 0.82), (0.2, 0.75), 14) + \
            bezier3((0.2, 0.75), (0.21, 0.7), (0.16, 0.66), (0.1, 0.65), 10)[1:] + [(0.04, 0.64)]
        gild(p, head, 90, 1.3)
        gild(p, [(0.19, 0.765), (0.29, 0.75), (0.31, 0.72), (0.28, 0.705), (0.26, 0.725), (0.19, 0.72)], 160, 1.2)  # hooked beak
        for k in range(5):  # the crest, sweeping back from the crown
            base = (0.06 + 0.02 * k, 0.8 - 0.005 * k)
            cr = bezier3(base, (base[0] - 0.02, base[1] + 0.1), (base[0] - 0.12 - k * 0.03, base[1] + 0.16 - k * 0.01),
                         (base[0] - 0.24 - k * 0.04, base[1] + 0.1 - k * 0.04 + 0.015 * math.sin(TAU * (t + k * 0.2))), 16)
            p.poly(thick(cr, [lerp(0.03, 0.006, i / 16) for i in range(17)]), "ink", 230, occlude=False)
            p.disc(*cr[-1], 0.016, "accent", 255, occlude=False)
            p.glow(*cr[-1], 0.05, 170)
        p.disc(0.135, 0.745, 0.019, "accent", 255, occlude=False)
        p.dot(0.138, 0.745, 1.1, "fill", 255)
        p.glow(0.135, 0.745, 0.08, 230)
        p.line([(0.1, 0.72), (0.03, 0.7)], 0.7, "ink", 200)
    for i in range(11):  # the burning nest of spices
        x = -0.6 + 0.12 * i
        center = 1.25 if 3 < i < 7 else 0.85
        for layer, sc, vv in (("accent", 1.0, 200), ("flare", 0.55, 245)):
            h = (0.38 + 0.12 * math.sin(TAU * (2 * t + i * 0.37)) + 0.06 * math.sin(TAU * (3 * t + i * 0.71))) * sc * center
            flame_tongue(p, x, -1.06, h, 0.075 * sc, 0.05 * math.sin(TAU * (t + i * 0.2)) * sc, layer, vv)
        u = (t * 2 + i * 0.29) % 1
        p.sparkle(x + 0.06 * math.sin(TAU * (u + i)), -1.0 + 0.95 * u, 0.03, int(230 * math.sin(math.pi * u)))
    nest = bezier3((-0.72, -1.04), (-0.5, -1.24), (0.5, -1.24), (0.72, -1.04), 30)
    gild(p, nest + [(0.66, -1.06), (-0.66, -1.06)], 60, 1.4)
    for k in range(14):
        x0 = -0.66 + k * 0.1
        p.line(bezier((x0, -1.07), (x0 + 0.06, -1.13), (x0 + 0.13, -1.18), 6), 0.7, "ink", 190)
        p.line(bezier((x0 + 0.1, -1.07), (x0 + 0.03, -1.13), (x0 - 0.02, -1.17), 6), 0.7, "ink", 150)
    hierophant_frame(p, t, "THE PHOENIX")


# ===================================================================================
#  VII · THE SUN STONE
# ===================================================================================
def day_sign(p, k, s):
    """The twenty day signs as small engraved pictographs, centred on the
    origin, about `s` across. Order follows the stone, from Cipactli."""
    L = lambda pts, w=0.9, v=230: p.line([(x * s, y * s) for x, y in pts], w, "ink", v)  # noqa: E731
    C = lambda x, y, r, w=0.9: p.circle(x * s, y * s, r * s, w, "ink", 230)  # noqa: E731
    D = lambda x, y, r: p.dot(x * s, y * s, r, "accent", 255)  # noqa: E731
    k %= 20
    if k == 0:  # crocodile: long jaw with teeth
        L([(-0.45, 0.1), (0.45, 0.2), (0.45, 0.05), (-0.45, -0.05)])
        L([(-0.45, -0.05), (0.4, -0.25)])
        for j in range(5):
            L([(-0.3 + j * 0.15, j * 0.03), (-0.25 + j * 0.15, -0.1)], 0.6)
        D(-0.25, 0.18, 1.2)
    elif k == 1:  # wind: Ehecatl's beaked mask and spiral
        C(-0.1, 0.05, 0.28)
        L([(0.18, 0.08), (0.45, -0.02), (0.18, -0.12)])
        L([polar(0.03 + 0.012 * j, 90 + 35 * j, -0.1, 0.05) for j in range(16)], 0.7)
    elif k == 2:  # house
        L([(-0.35, -0.4), (-0.35, 0.05), (0.35, 0.05), (0.35, -0.4), (-0.35, -0.4)])
        L([(-0.45, 0.05), (0.0, 0.42), (0.45, 0.05)])
        L([(-0.1, -0.4), (-0.1, -0.12), (0.1, -0.12), (0.1, -0.4)], 0.7)
    elif k == 3:  # lizard
        L([(-0.45, -0.1), (-0.15, 0.0), (0.2, 0.0), (0.42, 0.12)])
        for x in (-0.05, 0.15):
            L([(x, 0.0), (x - 0.08, 0.25)], 0.7)
            L([(x, 0.0), (x - 0.08, -0.25)], 0.7)
        D(0.36, 0.14, 1.0)
    elif k == 4:  # serpent
        L([(-0.45 + 0.9 * j / 20, 0.18 * math.sin(j / 20 * 2.5 * TAU)) for j in range(21)], 1.1)
        D(0.42, 0.05, 1.2)
    elif k == 5:  # death: skull
        C(0.0, 0.08, 0.3)
        C(-0.11, 0.1, 0.08, 0.8)
        C(0.11, 0.1, 0.08, 0.8)
        L([(-0.15, -0.3), (0.15, -0.3)])
        for j in range(4):
            L([(-0.11 + j * 0.075, -0.18), (-0.11 + j * 0.075, -0.3)], 0.6)
    elif k == 6:  # deer: head and antlers
        C(0.0, -0.12, 0.2)
        for sg in (1, -1):
            L([(sg * 0.12, 0.05), (sg * 0.25, 0.4), (sg * 0.4, 0.45)], 0.8)
            L([(sg * 0.2, 0.28), (sg * 0.06, 0.42)], 0.7)
        D(-0.07, -0.08, 1.0)
    elif k == 7:  # rabbit: head and long ears
        C(0.0, -0.15, 0.2)
        for sg in (1, -1):
            L([(sg * 0.07 + 0.08 * math.sin(a) * sg, 0.02 + 0.22 * (1 - math.cos(a))) for a in (math.pi * j / 10 for j in range(11))], 0.8)
        D(-0.07, -0.12, 1.0)
    elif k == 8:  # water: stream with drops
        L([(-0.4, 0.2), (-0.1, 0.0), (0.1, 0.1), (0.4, -0.15)], 1.2)
        for x, y in ((-0.25, -0.2), (0.0, -0.3), (0.25, 0.25)):
            C(x, y, 0.07, 0.7)
    elif k == 9:  # dog: head with pointed ear
        L([(-0.35, -0.2), (-0.3, 0.15), (-0.1, 0.4), (0.0, 0.15), (0.35, 0.1), (0.4, -0.05), (0.1, -0.15), (-0.35, -0.2)])
        D(0.05, 0.05, 1.0)
    elif k == 10:  # monkey: face with curled tail
        C(-0.1, 0.05, 0.22)
        L([polar(0.18 - 0.008 * j, -90 + 22 * j, 0.22, -0.1) for j in range(18)], 0.8)
        D(-0.16, 0.08, 1.0)
        D(-0.04, 0.08, 1.0)
    elif k == 11:  # grass: twisted strands
        for j in range(3):
            L([((j - 1) * 0.18 + 0.08 * math.sin(i / 10 * TAU + j), -0.4 + 0.8 * i / 10) for i in range(11)], 0.8)
    elif k == 12:  # reed: shaft and fletching
        L([(0.0, -0.45), (0.0, 0.45)], 1.1)
        for j in range(3):
            L([(0.0, 0.3 - j * 0.12), (0.18, 0.4 - j * 0.12)], 0.7)
            L([(0.0, 0.3 - j * 0.12), (-0.18, 0.4 - j * 0.12)], 0.7)
    elif k == 13:  # jaguar: spotted head
        C(0.0, 0.0, 0.32)
        for x, y in ((-0.12, 0.1), (0.12, 0.12), (0.0, -0.12), (-0.15, -0.1), (0.15, -0.08)):
            C(x, y, 0.05, 0.7)
        for sg in (1, -1):
            L([(sg * 0.2, 0.25), (sg * 0.28, 0.4), (sg * 0.32, 0.22)], 0.7)
    elif k == 14:  # eagle: hooked beak
        L([(-0.3, 0.25), (0.1, 0.3), (0.38, 0.12), (0.4, -0.05), (0.28, 0.02), (0.1, -0.05), (-0.3, -0.25)])
        D(0.0, 0.14, 1.2)
    elif k == 15:  # vulture: beak and ruff
        L([(-0.1, 0.2), (0.25, 0.15), (0.38, 0.0), (0.2, -0.02)])
        for j in range(5):
            L([(-0.3 + 0.05 * j, -0.05 - 0.05 * j), (-0.1 + 0.05 * j, -0.15 - 0.05 * j)], 0.6)
        D(0.05, 0.1, 1.0)
    elif k == 16:  # movement: ollin
        L([(-0.35, 0.35), (0.35, -0.35)], 1.2)
        L([(-0.35, -0.35), (0.35, 0.35)], 1.2)
        C(0.0, 0.0, 0.12)
        D(0.0, 0.0, 1.0)
    elif k == 17:  # flint knife with a face
        L([(0.0, 0.45), (0.2, 0.0), (0.0, -0.45), (-0.2, 0.0), (0.0, 0.45)], 1.0)
        L([(-0.1, 0.0), (0.1, 0.0)], 0.6)
        D(-0.05, 0.12, 1.0)
    elif k == 18:  # rain: Tlaloc's goggles and falling drops
        C(-0.12, 0.2, 0.1)
        C(0.12, 0.2, 0.1)
        for x in (-0.25, 0.0, 0.25):
            L([(x, -0.05), (x, -0.4)], 0.8)
    else:  # flower
        for j in range(4):
            q = polar(0.17, 45 + 90 * j)
            C(q[0], q[1], 0.15, 0.8)
        C(0.0, 0.0, 0.08)
        D(0.0, 0.0, 1.1)


def tonatiuh(p, t):
    """The face at the centre of the stone, its tongue a flint knife."""
    gild(p, ellipse(0, 0.0, 0.15, 0.17), 120, 1.6)
    p.poly([(-0.14, 0.1), (0.14, 0.1), (0.15, 0.14), (-0.15, 0.14)], "ink", 200, occlude=False)  # headband
    for x in (-0.09, -0.03, 0.03, 0.09):
        p.disc(x, 0.12, 0.012, "accent", 255, occlude=False)
    for sg in (1, -1):
        eye_ = ellipse(sg * 0.06, 0.04, 0.035, 0.016)
        p.poly(eye_, "fill")
        p.line(eye_, 0.9, closed=True)
        p.dot(sg * 0.06, 0.04, 1.2, "accent")
        p.line([(sg * 0.025, 0.07), (sg * 0.1, 0.075)], 0.8, "ink", 230)
        ear = (sg * 0.18, 0.0)  # ear spools with pendants
        p.disc(*ear, 0.04, "fill")
        p.circle(*ear, 0.04, 1.0)
        p.circle(*ear, 0.018, 0.7, "ink", 200)
        p.line([(ear[0], -0.04), (ear[0], -0.1)], 1.0)
        p.dot(ear[0], -0.11, 1.4, "accent")
    p.poly([(-0.015, 0.03), (0.015, 0.03), (0.03, -0.04), (-0.03, -0.04)], "fill")
    p.line([(-0.015, 0.03), (-0.03, -0.04), (0.03, -0.04), (0.015, 0.03)], 0.8)
    mouth = [(-0.06, -0.07), (0.06, -0.07), (0.05, -0.1), (-0.05, -0.1)]
    p.poly(mouth, "fill")
    p.line(mouth, 0.9, closed=True)
    for x in (-0.035, -0.012, 0.012, 0.035):
        p.line([(x, -0.07), (x, -0.08)], 0.6, "ink", 220)
    knife = [(-0.03, -0.09), (0.03, -0.09), (0.02, -0.17), (0.0, -0.24), (-0.02, -0.17)]
    p.poly(knife, "accent", 200, occlude=False)
    p.line(knife, 0.9, closed=True)
    p.dot(0.0, -0.13, 0.9, "fill", 255)
    p.glow(0, 0, 0.32, int(160 + 80 * wave(t, 2)))


@one("sunstone", "The Sun Stone", "Mesoamerican Mysteries", "Obsidian Sun",
     "The great stone of the Fifth Sun, Nahui Ollin: the face of Tonatiuh at its heart with the four past worlds about him, the twenty day-signs in their ring, and two fire serpents carrying the sun across the sky")
def sunstone(p, t, v):
    fine_rays(p, (0, 0), 64, 1.36, 2.3, 130, t, w=0.03)
    p.glow(0, 0, 1.5, 110, "light")
    p.disc(0, 0, 1.4, "fill")
    p.poly(p.circle_pts(0, 0, 1.4)[:-1], "ink", 24, occlude=False)
    for side in (1, -1):  # Xiuhcoatl, the fire serpents: tails at the top, heads meeting below
        arc = [polar(1.24, 90 - side * (10 + 152 * k / 80)) for k in range(81)]  # tail at the top, head end at 162°
        ws = [lerp(0.07, 0.15, (k / 80) ** 0.7) for k in range(81)]
        band = thick(arc, ws)
        p.poly(band, "fill")
        p.poly(band, "ink", 70, occlude=False)
        p.line(band, 1.4, closed=True)
        nm = _normals(arc)
        for k in range(3, 80, 4):  # body segments and flame tufts
            (x, y), n_ = arc[k], nm[k]
            w = ws[k] / 2
            p.line([(x + n_[2] * w, y + n_[3] * w), (x - n_[2] * w, y - n_[3] * w)], 0.9, "ink", 220)
            out = 1 if (x * n_[2] + y * n_[3]) > 0 else -1
            b = (x + n_[2] * w * out, y + n_[3] * w * out)
            h = 0.055 + 0.02 * math.sin(TAU * (2 * t + k * 0.1))
            p.poly([(b[0] - n_[0] * 0.022, b[1] - n_[1] * 0.022), (b[0] + n_[2] * h * out + n_[0] * 0.01, b[1] + n_[3] * h * out + n_[1] * 0.01),
                    (b[0] + n_[0] * 0.022, b[1] + n_[1] * 0.022)], "accent", 210, occlude=False)
            p.dot(x + n_[0] * 0.03, y + n_[1] * 0.03, 1.0, "accent", 200)
    cart = [(-0.13, 1.14), (0.13, 1.14), (0.13, 1.4), (-0.13, 1.4)]  # the date 13 Reed
    p.poly(cart, "fill")
    p.line(cart, 1.6, closed=True)
    with p.tf(dy=1.3):
        day_sign(p, 12, 0.14)
    for j in range(13):
        p.dot(-0.11 + j * 0.0183, 1.18, 1.0, "accent", 255)
    for r, w_ in ((1.1, 1.6), (1.38, 1.4), (1.41, 2.4)):
        p.circle(0, 0, r, w_)
    with p.tf(rot=-45 * t):  # the band of feathers and the solar rays (all 45°-periodic, so the turn is seamless)
        for i in range(64):
            a = 5.625 * i
            p.line([polar(1.0, a), polar(1.08, a + 2)], 0.7, "ink", 170)
        for i in range(16):
            a = 22.5 * i
            big = i % 2 == 0
            gild(p, [polar(0.74, a - (8 if big else 4.5)), polar(1.08 if big else 0.96, a), polar(0.74, a + (8 if big else 4.5))], 100 if big else 70, 1.3)
            p.line([polar(0.77, a), polar(1.0 if big else 0.9, a)], 0.6, "ink", 170)
            if big:
                p.poly([polar(0.78, a - 4), polar(0.9, a), polar(0.78, a + 4)], "accent", 120, occlude=False)
        p.circle(0, 0, 0.74, 1.6)
        for i in range(40):  # quincunx band
            a = 9 * i
            for dd in ((0, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                p.dot(*polar(0.69 + dd[0] * 0.013, a + dd[1] * 1.7), 0.9, "ink", 210)
    for side in (1, -1):  # the fire serpents' heads, facing each other, a god's face in each mouth
        org = polar(1.24, 90 - side * 162)
        with p.tf(dx=org[0] + side * 0.03, dy=org[1] + 0.01, sx=side, s=1.0):
            upper = [(0.02, 0.1), (0.02, 0.16), (-0.12, 0.17), (-0.22, 0.14), (-0.28, 0.17), (-0.3, 0.24), (-0.25, 0.27),
                     (-0.33, 0.25), (-0.36, 0.15), (-0.32, 0.08), (-0.2, 0.06), (-0.08, 0.05)]
            lower = [(0.02, -0.1), (-0.1, -0.11), (-0.24, -0.09), (-0.29, -0.04), (-0.2, -0.05), (-0.08, -0.03)]
            gild(p, upper, 100, 1.3)
            gild(p, lower, 100, 1.3)
            for j, (x, y) in enumerate(((-0.12, 0.13), (-0.17, 0.125), (-0.22, 0.11))):  # stars on the snout
                p.circle(x, y, 0.014, 0.6, "ink", 230)
                p.dot(x, y, 0.8, "accent", 255)
            p.arc(-0.28, 0.2, 0.035, -60, 200, 0.9, "ink", 230)  # the curled nose
            for x in (-0.27, -0.21):  # fangs
                p.poly([(x - 0.012, 0.065), (x + 0.012, 0.065), (x, 0.03)], "ink", 240, occlude=False)
                p.poly([(x - 0.01, -0.045), (x + 0.01, -0.045), (x + 0.005, -0.015)], "ink", 240, occlude=False)
            p.disc(-0.06, 0.11, 0.022, "fill")
            p.disc(-0.06, 0.11, 0.022, "accent", 255, occlude=False)
            p.arc(-0.06, 0.11, 0.04, 20, 160, 0.9, "ink", 230)
            fc = (-0.16, 0.01)  # the face in profile, looking out of the jaws
            prof = [(fc[0] + 0.03, fc[1] + 0.05), (fc[0] - 0.02, fc[1] + 0.05), (fc[0] - 0.045, fc[1] + 0.02), (fc[0] - 0.06, fc[1] + 0.0),
                    (fc[0] - 0.04, fc[1] - 0.01), (fc[0] - 0.045, fc[1] - 0.03), (fc[0] - 0.02, fc[1] - 0.045), (fc[0] + 0.03, fc[1] - 0.045)]
            gild(p, prof, 140, 1.0)
            p.dot(fc[0] - 0.02, fc[1] + 0.02, 1.1, "fill", 255)
            p.circle(fc[0] + 0.02, fc[1] + 0.0, 0.018, 0.7, "ink", 230)  # ear spool
            p.glow(*fc, 0.09, int(120 + 70 * wave(t, 2)))
    p.circle(0, 0, 0.645, 1.2)  # the twenty day-signs, read counter-clockwise from the top
    p.circle(0, 0, 0.47, 1.2)
    for i in range(20):
        a = 90 + 18 * i
        c = polar(0.557, a)
        lit = max(0.0, 1 - min((t * 20 - i) % 20, (i - t * 20) % 20) / 1.5)
        with p.tf(dx=c[0], dy=c[1], rot=a - 90):
            box = [(-0.058, -0.068), (0.058, -0.068), (0.058, 0.068), (-0.058, 0.068)]
            p.poly(box, "fill")
            p.line(box, 0.8, "ink", 220, closed=True)
            day_sign(p, i, 0.1)
        if lit > 0:
            p.glow(*c, 0.08, int(200 * lit))
    p.disc(0, 0, 0.45, "fill")  # Nahui Ollin: the four past suns in the arms of Movement
    p.poly(p.circle_pts(0, 0, 0.45)[:-1], "ink", 30, occlude=False)
    suns = {45: 13, 135: 1, 225: 18, 315: 8}  # Jaguar, Wind, Rain of fire, Water
    for i in range(4):
        a = 45 + 90 * i
        gild(p, [polar(0.13, a - 25), polar(0.43, a - 12), polar(0.45, a), polar(0.43, a + 12), polar(0.13, a + 25)], 90, 1.4)
        c = polar(0.31, a)
        with p.tf(dx=c[0], dy=c[1], rot=a - 90):
            box = [(-0.07, -0.07), (0.07, -0.07), (0.07, 0.07), (-0.07, 0.07)]
            p.poly(box, "fill")
            p.line(box, 0.9, closed=True)
            day_sign(p, suns[a], 0.11)
            for j in range(4):
                p.dot(-0.045 + 0.03 * j, -0.095, 1.2, "accent", 255)
    for sg in (1, -1):  # the clawed hands clutching hearts
        hc = (sg * 0.3, 0.0)
        p.disc(hc[0] + sg * 0.03, hc[1], 0.035, "accent", 190, occlude=False)
        p.circle(hc[0] + sg * 0.03, hc[1], 0.035, 0.8)
        for k in range(3):
            claw = bezier((hc[0] - sg * 0.06, hc[1] + 0.05 - k * 0.05), (hc[0] + sg * 0.04, hc[1] + 0.06 - k * 0.05), (hc[0] + sg * 0.06, hc[1] + 0.02 - k * 0.05), 8)
            p.poly(thick(claw, [lerp(0.025, 0.004, j / 8) for j in range(9)]), "ink", 230, occlude=False)
    p.disc(0, 0, 0.19, "fill")
    p.circle(0, 0, 0.19, 1.6)
    tonatiuh(p, t)
    for a, k in ((90, 17), (270, 18)):  # 1 Flint above the face, 1 Rain below
        c = polar(0.335, a)
        box = [(c[0] - 0.05, c[1] - 0.05), (c[0] + 0.05, c[1] - 0.05), (c[0] + 0.05, c[1] + 0.05), (c[0] - 0.05, c[1] + 0.05)]
        p.poly(box, "fill")
        p.line(box, 0.8, closed=True)
        with p.tf(dx=c[0], dy=c[1]):
            day_sign(p, k, 0.08)
    hierophant_frame(p, t, "THE SUN STONE")
