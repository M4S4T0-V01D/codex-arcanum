"""The Seven Hierophants: hand-composed one-of-one plates.

Each fills the whole plate (no rolled halo, ring, frame or motto), uses its
own palette, and sits inside the ornate Hierophant frame. They are
registered as sigils with weight 0, so they are never rolled; traits.py
places them at fixed token ids.
"""
import math

from .layers import _units
from .pen import TAU, bezier, bezier3, lerp, ngon, polar, thick, wave
from .sigils import SIGILS, _normals, eye, lotus_petal, serpent_run, sigil, snake_head_top

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


def hierophant_frame(p, t, title):
    e1, e2, e3 = _units(p, 0.474), _units(p, 0.456), _units(p, 0.44)
    sq = lambda e: [(-e, -e), (e, -e), (e, e), (-e, e)]  # noqa: E731
    p.line(sq(e1), 1.4, "ink", 230, closed=True)
    p.line(sq(e2), 3.0, "ink", 255, closed=True)
    p.line(sq(e3), 0.8, "ink", 170, closed=True)
    for i in range(60):  # a beaded border between the rules
        f = i / 60
        for (x0, y0), (x1, y1) in zip(sq((e1 + e2) / 2), sq((e1 + e2) / 2)[1:] + sq((e1 + e2) / 2)[:1]):
            p.dot(lerp(x0, x1, f), lerp(y0, y1, f), 0.9, "ink", 190)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        c = (sx * e2, sy * e2)
        p.disc(*c, 0.11, "fill")
        p.circle(*c, 0.11, 2.0)
        p.circle(*c, 0.085, 0.8, "ink", 180)
        for j in range(12):
            p.line([polar(0.03, 30 * j, *c), polar(0.075 if j % 2 else 0.06, 30 * j, *c)], 0.8, "ink", 220)
        p.sparkle(*c, 0.09, int(150 + 105 * wave(t, 1, k / 4)), rot=45)
    for sx, sy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        if sy:
            continue
        c = (sx * e2, 0)
        dia = [(c[0], 0.09), (c[0] + 0.05, 0), (c[0], -0.09), (c[0] - 0.05, 0)]
        p.poly(dia, "fill")
        p.line(dia, 1.4, closed=True)
    # title cartouche (top) and edition line (bottom)
    w, y = 0.62, e2
    cart = [(-w, y - 0.06), (w, y - 0.06), (w + 0.05, y), (w, y + 0.06), (-w, y + 0.06), (-w - 0.05, y)]
    p.poly(cart, "fill")
    p.line(cart, 1.4, closed=True)
    p.text(title, 0, y, 12, "serif", "ink", 255, upright=True)
    cart2 = [(x, -yy) for x, yy in cart]
    p.poly(cart2, "fill")
    p.line(cart2, 1.4, closed=True)
    p.text("HIEROPHANT · ONE OF ONE", 0, -y, 10, "serif", "accent", 255, upright=True)


def feather(p, root, a, L, wmax, barbs=True, flame=0.0, t=0.0):
    path = bezier(root, polar(L * 0.55, a - 5, *root), polar(L, a, *root), 22)
    ws = [wmax * math.sin(math.pi * min(1.0, 0.08 + 0.92 * (i / 22) ** 0.9)) ** 0.6 * (1 - 0.15 * i / 22) + 0.002 for i in range(23)]
    f = thick(path, ws)
    p.poly(f, "fill")
    p.poly(f, "ink", 50, occlude=False)
    p.line(f, 1.1, closed=True)
    p.line(path[2:-2], 0.8, "ink", 210)
    if barbs:
        for j in range(3, 20, 3):
            (x0, y0), (x1, y1) = path[j], path[j + 1]
            dl = math.hypot(x1 - x0, y1 - y0) or 1
            tx, ty = (x1 - x0) / dl, (y1 - y0) / dl
            for sg in (1, -1):
                w = ws[j] * 0.45
                p.line([(x0, y0), (x0 - ty * sg * w + tx * w * 0.9, y0 + tx * sg * w + ty * w * 0.9)], 0.5, "ink", 140)
    if flame:
        tip = path[-1]
        h = flame * (0.7 + 0.3 * math.sin(TAU * (t * 3 + L * 7)))
        p.ray(*tip, a, 0.0, h, wmax * 0.9, 0.0, 230, "flare", steps=8)
    return path


# ---------------------------------------------------------------------------
@one("ra", "The Eye of Ra", "Egyptian Mysteries", "Solar Lapis",
     "The burning Eye of Ra: the sun-disc winged by Horus of Behdet and girded by twin uraei, its rays falling as hands that offer life, above a wall of the sacred writing")
def ra(p, t, v):
    # a wall of hieroglyphs, read top to bottom by a passing light
    scan = 1.85 - 3.7 * t
    for ci, x in enumerate([-1.56 + 0.16 * i for i in range(20)]):
        p.line([(x - 0.08, 1.65), (x - 0.08, -1.65)], 0.5, "ink", 45)
        for ri, y in enumerate([1.52 - 0.165 * j for j in range(19)]):
            ch = HIERO[(ci * 7 + ri * 13 + ci * ri) % len(HIERO)]
            p.text(ch, x, y, 13, "hiero", "ink", 62, upright=True)
            lit = math.exp(-((y - scan) / 0.22) ** 2)
            if lit > 0.06:
                p.text(ch, x, y, 13, "hiero", "accent", int(150 * lit), upright=True)
    sun = (0, 0.32)
    for i in range(36):  # the sun's rays
        long = i % 2 == 0
        p.ray(*sun, 90 + 10 * i, 0.4, (2.3 if long else 1.7) + 0.12 * wave(t, 2, i * 0.3), 0.03, 0.2 if long else 0.1,
              int(70 + 70 * wave(t, 1, -i / 36)))
    for i in range(9):  # the Aten's hands: rays ending in ankhs
        a = 235 + i * 8.75
        end = polar(1.45, a, *sun)
        p.ray(*sun, a, 0.45, 1.4, 0.02, 0.07, 200)
        p.line([polar(0.46, a, *sun), end], 0.7, "ink", 150)
        p.text("𓋹", *end, 17, "hiero", "ink", 240, upright=True)
    flap = 4 * math.sin(TAU * t)
    for side in (1, -1):  # the wings of Behdety
        with p.tf(dx=side * 0.3, dy=sun[1] + 0.02, sx=side):
            for k in range(9):  # primaries
                feather(p, (0.0, 0.0), 8 - k * 4.2 + flap * (1 - k * 0.08), 1.35 - k * 0.07, 0.085)
            for k in range(8):  # secondaries
                feather(p, (0.02, -0.02), 2 - k * 3.6 + flap * 0.6, 0.8 - k * 0.04, 0.08, barbs=False)
            for k in range(7):  # coverts
                feather(p, (0.0, 0.03), 12 - k * 5 + flap * 0.4, 0.42 - k * 0.025, 0.075, barbs=False)
            p.arc(0.0, -0.05, 0.5, -15 + flap * 0.4, 25 + flap * 0.4, 1.4, "ink", 210)
    for side in (1, -1):  # twin uraei, rearing, hooded
        body = bezier3((side * 0.36, sun[1] - 0.2), (side * 0.55, sun[1] - 0.45), (side * 0.38, sun[1] - 0.72), (side * 0.5, sun[1] - 0.92), 40)
        serpent_run(p, body, [lerp(0.09, 0.03, i / 40) for i in range(41)], flow=-2 * t)
        hc = (side * 0.48, sun[1] - 0.12)
        hood = [polar(r, a, *hc) for a, r in ((90, 0.16), (60, 0.15), (30, 0.12), (0, 0.1), (-40, 0.11), (-90, 0.14), (-140, 0.11), (180, 0.1), (150, 0.12), (120, 0.15))]
        p.poly(hood, "fill")
        p.poly(hood, "ink", 60, occlude=False)
        p.line(hood + [hood[0]], 1.6)
        for j in range(4):
            p.arc(hc[0], hc[1] - 0.02, 0.05 + j * 0.022, 200, 340, 0.6, "ink", 170)
        p.disc(hc[0], hc[1] + 0.05, 0.04, "fill")
        p.circle(hc[0], hc[1] + 0.05, 0.04, 1.2)
        for sg in (1, -1):
            p.disc(hc[0] + sg * 0.018, hc[1] + 0.06, 0.009, "accent", 255, occlude=False)
    # the disc, and the Eye within it
    p.glow(*sun, 0.85, 170, "light")
    p.disc(*sun, 0.42, "fill")
    p.poly(p.circle_pts(*sun, 0.42)[:-1], "ink", 70, occlude=False)
    for r, w_, vv in ((0.42, 3.0, 255), (0.39, 0.8, 200), (0.34, 1.6, 230), (0.12, 0.8, 160)):
        p.circle(*sun, r, w_, "ink", vv)
    for i in range(48):
        p.line([polar(0.35, 7.5 * i + 7.5 * t, *sun), polar(0.385, 7.5 * i + 7.5 * t, *sun)], 0.8, "ink", 210)
    with p.tf(dx=sun[0], dy=sun[1] - 0.02, sx=-0.33, sy=0.33):
        up = bezier3((-0.6, 0.05), (-0.3, 0.36), (0.25, 0.33), (0.58, 0.03), 40)
        lo = bezier3((-0.6, 0.05), (-0.25, -0.18), (0.25, -0.16), (0.58, 0.03), 40)
        p.poly(up + lo[::-1], "fill")
        p.disc(0.02 * math.sin(TAU * t), 0.07, 0.15, "accent", 235, occlude=False)
        p.disc(0.02 * math.sin(TAU * t), 0.07, 0.06, "fill", 255, occlude=False)
        p.line(up, 4.0)
        p.line(lo, 3.6)
        p.poly(thick(bezier((0.5, 0.05), (0.76, 0.1), (0.98, 0.04), 20), [lerp(0.07, 0.035, i / 20) for i in range(21)]), "ink")
        p.poly(thick(bezier3((-0.8, 0.42), (-0.3, 0.66), (0.35, 0.66), (0.84, 0.44), 40), [lerp(0.11, 0.06, i / 40) for i in range(41)]), "ink")
        p.poly(thick(bezier((-0.08, -0.14), (-0.1, -0.4), (-0.18, -0.7), 20), [lerp(0.07, 0.045, i / 20) for i in range(21)]), "ink")
        spiral = bezier3((0.12, -0.13), (0.14, -0.4), (0.27, -0.46), (0.40, -0.46), 20) + \
            [polar(lerp(0.16, 0.035, i / 50), 90 - 450 * i / 50, 0.4, -0.62) for i in range(1, 51)]
        p.poly(thick(spiral, [lerp(0.055, 0.025, i / len(spiral)) for i in range(len(spiral))]), "ink")
    p.glow(*sun, 0.2, int(180 + 75 * wave(t, 2)))
    # an offering frieze along the foot
    p.line([(-1.5, -1.12), (1.5, -1.12)], 1.4)
    for i, ch in enumerate("𓋹𓊽𓌀𓋹𓇳𓋹𓌀𓊽𓋹"):
        x = -1.2 + 0.3 * i
        p.text(ch, x, -1.28, 30, "hiero", "ink", 245, upright=True)
        p.glow(x, -1.28, 0.12, int(70 + 70 * wave(t, 1, i / 9)))
    hierophant_frame(p, t, "THE EYE OF RA")


# ---------------------------------------------------------------------------
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


@one("tablet", "The Emerald Tablet", "Hermeticism", "Smaragdine",
     "The Tabula Smaragdina itself, found in the hands of Hermes in his tomb: every word of the Great Work cut into a single emerald")
def tablet(p, t, v):
    c = (0, 0.05)
    for i in range(32):
        long = i % 2 == 0
        p.ray(*c, 90 + 11.25 * i, 0.5, (2.2 if long else 1.6) + 0.1 * wave(t, 2, i * 0.4), 0.05, 0.28 if long else 0.14,
              int(110 + 100 * wave(t, 1, -i / 32)))
    hw, top, bot = 0.95, 0.3, -1.18
    shape = [(-hw, bot)] + p.circle_pts(0, top, hw, 180, 0, 60) + [(hw, bot)]
    p.glow(*c, 1.5, 120, "light")
    p.poly(shape, "fill")
    p.poly(shape, "accent", 60, occlude=False)
    # crystal facets
    for (x0, y0), (x1, y1) in (((-hw, bot), (-0.2, 0.1)), ((hw, bot), (0.25, -0.2)), ((-hw, 0.2), (0.1, 0.9)), ((hw, 0.3), (-0.3, -0.6)),
                               ((-0.4, bot), (0.2, -0.4)), ((0.5, 0.9), (0.72, -0.1))):
        p.line([(x0, y0), (x1, y1)], 0.8, "accent", 70)
    p.glow(0, 0.0, 0.9, int(25 + 20 * wave(t, 1)))
    for k, (d, w_, layer, vv) in enumerate(((0.0, 3.2, "ink", 255), (0.045, 1.0, "ink", 170), (0.075, 0.8, "accent", 160))):
        inner = [(-hw + d, bot + d)] + p.circle_pts(0, top, hw - d, 180, 0, 60) + [(hw - d, bot + d)]
        p.line(inner, w_, layer, vv, closed=True)
    # title along the arch, sun and moon beside it
    title = "TABVLA · SMARAGDINA"
    for i, ch in enumerate(title):
        a = 160 - 140 * i / (len(title) - 1)
        if ch != " ":
            p.text(ch, *polar(hw - 0.15, a, 0, top), 12, "serif", "ink", 240, angle=a - 90)
    p.text("☉", -0.6, 0.5, 22, "symbols", "ink", 255, upright=True)
    p.text("☽", 0.6, 0.5, 22, "symbols", "accent", 255, upright=True)
    p.glow(-0.6, 0.5, 0.12, 160)
    p.glow(0.6, 0.5, 0.12, 120)
    # the inscription, lit line by line
    lit_line = t * (len(TABULA) + 3) - 1.5
    for i, line in enumerate(TABULA):
        y = 0.24 - i * 0.108
        p.text(line, 0, y, 8.6, "serif", "ink", 240, upright=True)
        lit = math.exp(-((i - lit_line) / 0.8) ** 2)
        if lit > 0.05:
            p.text(line, 0, y, 8.6, "serif", "accent", int(200 * lit), upright=True)
    p.line([(-0.5, -1.06), (0.5, -1.06)], 0.8, "ink", 200)
    p.text("HERMES TRISMEGISTVS", 0, bot - 0.13, 13, "serif", "ink", 245, upright=True)
    for i in range(14):  # motes rising past the tablet
        u = (t + i / 14) % 1
        x = lerp(-1.2, 1.2, (i * 0.618) % 1) + 0.05 * math.sin(TAU * (u + i * 0.3))
        p.sparkle(x, lerp(-1.3, 1.4, u), 0.035, int(220 * math.sin(math.pi * u)), rot=45)
    hierophant_frame(p, t, "THE EMERALD TABLET")


# ---------------------------------------------------------------------------
GAYATRI = "ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात् ।"


@one("aum", "AUM, the Pranava", "Vedic Mysteries", "Saffron Night",
     "The sacred syllable from which the Vedas say the worlds were sounded into being, enthroned on the lotus and ringed by the Gayatri and a mala of one hundred and eight beads")
def aum(p, t, v):
    c = (0, 0.12)
    for i in range(48):
        long = i % 2 == 0
        p.ray(*c, 90 + 7.5 * i, 0.5, (2.0 if long else 1.5) + 0.1 * wave(t, 2, i * 0.3), 0.03, 0.2 if long else 0.1,
              int(110 + 90 * wave(t, 1, -i / 48)))
    p.glow(*c, 1.2, 150, "light")
    for i in range(32):
        p.line(lotus_petal(0.95, 1.2, 90 + 11.25 * i + 11.25 * t, 5.2), 1.0, "ink", 210)
    for i in range(16):
        petal = lotus_petal(0.72, 0.95, 90 + 22.5 * i - 22.5 * t + 11.25, 10.5)
        p.poly(petal, "fill")
        p.poly(petal, "accent", 40, occlude=False)
        p.line(petal, 1.2)
    for r, w_ in ((0.72, 1.4), (1.21, 1.0), (1.24, 0.6)):
        p.circle(0, 0, r, w_, "ink", 210)
    for i in range(108):  # the mala
        a = 90 + i * 360 / 108 + 360 / 108 * t
        p.dot(*polar(1.3, a), 2.4 if i % 27 == 0 else 1.5, "ink" if i % 27 else "accent", 255)
    words = GAYATRI.split()
    for i, w in enumerate(words):
        a = 90 - 360 * (i + 0.5) / len(words)
        p.text(w, *polar(1.44, a), 13, "deva", "ink", 235, angle=a - 90)
    # the lotus throne
    for row, (n, r, h, y0, vv) in enumerate(((7, 0.17, 0.42, -0.86, 40), (5, 0.17, 0.5, -0.9, 70))):
        for i in range(n):
            x = (i - (n - 1) / 2) * (0.24 if row == 0 else 0.26)
            lean = x * 0.35
            base_y = y0 - 0.05 * (x / 0.6) ** 2
            tip = (x + lean, base_y + h - 0.12 * abs(x))
            petal = bezier3((x - r * 0.75, base_y), (x - r, base_y + h * 0.45), (tip[0] - r * 0.25, tip[1] - h * 0.25), tip, 14) + \
                bezier3(tip, (tip[0] + r * 0.25, tip[1] - h * 0.25), (x + r, base_y + h * 0.45), (x + r * 0.75, base_y), 14)[1:]
            p.poly(petal, "fill")
            p.poly(petal, "accent", vv, occlude=False)
            p.line(petal, 1.3)
            p.line(bezier((x, base_y + 0.02), (x + lean * 0.5, base_y + h * 0.5), tip, 10)[:-2], 0.6, "ink", 170)
    # the syllable
    p.text("ॐ", c[0], c[1] + 0.02, 300, "deva", "flare", int(70 + 40 * wave(t, 2)), upright=True)
    p.text("ॐ", *c, 290, "deva", "ink", 255, upright=True)
    p.sparkle(0.2, 0.86, 0.2, int(200 + 55 * wave(t, 2)), rot=45 * t)
    hierophant_frame(p, t, "AUM · THE PRANAVA")


# ---------------------------------------------------------------------------
def _rot(v, ax, ay, az):
    x, y, z = v
    for a, (i, j) in ((ax, (1, 2)), (ay, (0, 2)), (az, (0, 1))):
        c, s = math.cos(a), math.sin(a)
        w = [x, y, z]
        w[i], w[j] = c * w[i] - s * w[j], s * w[i] + c * w[j]
        x, y, z = w
    return x, y, z


@one("ophanim", "The Ophanim", "Merkabah Mysticism", "Seraph Fire",
     "The wheels within wheels that Ezekiel saw beside the living creatures by the river Chebar: their rims were high and dreadful, and full of eyes round about")
def ophanim(p, t, v):
    for i in range(16):
        p.ray(0, 0, 90 + 22.5 * i + 22.5 * t, 0.3, 2.3, 0.05, 0.3, int(110 + 80 * wave(t, 1, -i / 16)))
    flap = 5 * math.sin(TAU * t)
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):  # seraph wings behind the wheels
        with p.tf(sx=sx, sy=sy):
            for k in range(6):
                feather(p, (0.1, 0.1), 52 - k * 7.5 + flap * (1 - k * 0.08), 1.32 - k * 0.07, 0.13)
            for k in range(5):
                feather(p, (0.1, 0.1), 47 - k * 8 + flap * 0.6, 0.7 - k * 0.04, 0.12, barbs=False)
    rings = [(1.0, lambda u: (0.0, TAU * u, 0.3)), (0.82, lambda u: (TAU * u, 0.5, 0.0)), (0.64, lambda u: (0.9, -TAU * u, TAU * u))]
    segs, eyes = [], []
    for ri, (R, rot) in enumerate(rings):
        ax, ay, az = rot(t)
        for side in (-0.045, 0.045):
            pts = [_rot((math.cos(a) * (R + side), math.sin(a) * (R + side), 0.0), ax, ay, az) for a in (TAU * k / 140 for k in range(141))]
            for k in range(140):
                segs.append(((pts[k][2] + pts[k + 1][2]) / 2, pts[k], pts[k + 1]))
        for k in range(12):
            a = TAU * k / 12
            q = _rot((math.cos(a) * R, math.sin(a) * R, 0.0), ax, ay, az)
            q2 = _rot((math.cos(a + 0.05) * R, math.sin(a + 0.05) * R, 0.0), ax, ay, az)
            eyes.append((q[2], q, math.degrees(math.atan2(q2[1] - q[1], q2[0] - q[0])), ri * 12 + k))
    segs.sort(key=lambda s: s[0])
    for z, a, b in segs:
        k = (z + 1.1) / 2.2
        p.line([a[:2], b[:2]], lerp(0.8, 3.0, k), "ink", int(lerp(70, 255, k)))
    for z, q, ang, idx in sorted(eyes):
        if z < -0.15:
            continue
        k = (z + 1) / 2
        blink = max(0.0, 1 - abs(((t * 3 + idx * 0.37) % 1) - 0.5) / 0.04)
        with p.tf(dx=q[0], dy=q[1], rot=ang, s=0.5 + 0.5 * k):
            eye(p, 0, 0, 0.16, 0.08, t, blink, (0, 0), 1.1, lashes=False)
    # the burning centre
    p.glow(0, 0, 0.7, 255, "light")
    for i in range(14):
        a = 90 + i * 360 / 14
        h = 0.18 + 0.07 * math.sin(TAU * (3 * t + i * 0.3))
        p.ray(0, 0, a + 6 * math.sin(TAU * (t + i * 0.2)), 0.1, 0.1 + h * 1.5, 0.08, 0.0, 230, "flare", steps=8)
    p.sparkle(0, 0, 0.32, 255, rot=30 * t)
    p.glow(0, 0, 0.2, 255)
    for i in range(3):  # Holy, holy, holy
        a = 245 + 25 * i
        p.text("קדוש", *polar(1.42, a), 17, "hebrew", "accent", 240, angle=a + 90)
        if i < 2:
            p.sparkle(*polar(1.42, a + 12.5), 0.04, 220)
    hierophant_frame(p, t, "THE OPHANIM")


# ---------------------------------------------------------------------------
def _tree(rng_seed, root, up, depth, length, width, spread, t, sway, out):
    import random
    rng = random.Random(rng_seed)

    def grow(x, y, ang, L, w, d, path_id):
        a = ang + sway * math.sin(TAU * t + d * 0.7 + path_id * 0.13) * (depth - d + 1) / depth
        ex, ey = x + L * math.cos(math.radians(a)), y + L * math.sin(math.radians(a))
        out["branches"].append(((x, y), (ex, ey), w, w * 0.68, d))
        if d == 0:
            out["tips"].append((ex, ey))
            return
        kids = 3 if rng.random() < 0.35 else 2
        for k in range(kids):
            off = (k - (kids - 1) / 2) * spread * (1.25 if kids == 2 else 1) + rng.uniform(-8, 8)
            grow(ex, ey, a + off, L * rng.uniform(0.66, 0.8), w * 0.68, d - 1, path_id * 3 + k)

    grow(root[0], root[1], up, length, width, depth, 1)


@one("yggdrasil", "Yggdrasil, the World Tree", "Norse Mysteries", "World Ash",
     "The ash that holds the nine worlds in its branches and roots, where Odin hung nine nights to win the runes, with the serpent of Midgard coiled about its waist")
def yggdrasil(p, t, v):
    for k in range(3):  # aurora
        base = 1.0 + 0.15 * k
        pts = [(x, base + 0.12 * math.sin(TAU * (t + x * 0.5 + k * 0.3)) + 0.05 * math.sin(TAU * (2 * t + x * 1.3)))
               for x in [lerp(-1.6, 1.6, i / 60) for i in range(61)]]
        p.poly(thick(pts, [0.14 * (0.6 + 0.4 * math.sin(math.pi * i / 60)) for i in range(61)]), "light", int(45 + 25 * wave(t, 1, k / 3)), occlude=False)
    crown = {"branches": [], "tips": []}
    roots = {"branches": [], "tips": []}
    _tree(331, (0, 0.05), 90, 6, 0.36, 0.09, 40, t, 2.5, crown)
    _tree(332, (0, -0.32), 270, 5, 0.3, 0.085, 44, t, 1.2, roots)
    trunk = [(-0.11, -0.4), (0.11, -0.4), (0.07, 0.1), (-0.07, 0.1)]
    for tree in (roots, crown):
        for (x0, y0), (x1, y1), w0, w1, d in sorted(tree["branches"], key=lambda b: -b[4]):
            seg = thick([(x0, y0), (x1, y1)], [w0, w1])
            p.poly(seg, "fill")
            p.poly(seg, "ink", 120 + 15 * (6 - d), occlude=False)
        for i, (x, y) in enumerate(tree["tips"]):
            p.dot(x, y, 1.6, "accent", int(160 + 95 * wave(t, 1, i * 0.37)))
            if i % 5 == 0:
                p.glow(x, y, 0.08, int(120 * wave(t, 1, i * 0.21)))
    p.poly(trunk, "fill")
    p.poly(trunk, "ink", 170, occlude=False)
    for i in range(5):  # bark
        x = -0.07 + 0.035 * i
        p.line(bezier((x, -0.38), (x + 0.02 * math.sin(i), -0.15), (x * 0.7, 0.08), 10), 0.6, "ink", 90)
    # Jörmungandr round Midgard
    c = (0, -0.12)
    ell = [(0.62 * math.cos(a), c[1] + 0.13 * math.sin(a)) for a in (TAU * k / 160 for k in range(161))]
    dep = [-math.sin(TAU * k / 160) for k in range(161)]
    run, sgn, runs = [ell[0]], dep[0] > 0, []
    for q, d in zip(ell[1:], dep[1:]):
        run.append(q)
        if (d > 0) != sgn:
            runs.append((sgn, run)); run, sgn = [q], d > 0
    runs.append((sgn, run))
    worlds = [("Asgard", (0, 1.28)), ("Alfheim", (-0.78, 1.02)), ("Vanaheim", (0.78, 1.02)), ("Jotunheim", (-1.05, 0.25)),
              ("Muspelheim", (1.05, 0.25)), ("Midgard", c), ("Svartalfheim", (-0.72, -0.92)), ("Niflheim", (0.72, -0.92)), ("Helheim", (0, -1.32))]
    for i, (name, q) in enumerate(worlds):
        if name == "Midgard":
            for front, r in runs:
                if not front:
                    serpent_run(p, r, [0.07] * len(r), front=False)
        lit = 0.6 + 0.4 * wave(t, 1, i / 9)
        p.glow(*q, 0.22, int(200 * lit))
        p.disc(*q, 0.06, "fill")
        p.circle(*q, 0.06, 1.6)
        p.circle(*q, 0.085, 0.6, "ink", 180)
        p.text(FUTHARK[(i * 3) % len(FUTHARK)], *q, 13, "runic", "accent", 255, upright=True)
        if name == "Midgard":
            for front, r in runs:
                if front:
                    serpent_run(p, r, [0.07] * len(r), flow=-4 * t)
            snake_head_top(p, *ell[2], 160, 0.07, t)
    for i, ch in enumerate(FUTHARK * 2):  # ring of runes
        a = 90 - 360 * i / 48
        p.text(ch, *polar(1.5, a), 13, "runic", "ink", 200, angle=a - 90)
    p.circle(0, 0, 1.42, 0.8, "ink", 170)
    p.circle(0, 0, 1.58, 0.8, "ink", 170)
    hierophant_frame(p, t, "YGGDRASIL")


# ---------------------------------------------------------------------------
@one("phoenix", "The Phoenix", "Alchemy & Egypt", "Phoenix Flame",
     "The Bennu, the bird of Heliopolis, that burns upon its nest of spices and rises again from its own ashes: the alchemists' sign of the reddened Stone")
def phoenix(p, t, v):
    sun = (0, 0.55)
    for i in range(36):
        long = i % 2 == 0
        p.ray(*sun, 90 + 10 * i, 0.35, (2.0 if long else 1.4) + 0.1 * wave(t, 2, i * 0.3), 0.04, 0.24 if long else 0.12,
              int(120 + 100 * wave(t, 1, -i / 36)))
    p.glow(*sun, 0.75, 220, "light")
    p.circle(*sun, 0.48, 1.2, "ink", 170)
    flap = 7 * math.sin(TAU * t)
    for side in (1, -1):  # the wings, raised, flame-tipped
        with p.tf(dx=side * 0.1, dy=0.2, sx=side):
            for k in range(10):
                feather(p, (0.0, 0.0), 78 - k * 7.5 + flap * (1 - k * 0.05), 1.3 - k * 0.045, 0.09, flame=0.22, t=t + k * 0.1)
            for k in range(8):
                feather(p, (0.0, -0.02), 60 - k * 7 + flap * 0.6, 0.72 - k * 0.03, 0.085, barbs=False)
            for k in range(6):
                feather(p, (0.0, 0.0), 70 - k * 9 + flap * 0.4, 0.36 - k * 0.02, 0.08, barbs=False)
    for k in range(7):  # the tail: plumes with burning eyes
        a = 270 + (k - 3) * 15 + 3 * math.sin(TAU * (t + k * 0.13))
        L = 0.62 + 0.12 * (1 - abs(k - 3) / 3)
        path = feather(p, (0.0, -0.3), a, L, 0.08, flame=0.18, t=t + k * 0.2)
        q = path[-4]
        p.disc(*q, 0.05, "fill")
        p.circle(*q, 0.05, 1.2)
        p.disc(*q, 0.026, "accent", 240, occlude=False)
        p.glow(*q, 0.1, int(150 + 80 * wave(t, 2, k / 7)))
    body = [(0.0, 0.42), (0.13, 0.3), (0.16, 0.05), (0.1, -0.25), (0.0, -0.36), (-0.1, -0.25), (-0.16, 0.05), (-0.13, 0.3)]
    p.poly(body, "fill")
    p.poly(body, "ink", 70, occlude=False)
    p.line(body, 1.6, closed=True)
    for r in range(5):  # breast feathers
        for k in range(5 - r % 2):
            x = (k - (4 - r % 2) / 2) * 0.05
            p.arc(x, 0.22 - r * 0.1, 0.03, 200, 340, 0.6, "ink", 170)
    neck = bezier3((0.0, 0.38), (0.05, 0.5), (0.02, 0.62), (0.06, 0.7), 20)
    p.poly(thick(neck, [lerp(0.13, 0.08, i / 20) for i in range(21)]), "fill")
    p.poly(thick(neck, [lerp(0.13, 0.08, i / 20) for i in range(21)]), "ink", 70, occlude=False)
    head = [(0.0, 0.66), (0.05, 0.76), (0.12, 0.77), (0.18, 0.73), (0.26, 0.7), (0.19, 0.67), (0.22, 0.62), (0.13, 0.64), (0.06, 0.62)]
    p.poly(head, "fill")
    p.poly(head, "ink", 80, occlude=False)
    p.line(head + [head[0]], 1.5)
    for k in range(5):  # the crest
        cr = bezier((0.04, 0.75), (-0.02 - k * 0.03, 0.86 + k * 0.02), (-0.12 - k * 0.05, 0.84 + k * 0.05 + 0.02 * math.sin(TAU * (t + k * 0.2))), 12)
        p.poly(thick(cr, [lerp(0.03, 0.004, i / 12) for i in range(13)]), "ink", 230, occlude=False)
        p.dot(*cr[-1], 2.0, "accent", 255)
    p.disc(0.12, 0.715, 0.018, "accent", 255, occlude=False)
    p.glow(0.12, 0.715, 0.07, 230)
    for i in range(9):  # the burning nest
        x = -0.5 + 0.125 * i
        for layer, sc, vv in (("accent", 1.0, 190), ("flare", 0.55, 240)):
            h = (0.35 + 0.12 * math.sin(TAU * (2 * t + i * 0.37)) + 0.06 * math.sin(TAU * (3 * t + i * 0.71))) * sc * (1.2 if 2 < i < 6 else 0.8)
            sway = 0.05 * math.sin(TAU * (t + i * 0.2)) * sc
            w = 0.07 * sc
            tip = (x + sway * 1.4, -1.0 + h)
            fl = bezier3((x - w, -1.0), (x - w * 1.2, -1.0 + h * 0.35), (x + sway - w * 0.4, -1.0 + h * 0.7), tip, 12) + \
                bezier3(tip, (x + sway + w * 0.7, -1.0 + h * 0.6), (x + w * 1.1, -1.0 + h * 0.3), (x + w, -1.0), 12)[1:]
            p.poly(fl, layer, vv, occlude=False)
        u = (t * 2 + i * 0.29) % 1
        p.sparkle(x + 0.06 * math.sin(TAU * (u + i)), -0.95 + 0.9 * u, 0.03, int(230 * math.sin(math.pi * u)))
    nest = [(-0.62, -1.0), (0.62, -1.0), (0.48, -1.14), (-0.48, -1.14)]
    p.poly(nest, "fill")
    p.line(nest, 1.6, closed=True)
    for k in range(9):
        p.line([(-0.6 + k * 0.15, -1.02), (-0.5 + k * 0.13, -1.12)], 0.8, "ink", 180)
    hierophant_frame(p, t, "THE PHOENIX")


# ---------------------------------------------------------------------------
def _day_sign(p, k, c, s):
    """Twenty small engraved glyphs for the day-sign cartouches."""
    x, y = c
    k %= 20
    if k == 0: p.circle(x, y, s * 0.5, 0.9); p.dot(x, y, 1.6, "accent")
    elif k == 1: p.line([(x - s * 0.5, y), (x + s * 0.5, y)], 0.9); p.line([(x, y - s * 0.5), (x, y + s * 0.5)], 0.9)
    elif k == 2: p.line(ngon(3, s * 0.55, 90, x, y), 0.9, closed=True)
    elif k == 3: p.line([polar(s * 0.12 * (1 + j / 4), 90 + j * 60, x, y) for j in range(18)], 0.9)
    elif k == 4: p.line([(x - s * 0.5 + s * j / 4, y + (s * 0.3 if j % 2 else -s * 0.3)) for j in range(5)], 0.9)
    elif k == 5: [p.circle(*polar(s * 0.3, 90 * j, x, y), s * 0.18, 0.8) for j in range(4)]
    elif k == 6: p.line(ngon(4, s * 0.5, 45, x, y), 0.9, closed=True); p.dot(x, y, 1.4, "accent")
    elif k == 7: p.arc(x, y - s * 0.1, s * 0.45, 0, 180, 0.9); p.line([(x - s * 0.45, y - s * 0.1), (x + s * 0.45, y - s * 0.1)], 0.9)
    elif k == 8: [p.dot(*polar(s * 0.35, 72 * j + 90, x, y), 1.4, "ink") for j in range(5)]; p.dot(x, y, 1.6, "accent")
    elif k == 9: p.line([(x - s * 0.4, y - s * 0.4), (x + s * 0.4, y + s * 0.4)], 0.9); p.line([(x - s * 0.4, y + s * 0.4), (x + s * 0.4, y - s * 0.4)], 0.9)
    elif k == 10: p.circle(x, y, s * 0.45, 0.9); p.circle(x, y, s * 0.2, 0.9)
    elif k == 11: p.line(ngon(3, s * 0.55, 270, x, y), 0.9, closed=True)
    elif k == 12: p.line([(x - s * 0.5, y - s * 0.2), (x, y + s * 0.4), (x + s * 0.5, y - s * 0.2)], 0.9)
    elif k == 13: [p.line([(x - s * 0.45, y + s * (j - 1) * 0.3), (x + s * 0.45, y + s * (j - 1) * 0.3)], 0.8) for j in range(3)]
    elif k == 14: p.line(ngon(6, s * 0.5, 90, x, y), 0.9, closed=True)
    elif k == 15: p.arc(x - s * 0.2, y, s * 0.3, -90, 90, 0.9); p.arc(x + s * 0.2, y, s * 0.3, 90, 270, 0.9)
    elif k == 16: p.line([(x, y + s * 0.5), (x, y - s * 0.5)], 0.9); [p.line([(x, y + s * (0.3 - j * 0.25)), (x + s * 0.35 * (1 if j % 2 else -1), y + s * (0.45 - j * 0.25))], 0.8) for j in range(4)]
    elif k == 17: p.line(ngon(5, s * 0.5, 90, x, y), 0.9, closed=True)
    elif k == 18: p.circle(x, y + s * 0.15, s * 0.3, 0.9); p.line([(x - s * 0.4, y - s * 0.35), (x + s * 0.4, y - s * 0.35)], 0.9)
    else: p.line([polar(s * 0.5, 90 + 144 * j, x, y) for j in range(6)], 0.9)


@one("sunstone", "The Sun Stone", "Mesoamerican Mysteries", "Obsidian Sun",
     "The great stone of the Fifth Sun, Nahui Ollin: the four past worlds at its heart, the twenty day-signs in their ring, and two fire serpents carrying the sun across the sky")
def sunstone(p, t, v):
    for i in range(24):
        p.ray(0, 0, 90 + 15 * i, 1.35, 2.4, 0.04, 0.16, int(60 + 60 * wave(t, 1, -i / 24)))
    p.glow(0, 0, 1.45, 120, "light")
    p.disc(0, 0, 1.4, "fill")
    p.poly(p.circle_pts(0, 0, 1.4)[:-1], "ink", 26, occlude=False)
    # outer ring: two fire serpents meeting below
    for side in (1, -1):
        arc = [polar(1.24, 90 + side * (8 + 164 * k / 80)) for k in range(81)]
        serpent_run(p, arc, [lerp(0.06, 0.13, (k / 80) ** 0.7) for k in range(81)], flow=-4 * t)
        nm = _normals(arc)
        for k in range(4, 78, 5):  # flame tufts along the back
            (x, y), n = arc[k], nm[k]
            out = 1 if (x * n[2] + y * n[3]) > 0 else -1
            w = lerp(0.06, 0.13, (k / 80) ** 0.7) / 2
            base = (x + n[2] * w * out, y + n[3] * w * out)
            h = 0.06 + 0.02 * math.sin(TAU * (2 * t + k * 0.1))
            p.poly([(base[0] - n[0] * 0.025, base[1] - n[1] * 0.025), (base[0] + n[2] * h * out, base[1] + n[3] * h * out),
                    (base[0] + n[0] * 0.025, base[1] + n[1] * 0.025)], "accent", 200, occlude=False)
        snake_head_top(p, *arc[-1], 270 - side * 90 + side * 8, 0.13, t + (0.5 if side > 0 else 0))
    p.disc(0, 1.24, 0.1, "fill")  # the date cartouche where the tails meet
    p.line(ngon(4, 0.12, 45, 0, 1.24), 1.4, closed=True)
    for j in range(3):
        p.dot(-0.04 + j * 0.04, 1.24, 1.8, "accent")
    for r, w_ in ((1.1, 1.6), (1.36, 1.4), (1.4, 2.4)):
        p.circle(0, 0, r, w_)
    # solar rays: eight great, eight small
    with p.tf(rot=-45 * t):
        for i in range(16):
            a = 22.5 * i
            big = i % 2 == 0
            tri = [polar(0.74, a - (9 if big else 5)), polar(1.06 if big else 0.92, a), polar(0.74, a + (9 if big else 5))]
            p.poly(tri, "fill")
            p.poly(tri, "ink", 90 if big else 60, occlude=False)
            p.line(tri, 1.3, closed=True)
            p.line([polar(0.76, a), polar(0.98 if big else 0.86, a)], 0.6, "ink", 160)
        p.circle(0, 0, 0.74, 1.6)
        for i in range(40):  # quincunx band
            a = 9 * i
            for dd in ((0, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                q = polar(0.69 + dd[0] * 0.012, a + dd[1] * 1.6)
                p.dot(*q, 0.9, "ink", 200)
    # the twenty day signs
    with p.tf(rot=18 * t):
        p.circle(0, 0, 0.64, 1.2)
        p.circle(0, 0, 0.47, 1.2)
        for i in range(20):
            a = 90 - 18 * i
            c = polar(0.555, a)
            with p.tf(dx=c[0], dy=c[1], rot=a - 90):
                box = [(-0.055, -0.065), (0.055, -0.065), (0.055, 0.065), (-0.055, 0.065)]
                p.line(box, 0.8, "ink", 220, closed=True)
                _day_sign(p, i, (0, 0), 0.09)
    # Nahui Ollin: the four past suns in the arms of Movement
    p.disc(0, 0, 0.45, "fill")
    for i in range(4):
        a = 45 + 90 * i
        arm = [polar(0.12, a - 22), polar(0.42, a - 12), polar(0.44, a), polar(0.42, a + 12), polar(0.12, a + 22)]
        p.poly(arm, "fill")
        p.poly(arm, "ink", 80, occlude=False)
        p.line(arm, 1.4, closed=True)
        c = polar(0.3, a)
        p.line(ngon(4, 0.07, a + 45, *c), 0.8, "ink", 220, closed=True)
        for j in range(i + 1):
            p.dot(*polar(0.03 * (j - i / 2), a + 90, *c), 1.4, "accent")
    p.disc(0, 0, 0.13, "fill")
    p.circle(0, 0, 0.13, 1.8)
    p.glow(0, 0, 0.32, int(200 + 55 * wave(t, 2)))
    p.sparkle(0, 0, 0.16, 255, rot=22.5 * t)
    hierophant_frame(p, t, "THE SUN STONE")
