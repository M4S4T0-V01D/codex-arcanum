"""Everything around the central figure: halo (behind), glyph ring, frame and
motto (in front)."""
import math

from .pen import TAU, UNIT, font, lerp, polar, wave

# ---- halos ----------------------------------------------------------------


def halo_rays(p, t):
    n = 36
    for i in range(n):
        a = 90 + i * 360 / n
        long = i % 2 == 0
        L = (1.8 if long else 1.35) + 0.12 * wave(t, 2, i * 0.41)
        p.ray(0, 0, a, 0.25, L, 0.03, 0.15 if long else 0.08, int(110 + 90 * wave(t, 1, -i / n)))
    p.glow(0, 0, 1.0, 110, "light")


def halo_emanation(p, t):
    n = 7
    for k in range(n):
        u = (k + t) / n
        r = 0.3 + u * 1.45
        p.circle(0, 0, r, 1.6, "faint", int(255 * math.sin(math.pi * u)))


def halo_lattice(p, t):
    r = 0.26
    with p.tf(rot=60 * t):
        for i in range(-8, 9):
            for j in range(-8, 9):
                x = r * (i + j * 0.5)
                y = r * j * math.sqrt(3) / 2
                d = math.hypot(x, y)
                if d < 2.3:
                    p.circle(x, y, r, 1.0, "faint", int(200 * max(0.25, 1 - d / 2.6)))


def halo_nimbus(p, t):
    b = 0.6 + 0.4 * wave(t, 1)
    p.glow(0, 0, 1.35, int(70 * b), "light", steps=16)


def halo_spheres(p, t):
    for r, rev, ph in ((1.08, 1, 0.1), (1.42, -1, 0.6), (1.6, 2, 0.35)):
        p.circle(0, 0, r, 1.0, "faint", 220)
        a = 90 + 360 * (rev * t + ph)
        p.dot(*polar(r, a), 3.0, "accent", 230)
        p.sparkle(*polar(r, a), 0.09, 220, rot=a)
        p.dot(*polar(r, a + 180), 2.0, "ink", 200)


HALOS = {
    "None": (24, None),
    "Rays of Glory": (20, halo_rays),
    "Emanation": (16, halo_emanation),
    "Sacred Lattice": (12, halo_lattice),
    "Nimbus": (16, halo_nimbus),
    "Celestial Spheres": (12, halo_spheres),
}

# ---- glyph rings ----------------------------------------------------------

RINGS = {
    "None": dict(weight=22),
    "Zodiac": dict(weight=10, key="symbols", items=list("♈♉♊♋♌♍♎♏♐♑♒♓"), size=17),
    "Planetary Metals": dict(weight=10, key="symbols", items=list("☉☽☿♀♂♃♄"), size=19),
    "Alchemical Elements": dict(weight=8, key="symbols", items=list("🜂🜄🜁🜃🜍☿🜔"), size=19),
    "Elder Futhark": dict(weight=7, key="runic", items=list("ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"), size=16),
    "Hebrew Alphabet": dict(weight=8, key="hebrew", items=list("אבגדהוזחטיכלמנסעפצקרשת"), size=15),
    "Greek Alphabet": dict(weight=8, key="serif_text", items=list("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"), size=14),
    "Ogham": dict(weight=4, key="ogham", items=list("ᚁᚂᚃᚄᚅᚆᚇᚈᚉᚊᚋᚌᚍᚎᚏᚐᚑᚒᚓᚔ"), size=16),
    "Hieroglyphs": dict(weight=6, key="hiero", items=list("𓋹𓂀𓆣𓊽𓌀𓇳𓋴𓅓𓆓𓃭𓊹𓇯"), size=19),
    "Bagua": dict(weight=4, key="symbols2", items=list("☰☴☵☶☷☳☲☱"), size=18),
    "Om Mani Padme Hum": dict(weight=4, key="deva", items=["ॐ", "मणि", "पद्मे", "हूँ"] * 2, size=15),
    "Emerald Tablet": dict(weight=5, key="serif", text="QVOD EST INFERIVS EST SICVT QVOD EST SVPERIVS ✦ ", size=12),
    "VITRIOL": dict(weight=3, key="serif", text="VISITA INTERIORA TERRAE RECTIFICANDO INVENIES OCCVLTVM LAPIDEM ✦ ", size=11),
}
RING_R = 1.22


def draw_ring(p, name, t):
    spec = RINGS[name]
    if name == "None":
        return
    R = RING_R
    p.circle(0, 0, R + 0.1, 1.4, "ink", 220)
    p.circle(0, 0, R - 0.1, 1.4, "ink", 220)
    # graduated scale just outside the ring, as on an engraved astrolabe limb
    p.circle(0, 0, R + 0.16, 0.6, "ink", 150)
    for i in range(180):
        a = i * 2
        L = 0.05 if i % 15 == 0 else (0.035 if i % 5 == 0 else 0.02)
        p.line([polar(R + 0.16, a), polar(R + 0.16 - L, a)], 0.6 if i % 5 else 0.9, "ink", 170)
    if "text" in spec:
        text = spec["text"].replace("✦", "·")
        f = font(spec["key"], int(spec["size"] * p.ss * p.k))
        widths = [f.getlength(c) for c in text]
        total = sum(widths)
        a = 90.0
        n = len(text)
        h = t * n
        for i, (c, w) in enumerate(zip(text, widths)):
            da = 360.0 * w / total
            ac = a - da / 2
            a -= da
            if c == " ":
                continue
            d = min((h - i) % n, (i - h) % n)
            lit = max(0.0, 1 - d / 4)
            p.text(c, *polar(R, ac), spec["size"], spec["key"], "ink", 220, angle=ac - 90)
            if lit > 0:
                p.text(c, *polar(R, ac), spec["size"], spec["key"], "accent", int(255 * lit), angle=ac - 90)
        return
    items = spec["items"]
    n = len(items)
    h = t * n
    for i, c in enumerate(items):
        a = 90 - 360 * i / n
        d = min((h - i) % n, (i - h) % n)
        lit = max(0.0, 1 - d / 1.3)
        p.text(c, *polar(R, a), spec["size"], spec["key"], "ink", 225, angle=a - 90)
        if lit > 0:
            p.text(c, *polar(R, a), spec["size"], spec["key"], "accent", int(255 * lit), angle=a - 90)
        p.dot(*polar(R, a - 180 / n), 1.3, "ink", 200)


# ---- frames ---------------------------------------------------------------

def _units(p, px_frac):
    """Canvas fraction (from centre) -> unit coords."""
    return px_frac / UNIT


def frame_folio(p, t, token):
    e1, e2 = _units(p, 0.468), _units(p, 0.445)
    sq = lambda e: [(-e, -e), (e, -e), (e, e), (-e, e)]  # noqa: E731
    p.line(sq(e1), 1.2, "ink", 220, closed=True)
    p.line(sq(e2), 2.4, "ink", 255, closed=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx * e2, sy * e2)
            d = 0.07
            dia = [(c[0], c[1] + d), (c[0] + d, c[1]), (c[0], c[1] - d), (c[0] - d, c[1])]
            p.poly(dia, "fill")
            p.line(dia, 1.4, closed=True)
            p.dot(*c, 1.8, "accent", 230)
    p.text(f"PLATE {token['roman']}", 0, _units(p, 0.415), 11, "serif", "ink", 235, upright=True)


def frame_seal(p, t, token):
    r1, r2 = _units(p, 0.47), _units(p, 0.445)
    p.circle(0, 0, r1, 1.4, "ink", 220)
    p.circle(0, 0, r2, 2.4, "ink", 255)
    n = 60
    for i in range(n):
        p.dot(*polar((r1 + r2) / 2, 90 + 360 * i / n + 6 * t), 1.2, "ink", 200)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx * _units(p, 0.44), sy * _units(p, 0.44))
            p.text("✦", *c, 14, "symbols2", "ink", 200, upright=True)


def frame_cartouche(p, t, token):
    w, h, rr = _units(p, 0.41), _units(p, 0.455), _units(p, 0.3)
    for k, (d, lw, vv) in enumerate(((0.0, 2.6, 255), (0.05, 1.2, 200))):
        ww, hh, r = w - d, h - d, rr - d
        pts = []
        for cx, cy, a0 in ((ww - r, hh - r, 0), (-ww + r, hh - r, 90), (-ww + r, -hh + r, 180), (ww - r, -hh + r, 270)):
            pts += p.circle_pts(cx, cy, r, a0, a0 + 90, 24)
        p.line(pts, lw, "ink", vv, closed=True)
    by = -h - 0.04
    p.line([(-w * 0.6, by), (w * 0.6, by)], 3.0)


def frame_arch(p, t, token):
    hw = _units(p, 0.43)
    top = _units(p, 0.468)
    sill = -_units(p, 0.455)
    spring = top - hw * 1.2  # springing line low enough that rho > half-width => pointed apex
    # arc radius chosen so the two arcs meet exactly at `top`
    for k, (d, lw, vv) in enumerate(((0.0, 2.6, 255), (0.06, 1.2, 200))):
        w_ = hw - d
        tp = top - d
        rho = ((tp - spring) ** 2 + w_ ** 2) / (2 * w_)
        cxr = w_ - rho
        a_end = math.degrees(math.atan2(tp - spring, -cxr))
        right = p.circle_pts(cxr, spring, rho, 0, a_end, 60)
        left = [(-x, y) for x, y in right[::-1]]
        pts = [(w_, sill + d)] + right + left + [(-w_, sill + d)]
        p.line(pts, lw, "ink", vv, closed=True)
    p.line([(-hw - 0.05, sill - 0.03), (hw + 0.05, sill - 0.03)], 2.4)
    p.dot(0, top + 0.035, 2.4, "accent", 230)


FRAMES = {
    "Folio Plate": (30, frame_folio),
    "Seal": (22, frame_seal),
    "Cartouche": (12, frame_cartouche),
    "Lancet Arch": (14, frame_arch),
    "Bare": (22, None),
}

# ---- mottos ---------------------------------------------------------------

MOTTOS = {
    "None": (40, None),
    "SOLVE ET COAGULA": (8, "Dissolve and coagulate"),
    "QVOD EST SVPERIVS EST SICVT QVOD INFERIVS": (6, "That which is above is as that which is below"),
    "ΕΝ ΤΟ ΠΑΝ": (4, "One is the All"),
    "V · I · T · R · I · O · L": (5, "Visit the interior of the earth; by rectifying you will find the hidden stone"),
    "IGNE NATVRA RENOVATVR INTEGRA": (4, "By fire, nature is renewed whole"),
    "ORDO AB CHAO": (6, "Order out of chaos"),
    "LVX E TENEBRIS": (6, "Light out of darkness"),
    "NOSCE TE IPSVM": (6, "Know thyself"),
    "ΓΝΩΘΙ ΣΕΑΥΤΟΝ": (4, "Know thyself (the Delphic maxim)"),
    "OBSCVRVM PER OBSCVRIVS": (4, "The obscure by the more obscure"),
    "OMNIA AB VNO": (5, "All things from the One"),
    "ORA LEGE LEGE LEGE RELEGE LABORA ET INVENIES": (3, "Pray, read, read, read, reread, work, and you will find (Mutus Liber)"),
    "SCIRE · AVDERE · VELLE · TACERE": (4, "To know, to dare, to will, to keep silent"),
    "PER IGNEM AD LVCEM": (5, "Through fire to light"),
    "AZOTH": (3, "The universal medicine: A to Z, Alpha to Omega"),
    "MEMENTO MORI": (4, "Remember that you must die"),
}


def draw_motto(p, text, t):
    if not text:
        return
    key = "serif_text" if any("Ͱ" <= c <= "Ͽ" for c in text) else "serif"
    R, max_span = 1.47, 96.0
    r_px = R * UNIT * p.size
    for size in (12, 11, 10, 9):
        f = font(key, int(size * p.ss * p.k))
        widths = [f.getlength(c) / p.ss for c in text]
        span = math.degrees(sum(widths) / r_px)
        if span <= max_span:
            break
    a = 270 - span / 2
    for c, w in zip(text, widths):
        da = math.degrees(w / r_px)
        ac = a + da / 2
        a += da
        if c != " ":
            p.text(c, *polar(R, ac), size, key, "ink", 240, angle=ac + 90)


# ---- degree seal ----------------------------------------------------------

def draw_degree(p, level, t):
    """A small seal at the lower right: one point of light per degree (1-5).
    The Hierophant's seal also burns."""
    c = (_units(p, 0.405), -_units(p, 0.405))
    r = 0.085
    p.disc(*c, r, "fill")
    p.circle(*c, r, 1.2, "ink", 230)
    p.circle(*c, r * 0.78, 0.6, "ink", 170)
    for i in range(level):
        a = 90 - 360 * i / level if level > 1 else 90
        q = polar(r * 0.45, a, *c) if level > 1 else c
        p.dot(*q, 1.7, "accent", 255)
    if level >= 4:
        p.glow(*c, r * 2.2, int(120 + 80 * wave(t, 1)) if level == 5 else 90)
    if level == 5:
        p.sparkle(*c, r * 2.0, int(170 + 85 * wave(t, 2)), rot=45 * t)
