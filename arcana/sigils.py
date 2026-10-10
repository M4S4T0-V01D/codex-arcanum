"""The central figures. Each one draws itself at loop phase t in [0, 1) and
must be seamless (state at t=1 == state at t=0): rotations are multiples
of the figure's symmetry angle, oscillations use integer frequencies."""
import math

from .pen import (TAU, bezier, bezier3, lerp, ngon, path_point, polar, smooth,
                  sub_path, thick, wave)

SIGILS = {}


def sigil(key, name, tradition, weight, lore, variants=None, rings=()):
    def deco(fn):
        SIGILS[key] = dict(key=key, name=name, tradition=tradition, weight=weight,
                           lore=lore, variants=variants or [], rings=rings, fn=fn)
        return fn
    return deco


def blink_at(t, centre=0.66, width=0.045):
    return max(0.0, 1.0 - abs(t - centre) / width)


def eye(p, cx, cy, w, h, t, blink=0.0, look=(0.0, 0.0), lw=2.2, lashes=True):
    """An all-seeing eye: calligraphic lids with kohl wings, crease, waterline,
    curled lashes and a jewelled iris (striations, collarette, limbal ring,
    breathing pupil, catchlights). `blink` 0..1 closes it."""
    o = max(0.04, 1.0 - blink)
    n = 64
    us = [i / n for i in range(n + 1)]
    px = 1 / 148.5 * lw  # one "line width" in unit coords
    up_y = lambda u: h / 2 * math.sin(math.pi * u) ** 0.8 * o  # noqa: E731
    lo_y = lambda u: -h / 2 * 0.8 * math.sin(math.pi * u) ** 1.15 * o  # noqa: E731
    X = lambda u: cx + w * (u - 0.5)  # noqa: E731
    up = [(X(u), cy + up_y(u)) for u in us]
    lo = [(X(u), cy + lo_y(u)) for u in us]
    p.poly(up + lo[::-1], "fill")
    # tear duct
    p.disc(X(0.045), cy - h * 0.02 * o, h * 0.06 * max(o, 0.3), "accent", 90, occlude=False)
    if o > 0.12:
        ir = h * 0.42
        ix, iy = cx + look[0] * w * 0.12, cy + look[1] * h * 0.06 + h * 0.03
        with p.clip(up + lo[::-1]), p.tf(dx=ix, dy=iy):
            p.disc(0, 0, ir, "fill")
            p.glow(0, 0, ir * 1.5, int(120 + 60 * wave(t, 2)))
            for k in range(48):  # striations
                a = k * 7.5 + 4 * math.sin(TAU * t)
                r1 = ir * (0.84 if k % 3 == 0 else 0.7 if k % 3 == 1 else 0.6)
                p.line([polar(ir * 0.4, a), polar(r1, a)], 0.55, "ink", 150 if k % 3 else 200)
            coll = [polar(ir * (0.56 + 0.05 * math.sin(math.radians(d) * 12)), d) for d in range(0, 360, 4)]
            p.line(coll, 0.8, "accent", 190, closed=True)
            p.circle(0, 0, ir, lw * 1.1, "accent", 240)
            p.circle(0, 0, ir * 0.9, 0.6, "ink", 170)
            pr = ir * (0.3 + 0.05 * wave(t, 1, 0.25))
            p.disc(0, 0, pr, "fill")
            p.circle(0, 0, pr, 0.9, "ink", 230)
            p.dot(-ir * 0.32, ir * 0.34, 2.0, "accent", 255)
            p.dot(ir * 0.24, -ir * 0.22, 1.0, "accent", 210)
            p.sparkle(-ir * 0.32, ir * 0.34, ir * 0.45, 190)
    # calligraphic lids: thick in the middle, hair-thin at the corners
    p.poly(thick(up, [px * (0.6 + 2.6 * math.sin(math.pi * u) ** 0.7) for u in us]), "ink", occlude=False)
    p.poly(thick(lo, [px * (0.4 + 1.3 * math.sin(math.pi * u)) for u in us]), "ink", occlude=False)
    # waterline and crease
    p.line([(X(u), cy + lo_y(u) * 0.78) for u in us[10:-10]], 0.6, "accent", 120)
    crease = [(X(u), cy + up_y(u) * (1.25 + 0.15 * o) + h * 0.12) for u in us[8:-8]]
    p.poly(thick(crease, [px * 0.9 * math.sin(math.pi * (i / (len(crease) - 1))) + 0.001 for i in range(len(crease))]), "ink", 210, occlude=False)
    # kohl wings sweeping off both corners
    ow = bezier3((X(1) - w * 0.02, cy), (X(1) + w * 0.08, cy + h * 0.02), (X(1) + w * 0.15, cy + h * 0.12), (X(1) + w * 0.2, cy + h * 0.3), 24)
    p.poly(thick(ow, [px * 2.2 * (1 - i / 24) ** 0.8 + 0.0005 for i in range(25)]), "ink", occlude=False)
    iw = bezier3((X(0) + w * 0.02, cy), (X(0) - w * 0.05, cy - h * 0.02), (X(0) - w * 0.08, cy - h * 0.12), (X(0) - w * 0.06, cy - h * 0.24), 18)
    p.poly(thick(iw, [px * 1.6 * (1 - i / 18) ** 0.8 + 0.0005 for i in range(19)]), "ink", occlude=False)
    if lashes:
        for j in range(9):
            u = 0.14 + 0.72 * j / 8
            bx, by = X(u), cy + up_y(u)
            L = h * (0.2 + 0.16 * math.sin(math.pi * u)) * (0.4 + 0.6 * o)
            lean = (u - 0.5) * 1.3
            tip = (bx + lean * L + w * 0.03, by + L * (0.4 + 0.6 * o))
            ctrl = (bx + lean * L * 0.05, by + L * 0.95)
            lash = bezier((bx, by), ctrl, tip, 12)
            p.poly(thick(lash, [px * 0.85 * (1 - i / 12) ** 0.7 + 0.0003 for i in range(13)]), "ink", 230, occlude=False)


def crescent(p, cx, cy, r, facing, depth=0.55, layer="ink"):
    """Crescent moon whose horns point toward `facing` (degrees)."""
    tip_a = 50.0
    t1 = polar(r, facing + tip_a, cx, cy)
    t2 = polar(r, facing - tip_a, cx, cy)
    outer = p.circle_pts(cx, cy, r, facing + tip_a, facing + 360 - tip_a, 60)
    icx, icy = polar(r * depth, facing, cx, cy)
    a1 = math.degrees(math.atan2(t2[1] - icy, t2[0] - icx))
    a0 = math.degrees(math.atan2(t1[1] - icy, t1[0] - icx))
    while a0 <= a1:
        a0 += 360
    ri = math.dist(t1, (icx, icy))
    inner = p.circle_pts(icx, icy, ri, a1, a0 - 360 if a0 - a1 > 360 else a0, 60)
    # inner arc must run through the back side, opposite `facing`
    mid = inner[len(inner) // 2]
    if math.dist(mid, polar(r, facing, cx, cy)) < math.dist(mid, polar(r, facing + 180, cx, cy)):
        inner = p.circle_pts(icx, icy, ri, a1, a0 - 360, 60)
    p.poly(outer + inner[::-1], layer)


def project(v, ry, rx, rz=0.0):
    x, y, z = v
    c, s = math.cos(ry), math.sin(ry)
    x, z = c * x + s * z, -s * x + c * z
    c, s = math.cos(rx), math.sin(rx)
    y, z = c * y - s * z, s * y + c * z
    c, s = math.cos(rz), math.sin(rz)
    x, y = c * x - s * y, s * x + c * y
    k = 1.0 / (1.0 - z * 0.12)
    return (x * k, y * k, z)


def edges_by_length(verts):
    d = [math.dist(a, b) for i, a in enumerate(verts) for b in verts[i + 1:]]
    m = min(d)
    return [(i, j) for i in range(len(verts)) for j in range(i + 1, len(verts))
            if abs(math.dist(verts[i], verts[j]) - m) < 1e-6]


def wireframe(p, verts, edges, ry, rx, rz, scale, lw=2.2):
    pts = [project(v, ry, rx, rz) for v in verts]
    order = sorted(edges, key=lambda e: pts[e[0]][2] + pts[e[1]][2])
    for i, j in order:
        z = (pts[i][2] + pts[j][2]) / 2
        k = (z + 1) / 2
        p.line([(pts[i][0] * scale, pts[i][1] * scale), (pts[j][0] * scale, pts[j][1] * scale)],
               lerp(1.0, lw, k), "ink", int(lerp(90, 255, k)))
    for i, j in order:
        z = (pts[i][2] + pts[j][2]) / 2
        if z > 0:
            p.line([(pts[i][0] * scale, pts[i][1] * scale), (pts[j][0] * scale, pts[j][1] * scale)], 5.0, "flare", int(110 * z))
    for x, y, z in pts:
        if z > -0.2:
            p.dot(x * scale, y * scale, lerp(1.2, 2.8, (z + 1) / 2), "accent", int(lerp(120, 255, (z + 1) / 2)))
        if z > 0.2:
            p.sparkle(x * scale, y * scale, 0.07 * scale / 0.5 * z, int(220 * z), rot=45)


def lotus_petal(r0, r1, a, half):
    """Pointed petal from radius r0 to tip r1 at angle a (deg), base half-angle."""
    b1, b2 = polar(r0, a - half), polar(r0, a + half)
    tip = polar(r1, a)
    m1, m2 = polar(lerp(r0, r1, 0.65), a - half * 1.15), polar(lerp(r0, r1, 0.65), a + half * 1.15)
    return bezier(b1, m1, tip, 12) + bezier(tip, m2, b2, 12)[1:]


def helix_runs(points, depths):
    """Split a path into front (depth>0) / back runs."""
    runs, cur, sign = [], [points[0]], depths[0] > 0
    for pt, d in zip(points[1:], depths[1:]):
        cur.append(pt)
        if (d > 0) != sign:
            runs.append((sign, cur))
            cur, sign = [pt], d > 0
    runs.append((sign, cur))
    return runs


def _normals(pts):
    out = []
    for i in range(len(pts)):
        x0, y0 = pts[max(0, i - 1)]
        x1, y1 = pts[min(len(pts) - 1, i + 1)]
        L = math.hypot(x1 - x0, y1 - y0) or 1.0
        out.append(((x1 - x0) / L, (y1 - y0) / L, -(y1 - y0) / L, (x1 - x0) / L))  # tangent, normal
    return out


def serpent_run(p, pts, widths, lw=1.8, front=True, flow=0.0):
    """One stretch of serpent body: shaded, scaled and glossy (front) or
    dimmed (behind). `flow` scrolls the scales (in scale lengths)."""
    poly = thick(pts, widths)
    p.poly(poly, "fill")
    p.poly(poly, "ink", 22 if front else 12, occlude=False)
    if front and len(pts) > 2:
        nm = _normals(pts)
        p.poly(thick(pts, [w * 0.7 for w in widths]), "ink", 30, occlude=False)
        back = [(x + n[2] * w * 0.12, y + n[3] * w * 0.12) for (x, y), n, w in zip(pts, nm, widths)]
        p.poly(thick(back, [w * 0.38 for w in widths]), "ink", 48, occlude=False)
        seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        total, wmean = sum(seg), sum(widths) / len(widths)
        step = max(1e-3, wmean * 0.3)
        d, acc, i, k = (flow % 1.0) * step, 0.0, 0, 0
        while d < total:
            while i < len(seg) - 1 and acc + seg[i] < d:
                acc += seg[i]; i += 1
            f = (d - acc) / (seg[i] or 1)
            x = lerp(pts[i][0], pts[i + 1][0], f); y = lerp(pts[i][1], pts[i + 1][1], f)
            w = lerp(widths[i], widths[i + 1], f)
            tx, ty, nx, ny = nm[i]
            rs = w * 0.13
            off = 0.11 if k % 2 else -0.11
            for r in (-0.62, -0.2, 0.22, 0.64):  # fractions of the half-width
                cx, cy = x + nx * w * 0.5 * (r + off), y + ny * w * 0.5 * (r + off)
                arc = [(cx + nx * rs * math.sin(q) - tx * rs * 0.9 * math.cos(q), cy + ny * rs * math.sin(q) - ty * rs * 0.9 * math.cos(q))
                       for q in (math.radians(a) for a in range(-90, 91, 30))]
                p.line(arc, 0.6, "ink", 165)
            d += step; k += 1
        p.line([(x + n[2] * w * 0.3, y + n[3] * w * 0.3) for (x, y), n, w in zip(pts, nm, widths)][1:-1], 1.6, "flare", 80)
    n = len(pts)
    p.line(poly[:n], lw)
    p.line(poly[n:], lw)
    if front and n > 2:  # where the body turns away, round it like a bending tube
        for end, prev in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            r = widths[0 if end is pts[0] else -1] / 2
            if r < 0.01:
                continue
            ang = math.degrees(math.atan2(end[1] - prev[1], end[0] - prev[0]))
            cap = p.circle_pts(end[0], end[1], r, ang - 90, ang + 90, 16)
            p.poly(cap + [end], "fill")
            p.poly(cap + [end], "ink", 22, occlude=False)
            p.line(cap, lw)


def snake_head_top(p, x, y, ang, neck, t, lw=1.8):
    """A viper's head seen from above: a spade wider than the neck, eyes on
    both sides, crown shields, nostrils and a flicking forked tongue.
    (x, y) is where the neck joins, `ang` the way it faces, `neck` the body
    width there (unit coords); the head is scaled to suit it."""
    s = neck / 0.1
    a = math.radians(ang)
    fx, fy = math.cos(a), math.sin(a)
    L = lambda u, w: (x + (fx * u - fy * w) * s, y + (fy * u + fx * w) * s)  # noqa: E731
    deg = math.degrees(a)
    half = [(0.0, 0.05), (0.04, 0.066), (0.09, 0.098), (0.14, 0.108), (0.19, 0.1), (0.24, 0.082), (0.285, 0.058), (0.315, 0.032), (0.325, 0.0)]
    outline = [L(u, w) for u, w in half] + [L(u, -w) for u, w in half[::-1][1:]]
    flick = wave(t, 3)
    if flick > 0.3:
        tl = 0.04 + 0.11 * (flick - 0.3) / 0.7
        tip = L(0.33 + tl, 0.006 * math.sin(TAU * t * 9))
        p.line([L(0.32, 0.0), tip, L(0.33 + tl + 0.045, 0.02)], 1.1, "accent", 235)
        p.line([tip, L(0.33 + tl + 0.045, -0.02)], 1.1, "accent", 235)
    p.poly(outline, "fill")
    p.poly(outline, "ink", 30, occlude=False)
    p.poly([L(u, w * 0.55) for u, w in half] + [L(u, -w * 0.55) for u, w in half[::-1][1:]], "ink", 26, occlude=False)
    # crown shields: frontal, supraoculars, parietals, internasals
    p.poly([L(0.13, 0.026), L(0.21, 0.02), L(0.23, 0.0), L(0.21, -0.02), L(0.13, -0.026)], "ink", 70, occlude=False)
    p.line([L(0.13, 0.026), L(0.21, 0.02), L(0.23, 0.0), L(0.21, -0.02), L(0.13, -0.026), L(0.13, 0.026)], 0.8, "ink", 220)
    for sg in (1, -1):
        sup = [L(0.14, 0.034 * sg), L(0.22, 0.03 * sg), L(0.235, 0.062 * sg), L(0.16, 0.078 * sg)]
        p.poly(sup, "ink", 80, occlude=False)
        p.line(sup + [sup[0]], 0.9, "ink", 230)
        p.line([L(0.06, 0.004 * sg), L(0.13, 0.026 * sg), L(0.12, 0.07 * sg)], 0.8, "ink", 200)  # parietal
        p.line([L(0.25, 0.004 * sg), L(0.285, 0.024 * sg)], 0.7, "ink", 190)  # internasal
        p.dot(*L(0.3, 0.018 * sg), 1.0, "fill", 255)  # nostril
        ex, ey = L(0.2, 0.084 * sg)
        er = 0.017 * s
        p.disc(ex, ey, er, "fill")
        p.disc(ex, ey, er, "accent", 235, occlude=False)
        p.glow(ex, ey, er * 3.2, int(180 + 60 * wave(t, 2)))
        with p.tf(dx=ex, dy=ey, rot=deg):
            p.poly([(er * 0.85 * math.cos(q), er * 0.18 * math.sin(q)) for q in (TAU * j / 16 for j in range(16))], "fill")
        p.circle(ex, ey, er, 0.8, "ink", 230)
    for row in range(3):  # small scales over the back of the head
        for k in range(5):
            w = (k - 2) * 0.026 + (0.013 if row % 2 else 0)
            p.arc(*L(0.015 + row * 0.03, w), 0.011 * s, deg + 180 - 80, deg + 180 + 80, 0.55, "ink", 150)
    p.line(outline, lw, closed=False)


def snake_head(p, x, y, ang, size, t, lw=1.8):
    """A viper's head in profile, mouth closed, tongue flicking. (x, y) is the
    back of the head, `ang` the direction it faces (degrees)."""
    a = math.radians(ang)
    flip = -1 if math.cos(a) < 0 else 1
    L = lambda u, w: (x + (math.cos(a) * u - math.sin(a) * w * flip) * size,  # noqa: E731
                      y + (math.sin(a) * u + math.cos(a) * w * flip) * size)
    rot = math.degrees(a) + (0 if flip > 0 else 180)
    outline = ((-0.17, 0.05), (-0.09, 0.078), (0.0, 0.098), (0.08, 0.094), (0.15, 0.074), (0.21, 0.046), (0.25, 0.022), (0.27, 0.004),
               (0.255, -0.014), (0.2, -0.03), (0.12, -0.05), (0.03, -0.074), (-0.06, -0.072), (-0.17, -0.05))
    head = [L(u, w) for u, w in outline]
    flick = wave(t, 3)
    if flick > 0.35:  # forked tongue
        tl = 0.05 + 0.09 * (flick - 0.35) / 0.65
        tip = L(0.265 + tl, 0.004 * math.sin(TAU * t * 9))
        p.line([L(0.265, 0.0), tip, L(0.265 + tl + 0.035, 0.016)], 1.0, "accent", 230)
        p.line([tip, L(0.265 + tl + 0.035, -0.014)], 1.0, "accent", 230)
    p.poly(head, "fill")
    p.poly(head, "ink", 40, occlude=False)
    p.poly([L(u, w) for u, w in outline[:7]] + [L(0.2, 0.026), L(0.0, 0.036), L(-0.17, 0.018)], "ink", 30, occlude=False)
    p.line(head[1:-1], lw)
    p.line([L(0.262, 0.004), L(0.17, -0.004), L(0.06, -0.014), L(-0.02, -0.032)], 0.9, "ink", 210)  # mouth
    for k in range(6):
        p.arc(*L(0.04 + 0.034 * k, 0.008), 0.014 * size, rot + 90 - 75 * flip, rot + 90 + 75 * flip, 0.6, "ink", 160)
    for row, (w0, w1, u0, u1) in enumerate(((0.072, 0.098, -0.13, 0.05), (0.045, 0.07, -0.13, 0.0))):
        for k in range(8):
            u = lerp(u0, u1, (k + 0.5 * (row % 2)) / 8)
            p.arc(*L(u, lerp(w0, w1, (u - u0) / (u1 - u0))), 0.01 * size, rot + 180 - 80, rot + 180 + 80, 0.55, "ink", 140)
    shield = [L(0.08, 0.07), L(0.105, 0.09), L(0.15, 0.082), L(0.165, 0.064), L(0.12, 0.062)]
    p.poly(shield, "fill")
    p.poly(shield, "ink", 70, occlude=False)
    p.line(shield, 1.0, closed=True)
    stripe = [L(*q) for q in bezier((0.1, 0.04), (0.03, 0.034), (-0.06, 0.0), 12)]
    p.poly(thick(stripe, [lerp(0.016, 0.004, i / 12) * size for i in range(13)]), "ink", 90, occlude=False)
    ex, ey = L(0.126, 0.044)
    er = 0.018 * size
    p.disc(ex, ey, er, "fill")
    p.disc(ex, ey, er, "accent", 235, occlude=False)
    p.glow(ex, ey, er * 3.5, int(190 + 60 * wave(t, 2)))
    with p.tf(dx=ex, dy=ey, rot=rot - 90):
        p.poly([(er * 0.2 * math.sin(q), er * 0.9 * math.cos(q)) for q in (TAU * j / 16 for j in range(16))], "fill")
    p.circle(ex, ey, er, 0.8, "ink", 230)
    p.dot(*L(0.235, 0.022), 1.2, "fill", 255)


@sigil("providence", "The Eye of Providence", "Freemasonry", 8,
       "The all-seeing eye in the radiant delta: the Great Architect watching over the unfinished work of the world",
       variants=[("Radiant Delta", 1), ("Unfinished Pyramid", 1)],
       rings=("Emerald Tablet", "Hebrew Alphabet", "Zodiac", "Greek Alphabet"))
def providence(p, t, v):
    blink = blink_at(t)
    look = (math.sin(TAU * t), 0.5 * math.sin(TAU * 2 * t))
    if v["variant"] == "Radiant Delta":
        n = 32
        for i in range(n):
            a = 90 + i * 360 / n
            long = i % 2 == 0
            L = (1.62 if long else 1.22) + 0.14 * wave(t, 2, i * 0.37)
            v = int(255 * (0.5 + 0.5 * wave(t, 1, -i / n)))
            p.ray(0, -0.08, a, 0.3, L, 0.025, 0.15 if long else 0.08, int(v * 0.85))
        p.glow(0, -0.08, 0.75, 170, "light")
        tri = ngon(3, 1.0, 90, 0, -0.08)
        p.poly(tri, "fill")
        p.line(tri, 3.0, closed=True)
        p.line(ngon(3, 0.88, 90, 0, -0.08), 1.2, "ink", 180, closed=True)
        p.glow(0, -0.12, 0.42, int(150 + 70 * wave(t, 2)))
        eye(p, 0, -0.12, 0.74, 0.34, t, blink, look)
    else:
        top, base, hw = 0.98, -0.92, 1.05
        half = lambda y: hw * (top - y) / (top - base)  # noqa: E731
        dy = 0.035 * math.sin(TAU * t)
        cy0 = 0.12 + dy
        cap = [(-half(0.12), cy0), (half(0.12), cy0), (0, top + dy)]
        cc = (0, (cy0 * 2 + top + dy) / 3)
        for i in range(24):
            a = i * 15 + 90
            long = i % 2 == 0
            L = (1.3 if long else 0.9) + 0.12 * wave(t, 2, i * 0.31)
            p.ray(*cc, a, 0.18, L, 0.02, 0.13 if long else 0.07, int(220 * (0.5 + 0.5 * wave(t, 1, -i / 24))))
        p.glow(*cc, 0.6, 180, "light")
        y1 = -0.02
        body = [(-hw, base), (hw, base), (half(y1), y1), (-half(y1), y1)]
        p.poly(body, "fill")
        rows = 9
        for r in range(1, rows):
            y = lerp(base, y1, r / rows)
            p.line([(-half(y), y), (half(y), y)], 1.1, "ink", 190)
            y0 = lerp(base, y1, (r - 1) / rows)
            step = 0.21
            off = (r % 2) * step / 2
            x = -half(y0) + off + step
            while x < half(y0) - 0.04:
                p.line([(x, y0), (x, y)], 1.1, "ink", 160)
                x += step
        p.line(body, 2.6, closed=True)
        p.text("MDCCLXXVI", 0, base + 0.06, 10, "serif", "ink", 230)
        p.poly(cap, "fill")
        p.line(cap, 2.6, closed=True)
        p.glow(cc[0], cc[1] - 0.03, 0.26, int(150 + 70 * wave(t, 2)))
        eye(p, cc[0], cc[1] - 0.03, 0.44, 0.2, t, blink, look, 1.8, lashes=False)


@sigil("ouroboros", "The Ouroboros", "Graeco-Egyptian Alchemy", 7,
       "The serpent that devours its own tail, drawn after the Chrysopoeia of Cleopatra: ΕΝ ΤΟ ΠΑΝ, the One is the All",
       rings=("Greek Alphabet", "Planetary Metals", "Alchemical Elements", "Emerald Tablet"))
def ouroboros(p, t, v):
    R, a0, span = 0.76, 88.0, 344.0
    n = 240

    def th(s):  # slim neck, thick body, long tapering tail
        if s < 0.22:
            return 0.115 + 0.075 * math.sin(math.pi / 2 * s / 0.22)
        return 0.012 + 0.178 * (1 - (s - 0.22) / 0.78) ** 0.85

    def frame(s, off=0.0):
        """Point at body fraction s, offset `off` (in half-widths, + = outside)."""
        a = math.radians(a0 - span * s)
        ur = (math.cos(a), math.sin(a))
        ut = (math.sin(a), -math.cos(a))  # toward the tail
        r = R + off * th(s) / 2
        return (r * ur[0], r * ur[1]), ur, ut

    ss = [i / n for i in range(n + 1)]
    centre = [frame(s)[0] for s in ss]
    body = thick(centre, [th(s) for s in ss])
    p.glow(0, 0, 0.6, int(45 + 25 * wave(t, 1)), "light")
    p.poly(body, "fill")
    p.poly(body, "ink", 34, occlude=False)  # gilt wash over the whole body
    # back (outer) is lit, belly (inner) in shadow: a band of brighter gilt
    p.poly(thick([frame(s, 0.42)[0] for s in ss], [th(s) * 0.42 for s in ss]), "ink", 60, occlude=False)

    N = 132  # scales along the body; the pattern scrolls 6 scales (one diamond) per loop
    flow = 6 * t
    # diamondback pattern along the spine
    for k in range(N // 6 + 1):
        s = (k * 6 + flow) / N
        if not 0.03 < s < 0.93:
            continue
        L = 2.6 / N
        q0, q1, q2, q3 = frame(s - L, 0.18)[0], frame(s, 0.62)[0], frame(s + L, 0.18)[0], frame(s, -0.26)[0]
        p.poly([q0, q1, q2, q3], "ink", 105, occlude=False)
        p.line([q0, q1, q2, q3], 0.8, "ink", 210, closed=True)
    # overlapping scales: staggered rows of small arcs that open toward the head
    for row in range(5):
        off = -0.62 + 0.31 * row
        for i in range(N):
            s = (i + 0.5 * (row % 2) + flow) / N
            if not 0.02 < s < 0.95:
                continue
            c, ur, ut = frame(s, off)
            rs = th(s) * 0.17
            arc = [(c[0] + ur[0] * rs * math.sin(f) + ut[0] * rs * 0.9 * math.cos(f),
                    c[1] + ur[1] * rs * math.sin(f) + ut[1] * rs * 0.9 * math.cos(f))
                   for f in (math.radians(d) for d in range(-90, 91, 30))]
            p.line(arc, 0.7, "ink", 175)
    # ventral plates across the belly
    for i in range(N // 2):
        s = (i * 2 + flow) / N
        if not 0.02 < s < 0.92:
            continue
        p.line([frame(s, -0.98)[0], frame(s, -0.7)[0]], 0.8, "ink", 150)
    # glossy highlight along the back
    p.line([frame(s, 0.5)[0] for s in ss[6:int(n * 0.9)]], 2.0, "flare", 90)
    p.line(body, 2.0, closed=True)

    # the head, in profile, jaws gaping round its own tail
    ah = math.radians(95)
    hc = (R * math.cos(ah), R * math.sin(ah))
    ur = (math.cos(ah), math.sin(ah))
    ut = (-math.sin(ah), math.cos(ah))
    L = lambda u, w: (hc[0] + ut[0] * u + ur[0] * w, hc[1] + ut[1] * u + ur[1] * w)  # noqa: E731
    top = [L(-0.17, 0.058), L(-0.08, 0.094), L(0.0, 0.118), L(0.09, 0.113), L(0.17, 0.09), L(0.228, 0.06),
           L(0.262, 0.034), L(0.256, 0.016)]
    lip = [L(0.256, 0.016), L(0.17, 0.021), L(0.08, 0.017), L(0.02, 0.01), L(-0.02, 0.0)]
    jaw = [L(-0.02, 0.0), L(0.07, -0.026), L(0.15, -0.045), L(0.205, -0.06), L(0.2, -0.076)]
    chin = [L(0.2, -0.076), L(0.12, -0.094), L(0.02, -0.104), L(-0.08, -0.09), L(-0.17, -0.058)]
    head = top + lip[1:] + jaw[1:] + chin[1:]
    p.poly(head, "fill")
    p.poly(head, "ink", 40, occlude=False)
    p.poly(top + lip[1:], "ink", 30, occlude=False)  # crown catches a little more light
    for c in (top, lip, jaw, chin):
        p.line(c, 2.0)
    deg = math.degrees(ah)
    # dark mouth interior and fangs
    mouth = lip[::-1] + jaw[1:]
    p.poly(mouth, "accent", 60, occlude=False)
    for fu, fl in ((0.215, 0.05), (0.17, 0.035)):
        p.poly([L(fu - 0.014, 0.019), L(fu + 0.009, 0.019), L(fu - 0.004, 0.019 - fl)], "ink", occlude=False)
    # fine scales over the crown and under the chin
    for row, (w0, w1, u0, u1) in enumerate(((0.07, 0.1, -0.13, 0.06), (0.045, 0.07, -0.13, 0.02), (-0.06, -0.08, -0.13, 0.12))):
        for k in range(10):
            u = lerp(u0, u1, (k + 0.5 * (row % 2)) / 10)
            w = lerp(w0, w1, (u - u0) / (u1 - u0))
            p.arc(*L(u, w), 0.011, deg + 180 - 80, deg + 180 + 80, 0.6, "ink", 150)
    # cranial plates and the heavy supraocular shield over the eye
    p.line([L(0.13, 0.098), L(0.19, 0.08), L(0.24, 0.052)], 0.8, "ink", 170)
    p.line([L(0.0, 0.114), L(0.03, 0.092), L(0.0, 0.07)], 0.7, "ink", 150)
    shield = [L(0.075, 0.084), L(0.105, 0.106), L(0.15, 0.1), L(0.165, 0.082), L(0.12, 0.08)]
    p.poly(shield, "fill")
    p.poly(shield, "ink", 70, occlude=False)
    p.line(shield, 1.2, closed=True)
    # postocular stripe running back to the angle of the jaw
    stripe = bezier((0.095, 0.058), (0.03, 0.05), (-0.06, 0.012), 16)
    p.poly(thick([L(*q) for q in stripe], [lerp(0.022, 0.006, i / 16) for i in range(17)]), "ink", 120, occlude=False)
    for k in range(7):  # labial scales along the upper lip
        p.arc(*L(0.03 + 0.031 * k, 0.03), 0.015, deg + 90 - 75, deg + 90 + 75, 0.7, "ink", 170)
    # jaw line, heat pit, nostril
    p.line([L(-0.02, 0.0), L(-0.06, -0.025), L(-0.1, -0.05)], 0.9, "ink", 190)
    p.dot(*L(0.19, 0.04), 1.3, "fill", 255)
    p.dot(*L(0.238, 0.042), 1.6, "fill", 255)
    # the eye: smaller, deep-set under the shield, slit pupil
    ex, ey = L(0.122, 0.06)
    p.disc(ex, ey, 0.022, "fill")
    p.disc(ex, ey, 0.022, "accent", 235, occlude=False)
    p.glow(ex, ey, 0.075, int(200 + 55 * wave(t, 2)))
    with p.tf(dx=ex, dy=ey, rot=deg - 90):
        slit = [(0.0042 * math.sin(a_), 0.02 * math.cos(a_)) for a_ in (TAU * j / 20 for j in range(20))]
        p.poly(slit, "fill")
    p.dot(*L(0.116, 0.068), 1.0, "accent", 255)
    p.circle(ex, ey, 0.022, 0.9, "ink", 230)
    p.text("ΕΝ ΤΟ ΠΑΝ", 0, 0, 22, "serif_text", "ink", 235, upright=True)


@sigil("squared_circle", "The Squaring of the Circle", "European Alchemy", 6,
       "Make of man and woman a circle, then a square, then a triangle, then a circle, and you will have the Stone (Maier, Atalanta Fugiens, Emblem XXI)",
       rings=("Planetary Metals", "Alchemical Elements", "Zodiac"))
def squared_circle(p, t, v):
    R = 0.98
    for a in (0, 90, 45, 135):
        p.line([polar(R, a), polar(R, a + 180)], 1.0, "faint", 255)
    p.circle(0, 0, R, 2.8)
    p.circle(0, 0, R + 0.04, 1.0, "ink", 160)
    sq = ngon(4, R, 45 + 90 * t)
    p.poly(sq, "fill", 255)
    p.line(sq, 2.4, closed=True)
    r2 = R / math.sqrt(2)
    p.circle(0, 0, r2, 1.2, "ink", 170)
    tri = ngon(3, r2, 90 - 120 * t)
    p.line(tri, 2.4, closed=True)
    r3 = r2 / 2
    p.ring(0, 0, r3, 2.4)
    p.glow(0, 0, r3 * 1.1, int(70 + 40 * wave(t, 2)))
    for k, (x, y) in enumerate(sq + tri):
        p.dot(x, y, 3.2, "accent")
        p.sparkle(x, y, 0.09, int(140 + 100 * wave(t, 1, k / 7)), rot=45)
    p.text("☉", -0.12, 0.0, 22, "symbols", "ink", 255, upright=True)
    p.text("☽", 0.12, 0.0, 22, "symbols", "accent", 255, upright=True)


@sigil("monas", "The Hieroglyphic Monad", "Elizabethan Hermeticism", 5,
       "John Dee's Monas Hieroglyphica (1564): Moon, Sun, the cross of the Elements and the fire of Aries, all planets folded into one glyph",
       rings=("Planetary Metals", "Zodiac", "Emerald Tablet"))
def monas(p, t, v):
    bob = 0.03 * math.sin(TAU * t)
    p.circle(0, bob * 0.3, 1.0, 1.0, "faint", 255)
    with p.tf(dy=bob):
        arc = p.circle_pts(0, 0.82, 0.3, 192, 348, 60)
        ws = [0.015 + 0.085 * math.sin(math.pi * i / (len(arc) - 1)) for i in range(len(arc))]
        p.poly(thick(arc, ws), "ink")
        p.ring(0, 0.16, 0.27, 3.0)
        p.disc(0, 0.16, 0.05 * (1 + 0.3 * wave(t, 2)), "accent", 255, occlude=False)
        p.glow(0, 0.16, 0.2, int(150 + 80 * wave(t, 2)))
        p.line([(0, -0.11), (0, -0.80)], 3.4)
        p.line([(-0.27, -0.40), (0.27, -0.40)], 3.4)
        p.arc(-0.12, -0.80, 0.12, 0, 180, 3.0)
        p.arc(0.12, -0.80, 0.12, 0, 180, 3.0)
    for i in range(4):
        a = 45 + 90 * i
        p.dot(*polar(0.95, a + 90 * t), 2.2, "accent", 200)


SEPHIROTH = [(0, 0), (1, 1), (-1, 1), (1, 3), (-1, 3), (0, 4), (1, 5), (-1, 5), (0, 6), (0, 8)]
PATHS = [(0, 1), (0, 2), (0, 5), (1, 2), (1, 3), (1, 5), (2, 4), (2, 5), (3, 4), (3, 5), (3, 6),
         (4, 5), (4, 7), (5, 6), (5, 7), (5, 8), (6, 7), (6, 8), (6, 9), (7, 8), (7, 9), (8, 9)]


@sigil("tree_of_life", "The Tree of Life", "Kabbalah", 7,
       "The ten Sephiroth and twenty-two paths of the Otz Chiim, struck through by the Lightning Flash that descends from Kether to Malkuth",
       rings=("Hebrew Alphabet", "Zodiac", "Planetary Metals"))
def tree_of_life(p, t, v):
    pos = [(x * 0.43, 0.97 - y * 0.2425) for x, y in SEPHIROTH]
    for a, b in PATHS:
        p.line([pos[a], pos[b]], 4.2, "faint", 200)
        p.line([pos[a], pos[b]], 1.4, "ink", 200)
    p.circle(0, 0.97 - 2 * 0.2425, 0.07, 1.0, "ink", 140)  # Daath
    flash = pos[:]
    u = t / 0.8
    lens = [0.0]
    for i in range(9):
        lens.append(lens[-1] + math.dist(flash[i], flash[i + 1]))
    frac = [x / lens[-1] for x in lens]
    if u <= 1:
        p.line(sub_path(flash, max(0, u - 0.14), u, 30), 3.2, "accent", 255)
        p.line(sub_path(flash, max(0, u - 0.14), u, 30), 9.0, "flare", 200)
        p.sparkle(*path_point(flash, u), 0.12, 255, rot=45 * u)
    letters = "אבגדהוזחטי"
    for i, (x, y) in enumerate(pos):
        p.ring(x, y, 0.088, 2.2)
        lit = math.exp(-(u - frac[i]) * 9) if u >= frac[i] else 0.0
        if lit > 0.02:
            p.circle(x, y, 0.088, 3.4, "accent", int(255 * lit))
            p.glow(x, y, 0.22, int(230 * lit))
        p.text(letters[i], x, y, 13, "hebrew", "ink", 255, upright=True)


@sigil("sri_yantra", "The Sri Yantra", "Tantra", 5,
       "Nine interlocking triangles, four of Shiva and five of Shakti, radiating from the bindu: the cosmos as a diagram of union",
       rings=("Om Mani Padme Hum", "Zodiac"))
def sri_yantra(p, t, v):
    hw, gate = 0.8, 0.16
    for k, d in enumerate((0.0, 0.035, 0.07)):
        h = hw - d
        g = gate + d
        pts = []
        for side in range(4):
            rot = 90 * side
            seg = [(-h, -h), (-g, -h), (-g, -h - 0.06 + d), (g, -h - 0.06 + d), (g, -h)]
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            pts += [(c * x - s * y, s * x + c * y) for x, y in seg]
        p.line(pts, 2.0 if k == 0 else 1.2, "ink", 255 if k == 0 else 190, closed=True)
    for r in (0.74, 0.71):
        p.circle(0, 0, r, 1.4, "ink", 210)
    for i in range(16):
        p.line(lotus_petal(0.56, 0.70, i * 22.5 + 22.5 * t, 10.5), 1.5, "ink", 230)
    p.circle(0, 0, 0.555, 1.2, "ink", 200)
    for i in range(8):
        p.line(lotus_petal(0.42, 0.55, i * 45 - 45 * t + 22.5, 21), 1.6, "ink", 230)
    S = 0.41
    p.circle(0, 0, S, 1.6)
    up = [(-0.68, 1.0), (-0.46, 0.62), (-0.18, 0.46), (-0.06, 0.24)]
    down = [(0.75, -1.0), (0.44, -0.74), (0.30, -0.42), (0.12, -0.26), (0.52, 0.06)]
    allt = [(yb, ya) for yb, ya in up] + [(yb, ya) for yb, ya in down]
    for i, (yb, ya) in enumerate(allt):
        hwid = min(math.sqrt(max(0.0, 1 - yb * yb)), 0.66 * abs(ya - yb))
        tri = [(-hwid * S, yb * S), (hwid * S, yb * S), (0, ya * S)]
        p.line(tri, 1.6, "ink", 255, closed=True)
        g = wave(t, 1, i / len(allt))
        if g > 0.85:
            p.line(tri, 2.2, "accent", int(255 * (g - 0.85) / 0.15), closed=True)
    p.disc(0, 0.02, 0.022 * (1 + 0.5 * wave(t, 2)), "accent", 255, occlude=False)
    p.glow(0, 0.02, 0.16, int(170 + 85 * wave(t, 2)))


@sigil("flower_of_life", "The Flower of Life", "Sacred Geometry", 6,
       "Overlapping circles of equal measure, cut into the granite of the Osirion at Abydos: the seed from which all forms unfold",
       variants=[("Flower", 2), ("Seed", 1)],
       rings=("Greek Alphabet", "Hieroglyphs", "Zodiac"))
def flower_of_life(p, t, v):
    r = 0.3
    k = 0.84 + 0.16 * math.cos(TAU * t)
    rings = 1 if v["variant"] == "Seed" else 2
    if rings == 1:
        r = 0.42
    centres = [(0.0, 0.0)]
    for ring in range(1, rings + 1):
        for side in range(6):
            a0 = polar(ring * r, 60 * side)
            a1 = polar(ring * r, 60 * (side + 1))
            for j in range(ring):
                centres.append((lerp(a0[0], a1[0], j / ring), lerp(a0[1], a1[1], j / ring)))
    rot = 60 * t
    outer = r * (rings + 1)
    p.glow(0, 0, outer * 0.8, int(60 + 150 * (1 - k)), "light")
    p.circle(0, 0, outer, 2.6)
    p.circle(0, 0, outer + 0.04, 1.0, "ink", 170)
    with p.tf(rot=rot):
        for i, (x, y) in enumerate(centres):
            d = math.hypot(x, y) / (rings * r) if rings else 0
            vv = int(255 * (0.6 + 0.4 * wave(t, 1, -d * 0.5)))
            p.circle(x * k, y * k, r, 1.8, "ink", vv)
        for x, y in centres:
            p.dot(x * k, y * k, 1.8, "accent", 200)


@sigil("metatron", "Metatron's Cube", "Sacred Geometry", 5,
       "Thirteen circles of the Fruit of Life joined by seventy-eight lines, within which every Platonic solid lies hidden",
       rings=("Hebrew Alphabet", "Greek Alphabet"))
def metatron(p, t, v):
    d, r = 0.42, 0.13
    cs = [(0.0, 0.0)] + [polar(d, 90 + 60 * i) for i in range(6)] + [polar(2 * d, 90 + 60 * i) for i in range(6)]
    for i, a in enumerate(cs):
        for b in cs[i + 1:]:
            p.line([a, b], 1.0, "ink", 120)
    for i, (x, y) in enumerate(cs):
        p.ring(x, y, r, 1.8)
        g = wave(t, 1, -i / 13)
        if g > 0.8:
            p.circle(x, y, r * 0.6, 1.6, "accent", int(255 * (g - 0.8) / 0.2))
            p.glow(x, y, r * 1.6, int(220 * (g - 0.8) / 0.2))
    cube = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    p.disc(0, 0, r, "fill")
    wireframe(p, cube, edges_by_length(cube), TAU * t, 0.62, 0.0, 0.075, 1.6)


SOLIDS = {
    "Tetrahedron (Fire)": [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)],
    "Octahedron (Air)": [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
    "Cube (Earth)": [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)],
}
_phi = (1 + 5 ** 0.5) / 2
SOLIDS["Icosahedron (Water)"] = [p for a in (-1, 1) for b in (-_phi, _phi)
                                 for p in ((0, a, b), (a, b, 0), (b, 0, a))]
SOLIDS["Dodecahedron (Aether)"] = ([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)] +
                                   [p for a in (-1 / _phi, 1 / _phi) for b in (-_phi, _phi)
                                    for p in ((0, a, b), (a, b, 0), (b, 0, a))])


@sigil("platonic", "The Platonic Solid", "Platonism", 6,
       "The five regular bodies of the Timaeus, which Plato gave to Fire, Air, Earth, Water and the Heavens",
       variants=[(k, 1) for k in SOLIDS] + [("Star Tetrahedron", 1)],
       rings=("Greek Alphabet", "Alchemical Elements", "Planetary Metals"))
def platonic(p, t, v):
    var = v["variant"]
    p.circle(0, 0, 0.98, 1.4, "ink", 150)
    p.circle(0, 0, 0.98, 6.0, "faint", 120)
    ry, rx, rz = TAU * t, 0.45, 0.25 * math.sin(TAU * t)
    p.glow(0, 0, 0.7, int(80 + 40 * wave(t, 2)), "light")
    for i in range(12):
        p.ray(0, 0, i * 30 + 15, 0.25, 0.95, 0.015, 0.05, int(60 + 50 * wave(t, 1, -i / 12)))
    if var == "Star Tetrahedron":
        a = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
        b = [(-x, -y, -z) for x, y, z in a]
        for verts in (a, b):
            wireframe(p, verts, edges_by_length(verts), ry, rx, rz, 0.5, 2.4)
        return
    verts = SOLIDS[var]
    m = max(math.sqrt(x * x + y * y + z * z) for x, y, z in verts)
    verts = [(x / m, y / m, z / m) for x, y, z in verts]
    wireframe(p, verts, edges_by_length(verts), ry, rx, rz, 0.8, 2.6)


@sigil("solomon", "The Seal of Solomon", "Solomonic Magic", 6,
       "Two triangles, fire and water, above and below, locked into the hexagram with which Solomon bound the spirits",
       rings=("Hebrew Alphabet", "Planetary Metals", "Zodiac"))
def solomon(p, t, v):
    p.circle(0, 0, 0.98, 2.6)
    p.circle(0, 0, 0.90, 1.4)
    for i in range(36):
        p.dot(*polar(0.94, i * 10 + 10 * t), 1.4, "ink", 200)
    up = ngon(3, 0.86, 90 + 120 * t)
    dn = ngon(3, 0.86, 270 - 120 * t)
    p.line(up, 4.4, "faint", 255, closed=True)
    p.line(dn, 4.4, "faint", 255, closed=True)
    p.line(up, 2.4, "ink", 255, closed=True)
    p.line(dn, 2.4, "accent", 230, closed=True)
    p.glow(0, 0, 0.9, 110, "light")
    for k, q in enumerate(up + dn):
        p.sparkle(*q, 0.1, int(140 + 115 * wave(t, 1, k / 6)), rot=60 * t)
    p.disc(0, 0, 0.26, "fill")
    p.circle(0, 0, 0.26, 1.4, "ink", 200)
    p.glow(0, 0, 0.3, int(120 + 60 * wave(t, 2)))
    p.text("יהוה", 0, 0.0, 24, "hebrew", "ink", 255, upright=True)


@sigil("horus", "The Eye of Horus", "Egyptian Mysteries", 7,
       "The Wedjat, the eye Horus lost fighting Set and Thoth made whole again: health, restoration and the full measure",
       rings=("Hieroglyphs",))
def horus(p, t, v):
    def band(path, w0, w1):  # a gold band with an engraved groove down its middle
        p.poly(thick(path, [lerp(w0, w1, i / (len(path) - 1)) for i in range(len(path))]), "ink")
        p.line(path[2:-2], 1.0, "ink", 120)

    with p.tf(dy=0.08, s=1.0 + 0.02 * math.sin(TAU * t)):
        brow = bezier3((-0.8, 0.42), (-0.3, 0.66), (0.35, 0.66), (0.84, 0.44), 40)
        band(brow, 0.11, 0.06)
        up = bezier3((-0.6, 0.05), (-0.3, 0.36), (0.25, 0.33), (0.58, 0.03), 40)
        lo = bezier3((-0.6, 0.05), (-0.25, -0.18), (0.25, -0.16), (0.58, 0.03), 40)
        p.poly(up + lo[::-1], "fill")
        lx = 0.06 * math.sin(TAU * t)
        p.glow(lx, 0.07, 0.34, int(120 + 60 * wave(t, 2)))
        with p.clip(up + lo[::-1]), p.tf(dx=lx, dy=0.07):
            ir = 0.17
            p.disc(0, 0, ir, "fill")
            for k in range(40):
                a = k * 9 + 5 * math.sin(TAU * t)
                p.line([polar(ir * 0.42, a), polar(ir * (0.92 if k % 2 else 0.75), a)], 0.55, "ink", 150)
            p.line([polar(ir * (0.6 + 0.05 * math.sin(math.radians(d) * 10)), d) for d in range(0, 360, 4)], 0.8, "accent", 190, closed=True)
            p.circle(0, 0, ir, 2.4, "accent", 240)
            p.disc(0, 0, ir * (0.36 + 0.05 * wave(t, 1)), "fill")
            p.circle(0, 0, ir * (0.36 + 0.05 * wave(t, 1)), 0.9, "ink", 230)
            p.dot(-ir * 0.32, ir * 0.36, 2.4, "accent", 255)
            p.sparkle(-ir * 0.32, ir * 0.36, ir * 0.5, 190)
        p.line(up, 3.4)
        p.line(lo, 3.0)
        p.line([(x, y - 0.035) for x, y in up[6:-6]], 0.7, "ink", 150)  # inner lid line
        band(bezier((0.5, 0.05), (0.76, 0.1), (0.98, 0.04), 20), 0.06, 0.035)
        drop = bezier((-0.08, -0.14), (-0.1, -0.4), (-0.18, -0.7), 20)
        band(drop, 0.07, 0.045)
        p.poly([(-0.25, -0.74), (-0.11, -0.74), (-0.18, -0.66)], "ink")
        lead = bezier3((0.12, -0.13), (0.14, -0.4), (0.27, -0.46), (0.40, -0.46), 20)
        C = (0.40, -0.62)
        spiral = [polar(lerp(0.16, 0.035, i / 50), 90 - 450 * i / 50, *C) for i in range(51)]
        path = lead + spiral[1:]
        band(path, 0.055, 0.025)
        spark = path_point(drop + path[::-1], t)
        p.dot(*spark, 3.2, "accent", int(255 * wave(t, 2)))
        p.sparkle(*spark, 0.09, int(255 * wave(t, 2)), rot=90 * t)


@sigil("ankh", "The Ankh beneath the Aten", "Egyptian Mysteries", 6,
       "The key of life held to the nostrils of kings, beneath the sun-disc whose rays end in open hands",
       rings=("Hieroglyphs",))
def ankh(p, t, v):
    sun = (0, 0.9)
    for i in range(11):
        a = 205 + i * 13
        end = polar(1.15, a, *sun)
        p.ray(*sun, a, 0.1, 1.2, 0.025, 0.1, int(230 * (0.55 + 0.45 * wave(t, 1, -i / 11))))
        p.line([polar(0.14, a, *sun), end], 0.7, "ink", 120)
        p.disc(*end, 0.025, "ink", 200, occlude=False)
        for k in range(3):
            u = ((k + t) / 3)
            p.sparkle(*polar(lerp(0.15, 1.1, u), a, *sun), 0.045, int(255 * math.sin(math.pi * u)))
    p.glow(*sun, 0.42, 255, "light")
    p.disc(*sun, 0.1, "ink", occlude=False)
    p.circle(*sun, 0.13, 1.4, "accent", 200)
    loop = [(0.25 * math.cos(a), 0.47 + 0.33 * math.sin(a)) for a in (TAU * i / 120 for i in range(121))]
    shape_parts = [
        thick(loop, 0.1),
        [(-0.1, 0.17), (-0.5, 0.24), (-0.5, -0.03), (-0.1, 0.04), (0.1, 0.04), (0.5, -0.03), (0.5, 0.24), (0.1, 0.17)],
        [(-0.065, 0.12), (0.065, 0.12), (0.14, -0.95), (-0.14, -0.95)],
    ]
    for part in shape_parts:
        p.poly(part, "fill")
    for part in shape_parts:
        p.poly(part, "ink", occlude=False)
    inner = [(0.25 * 0.82 * math.cos(a), 0.47 + 0.33 * 0.86 * math.sin(a)) for a in (TAU * i / 120 for i in range(121))]
    p.line(inner, 1.0, "ink", 0)
    p.line([(0, 0.05), (0, -0.88)], 1.0, "ink", 0)
    p.line([(-0.45, 0.105), (0.45, 0.105)], 1.0, "ink", 0)


@sigil("caduceus", "The Caduceus of Hermes", "Hermeticism", 7,
       "The winged staff of Hermes Trismegistus about which two serpents twine: the opposing currents reconciled",
       rings=("Planetary Metals", "Alchemical Elements", "Emerald Tablet"))
def caduceus(p, t, v):
    flap = 6 * math.sin(TAU * t)

    def feather(root, a, L, wmax, barbs=True):
        path = bezier(root, polar(L * 0.55, a - 5, *root), polar(L, a, *root), 22)
        ws = [wmax * math.sin(math.pi * min(1.0, 0.08 + 0.92 * (i / 22) ** 0.9)) ** 0.6 * (1 - 0.15 * i / 22) + 0.002 for i in range(23)]
        f = thick(path, ws)
        p.poly(f, "fill")
        p.poly(f, "ink", 45, occlude=False)
        p.line(f, 1.1, closed=True)
        p.line(path[2:-2], 0.8, "ink", 210)  # rachis
        if barbs:
            for j in range(3, 20, 3):
                (x0, y0), (x1, y1) = path[j], path[j + 1]
                dl = math.hypot(x1 - x0, y1 - y0) or 1
                tx, ty = (x1 - x0) / dl, (y1 - y0) / dl
                for sgn in (1, -1):
                    nx, ny = -ty * sgn, tx * sgn
                    w = ws[j] * 0.45
                    p.line([(x0, y0), (x0 + nx * w + tx * w * 0.9, y0 + ny * w + ty * w * 0.9)], 0.5, "ink", 140)

    for side in (1, -1):
        with p.tf(dy=0.6, sx=side):
            for k in range(7):  # primaries
                feather((-0.04, 0.0), 158 - k * 10 - flap * (1 - k * 0.1), 0.78 - k * 0.06, 0.08)
            for k in range(5):  # coverts, layered over the root
                feather((-0.03, 0.01), 150 - k * 10 - flap * 0.5, 0.34 - k * 0.03, 0.075, barbs=False)
            p.arc(-0.04, 0.0, 0.22, 100 - flap * 0.5, 155 - flap * 0.5, 1.2, "ink", 200)

    staff = [(-0.028, 0.6), (0.028, 0.6), (0.04, -0.96), (-0.04, -0.96)]
    y_top, y_bot, turns = 0.36, -0.82, 2.25
    k = TAU * turns / (y_top - y_bot)
    snakes = []
    for phase in (0.0, math.pi):
        pts, dep, wid = [], [], []
        for i in range(201):
            y = lerp(y_bot, y_top, i / 200)
            th = math.pi / 2 + phase - (y_top - y) * k
            A = 0.07 + 0.2 * math.sin(math.pi * (0.15 + 0.75 * (y - y_bot) / (y_top - y_bot)))
            pts.append((A * math.sin(th), y))
            dep.append(math.cos(th))
            wid.append(lerp(0.003, 0.085, (i / 200) ** 0.5) * (1 - 0.25 * max(0.0, i / 200 - 0.9) / 0.1))
        snakes.append((pts, dep, wid))
    runs = []
    for pts, dep, wid in snakes:
        idx = 0
        for front, run in helix_runs(pts, dep):
            n = len(run)
            runs.append((front, run, wid[idx:idx + n]))
            idx += n - 1
    for front, run, w in runs:
        if not front:
            serpent_run(p, run, w, front=False)
    p.poly(staff, "fill")
    p.poly(staff, "ink", occlude=False)
    p.line([(0, 0.55), (0, -0.9)], 1.0, "ink", 0)
    for front, run, w in runs:
        if front:
            serpent_run(p, run, w, flow=-3 * t)
    for pts, dep, wid in snakes:
        x, y = pts[-1]
        side = 1 if x > 0 else -1
        snake_head_top(p, x, y, 90 + side * 30, wid[-1], t + (0.5 if side > 0 else 0))
        u = (t + (0.5 if side > 0 else 0)) % 1
        p.sparkle(*path_point(pts, u), 0.07, int(255 * math.sin(math.pi * u)))
    p.glow(0, 0.68, 0.3, 200, "light")
    p.ring(0, 0.68, 0.075, 2.0)
    p.disc(0, 0.68, 0.035 * (1 + 0.3 * wave(t, 2)), "accent", 255, occlude=False)
    p.glow(0, 0.68, 0.09, int(180 + 75 * wave(t, 2)))


@sigil("rose_cross", "The Rose Cross", "Rosicrucianism", 6,
       "The rose of twenty-two petals blooming at the heart of the cross, after the Fama Fraternitatis and the Golden Dawn",
       rings=("Hebrew Alphabet", "Zodiac", "Alchemical Elements", "Emerald Tablet"))
def rose_cross(p, t, v):
    cy = 0.2
    for i in range(24):
        long = i % 2 == 0
        p.ray(0, cy, 90 + 15 * i, 0.3, (1.15 if long else 0.85) + 0.08 * wave(t, 2, i * 0.3), 0.025, 0.12 if long else 0.07,
              int(120 + 100 * wave(t, 1, -i / 24)))
    ends = [((0, 0.86), (0, 1)), ((0, -0.98), (0, -1)), ((-0.78, cy), (-1, 0)), ((0.78, cy), (1, 0))]
    for (x, y), (dx, dy) in ends:
        for ox, oy in ((dx * 0.07, dy * 0.07), (-dy * 0.08, dx * 0.08), (dy * 0.08, -dx * 0.08)):
            p.ring(x + ox, y + oy, 0.065, 2.0)
    bars = [[(-0.085, -0.98), (0.085, -0.98), (0.085, 0.86), (-0.085, 0.86)],
            [(-0.78, cy - 0.085), (0.78, cy - 0.085), (0.78, cy + 0.085), (-0.78, cy + 0.085)]]
    for b in bars:
        p.poly(b, "fill")
    for b in bars:
        p.line(b, 2.2, closed=True)
        p.line([(lerp(b[0][0], b[2][0], 0.5), b[0][1]), (lerp(b[0][0], b[2][0], 0.5), b[2][1])] if b is bars[0]
               else [(b[0][0], cy), (b[1][0], cy)], 1.0, "accent", 140)
    bloom = 1 + 0.03 * math.sin(TAU * t)
    with p.tf(dy=cy, s=bloom):
        for i in range(5):  # sepals behind the flower
            a_ = 90 + 72 * i + 36 + 6 * t * 0
            sep = [polar(0.18, a_ - 14), polar(0.36, a_ - 6), polar(0.47, a_), polar(0.36, a_ + 6), polar(0.18, a_ + 14)]
            p.poly(sep, "fill")
            p.poly(sep, "ink", 60, occlude=False)
            p.line(sep, 1.3, closed=True)
            p.line([polar(0.2, a_), polar(0.42, a_)], 0.6, "ink", 160)

        def petal(r0, r1, a_, half, tint):
            """A broad, cupped rose petal: narrow claw, wide rounded blade with a
            shallow notch, a rolled (lit) outer edge and a darker throat."""
            pts = []
            for k in range(21):
                f = k / 20
                ang = a_ - half + 2 * half * f
                notch = 0.035 * (r1 - r0) * math.exp(-((f - 0.5) / 0.08) ** 2)
                pts.append(polar(r1 - notch - (r1 - r0) * 0.12 * (2 * abs(f - 0.5)) ** 2, ang))
            base = [polar(r0, a_ + half * 0.25), polar(r0, a_ - half * 0.25)]
            shape = pts + base
            p.poly(shape, "fill")
            p.poly(shape, "accent", tint, occlude=False)
            throat = [polar(r0 + (r1 - r0) * 0.45, a_ - half * 0.55 + half * 1.1 * k / 10) for k in range(11)] + base
            p.poly(throat, "fill", 120, occlude=False)
            p.line(shape, 1.4, closed=True)
            p.line([polar(r1 - (r1 - r0) * 0.1, a_ - half * 0.8 + half * 1.6 * k / 12) for k in range(13)], 1.6, "flare", 120)

        for count, r0, r1, spin, tint in ((12, 0.12, 0.4, 30 * t, 34), (7, 0.07, 0.3, -360 / 7 * t, 48), (3, 0.03, 0.2, 120 * t, 64)):
            half = 360 / count * 0.62
            for i in range(count):
                petal(r0, r1, 90 + spin + 360 * i / count + (180 / count if count == 7 else 0), half, tint)
        # a spiralling, tightly furled bud at the heart
        bud = [polar(0.11 * (k / 80) ** 0.9, 90 + 720 * (k / 80) + 120 * t) for k in range(81)]
        p.disc(0, 0, 0.11, "fill")
        p.disc(0, 0, 0.11, "accent", 80, occlude=False)
        p.line(bud, 1.6)
        p.line([polar(0.11 * (k / 80) ** 0.9 + 0.006, 90 + 720 * (k / 80) + 120 * t) for k in range(10, 81)], 1.2, "flare", 150)
        p.circle(0, 0, 0.11, 1.2)
    p.glow(0, cy, 0.22, int(150 + 80 * wave(t, 2)))


TRIGRAMS = [(1, 1, 1), (0, 1, 1), (0, 1, 0), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1), (1, 1, 0)]


@sigil("taiji", "The Taijitu and the Eight Trigrams", "Taoism", 6,
       "Yin and Yang turning within one another, ringed by the Earlier Heaven arrangement of Fu Xi's eight trigrams",
       rings=("Bagua", "Zodiac"))
def taiji(p, t, v):
    R = 0.42
    p.circle(0, 0, 0.98, 2.4)
    p.circle(0, 0, 0.54, 1.2, "ink", 180)
    cur = t * 8
    for i, bits in enumerate(TRIGRAMS):
        a = 90 - 45 * i
        lit = max(0.0, 1 - min((cur - i) % 8, (i - cur) % 8) / 1.2)
        with p.tf(rot=a - 90):
            for k, bit in enumerate(bits):
                y = 0.64 + 0.095 * k
                segs = [(-0.16, 0.16)] if bit else [(-0.16, -0.035), (0.035, 0.16)]
                for x0, x1 in segs:
                    bar = [(x0, y - 0.03), (x1, y - 0.03), (x1, y + 0.03), (x0, y + 0.03)]
                    p.poly(bar, "ink", 255)
                    if lit > 0:
                        p.poly(bar, "accent", int(255 * lit), occlude=False)
    with p.tf(rot=-360 * t):
        p.disc(0, 0, R, "fill")
        yang = (p.circle_pts(0, 0, R, 90, -90, 90) + p.circle_pts(0, -R / 2, R / 2, -90, -270, 45)[1:]
                + p.circle_pts(0, R / 2, R / 2, -90, 90, 45)[1:])
        p.poly(yang, "ink", occlude=False)
        p.disc(0, -R / 2, R * 0.13, "fill")
        p.disc(0, R / 2, R * 0.13, "ink", occlude=False)
        p.circle(0, 0, R, 2.4)


@sigil("dharmachakra", "The Wheel of the Dharma", "Buddhism", 5,
       "The eight-spoked wheel set turning in the deer park at Sarnath: the Noble Eightfold Path rolling through the world",
       rings=("Om Mani Padme Hum",))
def dharmachakra(p, t, v):
    p.glow(0, 0, 0.9, 120, "light")
    with p.tf(rot=-45 * t):
        for i in range(8):
            p.ray(0, 0, 45 * i, 0.2, 1.55, 0.04, 0.26, int(150 + 80 * wave(t, 1, -i / 8)))
        for i in range(8):
            a = 22.5 + 45 * i
            p.line([polar(0.8, a), polar(0.9, a)], 2.4)
            p.ring(*polar(0.93, a), 0.05, 2.0)
        ring = p.circle_pts(0, 0, 0.75, 0, 360, 240)
        p.poly(thick(ring, 0.1), "fill")
        p.poly(thick(ring, 0.1), "ink", occlude=False)
        p.line(p.circle_pts(0, 0, 0.75, 0, 360, 240), 1.2, "ink", 0)
        for i in range(8):
            a = 22.5 + 45 * i
            with p.tf(rot=a):
                sp = [(0.17, 0), (0.42, 0.05), (0.7, 0.0), (0.42, -0.05)]
                p.poly(sp, "fill")
                p.line(sp, 1.8, closed=True)
                p.line([(0.2, 0), (0.66, 0)], 1.0, "accent", 140)
        p.ring(0, 0, 0.19, 2.2)
    p.glow(0, 0, 0.22, int(170 + 70 * wave(t, 2)))
    with p.tf(rot=120 * t):
        for i in range(3):
            with p.tf(rot=120 * i):
                comma = p.circle_pts(0, 0.07, 0.07, -90, 90, 20) + p.circle_pts(0, 0.035, 0.035, 90, -90, 12)
                p.poly(comma, "accent", 255, occlude=False)


@sigil("pentalpha", "The Pentalpha", "Pythagoreanism", 4,
       "The pentagram of the Pythagoreans, sign of Hygieia, whose heart holds a smaller star, and that one another, without end",
       rings=("Greek Alphabet", "Planetary Metals"))
def pentalpha(p, t, v):
    phi2 = _phi ** 2
    for n in range(-1, 7):
        u = n - t
        r = 0.95 * phi2 ** (-u)
        fade = smooth(0.02, 0.09, r) * (1 - smooth(0.8, 1.0, r))
        if fade <= 0.01:
            continue
        pts = ngon(5, r, 90 + 36 * u)
        star = [pts[i] for i in (0, 2, 4, 1, 3)]
        w = max(0.8, 2.6 * min(1.0, r / 0.5) ** 0.3)
        p.line(star, w, "ink", int(255 * fade), closed=True)
        p.circle(0, 0, r, 1.0, "ink", int(120 * fade))
    p.glow(0, 0, 0.32, int(200 + 55 * wave(t, 2)))
    p.sparkle(0, 0, 0.12, 255, rot=36 * t)
    p.circle(0, 0, 1.02, 2.4)
    for i, ch in enumerate("ΥΓΙΘΑ"):
        a = 90 - 72 * i
        p.disc(*polar(1.02, a), 0.08, "fill")
        p.circle(*polar(1.02, a), 0.08, 1.4)
        p.text(ch, *polar(1.02, a), 14, "serif_text", "ink", 255, upright=True)


@sigil("athanor", "The Philosophical Egg", "European Alchemy", 6,
       "The sealed Vas Hermeticum upon the athanor's slow fire, in which the matter is dissolved, putrefied and reborn",
       rings=("Alchemical Elements", "Planetary Metals", "VITRIOL"))
def athanor(p, t, v):
    base = [(-0.42, -0.62), (0.42, -0.62), (0.32, -0.98), (-0.32, -0.98)]
    p.poly(base, "fill")
    p.line(base, 2.2, closed=True)
    for i in range(3):
        y = -0.72 - 0.08 * i
        p.line([(-0.36 + 0.03 * i, y), (0.36 - 0.03 * i, y)], 1.0, "ink", 160)
    p.glow(0, -0.56, 0.42, int(170 + 60 * wave(t, 3)))
    cy, rx, ry = -0.05, 0.4, 0.5
    egg = [(rx * math.sin(s) * (1 - 0.14 * math.cos(s)), cy + ry * math.cos(s))
           for s in (TAU * i / 160 for i in range(160))]
    neck = [(-0.05, cy + ry - 0.02), (-0.05, 0.84), (0.05, 0.84), (0.05, cy + ry - 0.02)]
    p.poly(egg, "fill")
    p.poly(neck, "fill")
    lvl = -0.12
    liquid = []
    for x, y in egg:
        if y < lvl:
            liquid.append((x, y))
    wavepts = [(x, lvl + 0.025 * math.sin(TAU * (t + x * 1.5))) for x in [lerp(-rx * 0.97, rx * 0.97, i / 30) for i in range(31)]]
    liquid = sorted([q for q in liquid if q[0] > 0], key=lambda q: -q[1]) + \
        sorted([q for q in liquid if q[0] <= 0], key=lambda q: q[1])
    p.poly(liquid + wavepts, "accent", 60, occlude=False)
    p.line(wavepts, 1.4, "ink", 200)
    for i in range(7):
        u = (t + i / 7) % 1
        bx = lerp(-0.22, 0.22, (i * 0.618) % 1) + 0.02 * math.sin(TAU * (u * 2 + i))
        by = lerp(-0.5, lvl - 0.02, u)
        p.circle(bx, by, 0.018 + 0.012 * (i % 3), 1.0, "ink", int(220 * math.sin(math.pi * u)))
    p.line(egg, 2.6, closed=True)
    for i in range(7):
        x = -0.3 + 0.1 * i
        for layer, sc, vv in (("accent", 1.0, 170), ("flare", 0.55, 230)):
            h = (0.22 + 0.08 * math.sin(TAU * (2 * t + i * 0.37)) + 0.04 * math.sin(TAU * (3 * t + i * 0.71))) * sc * (1.15 if i in (2, 3, 4) else 0.85)
            sway = 0.035 * math.sin(TAU * (t + i * 0.2)) * sc
            w = 0.055 * sc
            tip = (x + sway * 1.4 + 0.02 * sc, -0.62 + h)
            left = bezier3((x - w, -0.62), (x - w * 1.2, -0.62 + h * 0.35), (x + sway - w * 0.4, -0.62 + h * 0.7), tip, 14)
            right = bezier3(tip, (x + sway + w * 0.7, -0.62 + h * 0.6), (x + w * 1.1, -0.62 + h * 0.3), (x + w, -0.62), 14)
            p.poly(left + right[1:], layer, vv, occlude=False)
        u = (t * 2 + i * 0.37) % 1
        p.sparkle(x + 0.04 * math.sin(TAU * (u + i)), -0.6 + 0.35 * u, 0.025, int(220 * math.sin(math.pi * u)))
    p.line(neck, 2.2)
    p.ring(0, 0.88, 0.05, 2.0)
    bob = 0.03 * math.sin(TAU * t)
    with p.tf(dy=0.17 + bob):
        p.circle(0, 0, 0.075, 2.2)
        p.arc(0, 0.12, 0.075, 200, 340, 2.2)
        p.line([(0, -0.075), (0, -0.25)], 2.2)
        p.line([(-0.07, -0.165), (0.07, -0.165)], 2.2)
        p.dot(0, 0, 2.2, "accent", int(255 * wave(t, 2)))


@sigil("tetractys", "The Tetractys", "Pythagoreanism", 5,
       "One, two, three and four, which make the perfect ten: the sacred figure by which the Pythagoreans swore their oath",
       rings=("Greek Alphabet",))
def tetractys(p, t, v):
    s = 0.44
    pts = [((j - k / 2) * s, 0.5 - k * s * 0.866) for k in range(4) for j in range(k + 1)]
    tri = [(0, 0.98), (-1.04, -0.82), (1.04, -0.82)]
    p.poly(tri, "fill")
    p.line(tri, 2.6, closed=True)
    p.line([(0, 0.86), (-0.9, -0.74), (0.9, -0.74)], 1.0, "ink", 150, closed=True)
    for i, a in enumerate(pts):
        for b in pts[i + 1:]:
            if abs(math.dist(a, b) - s) < 1e-6:
                p.line([a, b], 1.2, "ink", 150)
    cur = t * 13
    for i, (x, y) in enumerate(pts):
        p.ring(x, y, 0.075, 2.2)
        lit = 1.0 if i <= cur < 11 else 0.0
        if cur >= 11:
            lit = 1.0 - (cur - 11) / 2
        lit *= smooth(i, i + 0.6, cur) if cur < 11 else 1.0
        if lit > 0:
            p.disc(x, y, 0.05, "accent", int(255 * lit), occlude=False)
            p.glow(x, y, 0.16, int(200 * lit))


@sigil("triskele", "The Triple Spiral", "Celtic Mysteries", 5,
       "Three spirals in one unbroken line, carved at the entrance stone of Newgrange five thousand years ago",
       rings=("Ogham", "Elder Futhark"))
def triskele(p, t, v):
    p.circle(0, 0, 0.98, 2.2)
    for i in range(48):
        p.dot(*polar(0.92, 7.5 * i - 15 * t), 1.5, "ink", 200)
    p.glow(0, 0, 0.6, 90, "light")
    with p.tf(rot=-120 * t):
        R, rmax, turns = 0.47, 0.31, 1.75
        arms = []
        for i in range(3):
            base = 90 + 120 * i
            c = polar(R, base)
            to_centre = base + 180
            end_ang = to_centre - 100  # where the spiral's outer end sits on its own circle
            sp = [polar(rmax * (k / 140) ** 0.95, end_ang + 360 * turns * (k / 140 - 1), *c) for k in range(141)]
            e = sp[-1]
            tang = math.radians(end_ang + 90)
            # sweep from the spiral's outer end into the common centre
            link = bezier3(e, (e[0] + 0.3 * math.cos(tang), e[1] + 0.3 * math.sin(tang)),
                           polar(0.16, to_centre + 180 - 35), (0.0, 0.0), 30)
            arms.append(sp + link[1:])
        for arm in arms:
            n = len(arm)
            w = [0.022 + 0.05 * min(1.0, (i / n) * 3.5) ** 0.7 * (1 - 0.55 * max(0.0, i / n - 0.8) / 0.2) for i in range(n)]
            band = thick(arm, w)
            p.line(arm, 14.0, "flare", 60)
            p.poly(band, "fill")
            p.poly(band, "ink", 210, occlude=False)
            p.line(arm[3:-3], 1.0, "ink", 90)  # engraved groove
            p.line(band, 1.2, "ink", 255, closed=True)
        for i in range(3):
            c = polar(R, 90 + 120 * i)
            p.disc(*c, 0.028 * (1 + 0.4 * wave(t, 1, i / 3)), "accent", 255, occlude=False)
            p.glow(*c, 0.16, int(150 + 90 * wave(t, 1, i / 3)))
        p.disc(0, 0, 0.035, "accent", 230, occlude=False)
        p.glow(0, 0, 0.2, int(140 + 80 * wave(t, 2)))


@sigil("enneagram", "The Enneagram", "Fourth Way", 4,
       "Gurdjieff's symbol of perpetual motion: the Law of Three in the triangle, the Law of Seven in the circulating figure 1-4-2-8-5-7",
       rings=("Greek Alphabet", "Planetary Metals"))
def enneagram(p, t, v):
    R = 0.82
    pt = {k: polar(R, 90 - 40 * (k % 9)) for k in range(1, 10)}
    p.glow(0, 0, R * 0.9, 90, "light")
    for k in range(9):
        p.line([(0, 0), polar(R, 90 - 40 * k)], 0.6, "faint", 200)
    p.circle(0, 0, R, 2.4)
    tri = [pt[3], pt[6], pt[9]]
    p.line(tri, 2.2, "ink", 255, closed=True)
    hexad = [pt[k] for k in (1, 4, 2, 8, 5, 7)]
    p.line(hexad, 2.2, "ink", 255, closed=True)
    loop = hexad + [hexad[0]]
    p.line(sub_path(loop, max(0, t - 0.08), t, 16), 3.2, "accent", 255)
    p.dot(*path_point(loop, t), 3.4, "accent")
    p.sparkle(*path_point(loop, t), 0.1, 230, rot=360 * t)
    tl = tri + [tri[0]]
    p.dot(*path_point(tl, (t * 2) % 1), 2.8, "accent", 220)
    order = [1, 4, 2, 8, 5, 7]
    for k in range(1, 10):
        x, y = pt[k]
        if k in order:
            d = (t * 6 - order.index(k)) % 6
            p.glow(x, y, 0.16, int(230 * max(0.0, 1 - d / 1.5)))
        p.ring(x, y, 0.045, 1.8)
        p.text(str(k), *polar(R + 0.13, 90 - 40 * (k % 9)), 14, "serif_text", "ink", 255, upright=True)


@sigil("coniunctio", "The Chymical Wedding of Sun and Moon", "European Alchemy", 6,
       "Sol and Luna, the red king and the white queen, circling toward the conjunction from which the Mercury of the wise is born",
       rings=("Planetary Metals", "Alchemical Elements", "Zodiac"))
def coniunctio(p, t, v):
    R = 0.56
    p.circle(0, 0, R, 1.0, "ink", 140)
    p.circle(0, 0, R, 5.0, "faint", 140)
    a = 90 - 360 * t
    sx, sy = polar(R, a)
    with p.tf(dx=sx, dy=sy, rot=-90 * t):
        p.glow(0, 0, 0.42, 230, "light")
        for i in range(16):
            ang = i * 22.5
            if i % 2:
                p.ray(0, 0, ang, 0.15, 0.48 + 0.06 * wave(t, 3, i * 0.13), 0.04, 0.09, 235)
            else:
                wv = [polar(lerp(0.2, 0.34, k / 12), ang + 6 * math.sin(k / 12 * TAU)) for k in range(13)]
                p.line(wv, 1.4, "ink", 220)
        p.ring(0, 0, 0.17, 2.6)
        p.circle(0, 0, 0.11, 1.0, "ink", 160)
        p.disc(0, 0, 0.04, "accent", 255, occlude=False)
    mx, my = polar(R, a + 180)
    p.disc(mx, my, 0.17, "fill")
    crescent(p, mx, my, 0.16, a + 180 + 180, 0.5, "accent")
    p.circle(mx, my, 0.16, 1.0, "ink", 120)
    p.ring(0, 0, 0.1, 2.2)
    p.arc(0, 0.155, 0.09, 200, 340, 2.2)
    p.line([(0, -0.1), (0, -0.3)], 2.2)
    p.line([(-0.08, -0.2), (0.08, -0.2)], 2.2)
    p.dot(0, 0, 2.4, "accent", int(255 * wave(t, 2)))


@sigil("kundalini", "The Serpent Power", "Yoga & Tantra", 4,
       "Kundalini coiled at the root, rising through the seven lotuses along Sushumna while Ida and Pingala cross at every gate",
       rings=("Om Mani Padme Hum",))
def kundalini(p, t, v):
    y0, y1 = -0.84, 0.84
    sp = (y1 - y0) / 6
    ys = [y0 + i * sp for i in range(7)]
    petals = [4, 6, 10, 12, 16, 2, 24]
    for side, layer in ((1, "ink"), (-1, "accent")):
        pts = [(side * 0.22 * math.sin(math.pi * (y - y0) / sp), y) for y in (lerp(y0, y1, i / 200) for i in range(201))]
        p.line(pts, 1.6, layer, 170)
    p.line([(0, -0.98), (0, 0.98)], 2.4)
    coil = [(0.05 * (1 + k / 70) * math.cos(TAU * 3.5 * k / 140 - TAU * t),
             y0 - 0.06 + 0.022 * (1 + k / 70) * math.sin(TAU * 3.5 * k / 140 - TAU * t) + k * 0.001)
            for k in range(141)]
    p.line(coil, 2.0, "ink", 230)
    e = lerp(-1.0, 1.05, t)
    for i, (y, n) in enumerate(zip(ys, petals)):
        rr = 0.1 if i < 6 else 0.13
        if n == 2:
            for s in (-1, 1):
                pts = [(s * (0.05 + 0.08 * (1 - math.cos(a)) / 2 * 1.6), y + 0.06 * math.sin(a)) for a in (TAU * k / 30 for k in range(31))]
                p.poly(pts, "fill")
                p.line(pts, 1.4)
        else:
            for k in range(n):
                pet = [(x, yy + y) for x, yy in lotus_petal(rr * 0.5, rr, 360 * k / n + 90, 180 / n * 0.85)]
                p.poly(pet, "fill")
                p.line(pet, 1.1, "ink", 230)
        p.ring(0, y, rr * 0.5, 1.8)
        lit = math.exp(-(e - y) * 4) if e >= y else 0.0
        if lit > 0.03:
            p.disc(0, y, rr * 0.32, "accent", int(255 * lit), occlude=False)
            p.glow(0, y, rr * 1.6, int(220 * lit))
    if -0.98 < e < 0.98:
        p.dot(0, e, 3.6, "accent", 255)
        p.sparkle(0, e, 0.14, 255, rot=90 * t)


ZODIAC = "♈♉♊♋♌♍♎♏♐♑♒♓"
RETE_STARS = [(0.62, 20), (0.52, 75), (0.70, 130), (0.40, 170), (0.60, 215), (0.66, 290), (0.36, 330)]


@sigil("astrolabe", "The Astrolabe", "Hellenistic & Islamic Astronomy", 5,
       "The instrument of the heavens: the turning rete of fixed stars above the tympan of the observer's sky",
       rings=("Zodiac", "Planetary Metals", "Greek Alphabet"))
def astrolabe(p, t, v):
    p.circle(0, 0, 1.0, 2.6)
    p.circle(0, 0, 0.86, 1.6)
    for i in range(72):
        a = 90 - i * 5
        L = 0.92 if i % 6 else 0.86
        p.line([polar(1.0, a), polar(L, a)], 1.2 if i % 6 else 1.8, "ink", 220)
    for r in (0.66, 0.42, 0.26):
        p.circle(0, 0, r, 1.0, "faint", 255)
    for k in range(6):
        p.circle(0, 0.18 + 0.025 * k, 0.48 - 0.07 * k, 1.0, "faint", 255)
    for i in range(12):
        p.line([(0, 0), polar(0.86, 90 - i * 30)], 1.0, "faint", 200)
    with p.tf(rot=-360 * t):
        p.circle(0, 0.16, 0.5, 2.4)
        p.circle(0, 0.16, 0.43, 1.0, "ink", 200)
        for i in range(12):
            a = 90 - i * 30
            p.line([polar(0.43, a, 0, 0.16), polar(0.5, a, 0, 0.16)], 1.4)
            p.text(ZODIAC[i], *polar(0.465, a - 15, 0, 0.16), 10, "symbols", "ink", 230, angle=a - 15 - 90)
        p.circle(0, 0, 0.74, 2.0)
        for r, a in RETE_STARS:
            base = polar(0.74, a)
            tip = polar(r, a + 12)
            p.line([base, polar(lerp(0.74, r, 0.5), a + 3), tip], 1.6)
            flame = [polar(r + 0.04, a + 12), polar(r - 0.05, a + 5), tip]
            p.poly(flame, "ink", 255, occlude=False)
            p.dot(*tip, 2.0, "accent")
            p.sparkle(*tip, 0.06, 200, rot=45)
    with p.tf(rot=180 * t):
        rule = [(-0.98, -0.035), (0.98, -0.035), (0.98, 0.035), (-0.98, 0.035)]
        p.poly(rule, "fill")
        p.line(rule, 1.6, closed=True)
        p.line([(-0.9, 0), (0.9, 0)], 1.0, "accent", 180)
    p.ring(0, 0, 0.05, 2.0)


@sigil("valknut", "The Valknut", "Norse Mysteries", 5,
       "Three triangles knotted together, carved on the picture stones beside Odin and the fallen: the knot of the slain",
       rings=("Elder Futhark",))
def valknut(p, t, v):
    r, w = 0.72, 0.17
    for i in range(3):
        c = polar(0.3, 270 + 120 * i, 0, 0.06)
        band_o = ngon(3, r, 90, *c)
        band_i = ngon(3, r - w, 90, *c)
        p.poly(band_o + [band_o[0]] + [band_i[0]] + band_i[::-1], "fill")
        p.line(band_o, 2.4, closed=True)
        p.line(band_i, 2.4, closed=True)
        mid = ngon(3, r - w / 2, 90, *c)
        p.line(mid, 1.0, "ink", 110, closed=True)
        loop = mid + [mid[0]]
        u = (t + i / 3) % 1
        p.line(sub_path(loop, max(0.0, u - 0.07), u, 12), 2.6, "accent", 230)
    corners = [q for i in range(3) for q in ngon(3, r, 90, *polar(0.3, 270 + 120 * i, 0, 0.06))]
    for j, q in enumerate(corners):
        lit = max(0.0, 1 - min((t * 9 - j) % 9, (j - t * 9) % 9) / 1.5)
        p.sparkle(*q, 0.08 + 0.08 * lit, int(110 + 145 * lit), rot=30 * lit)
    p.glow(0, 0.06, 0.55, 120, "light")
    p.circle(0, 0, 1.0, 1.6, "ink", 200)
    for i in range(24):
        p.dot(*polar(1.0, 15 * i + 15 * t), 1.6, "accent", 200)


@sigil("giza", "The Pyramids of Giza", "Egyptian Mysteries", 7,
       "The three pyramids of the Giza plateau under the belt of Orion, the sky-form of Osiris",
       rings=("Hieroglyphs", "Zodiac"))
def giza(p, t, v):
    p.circle(0, 0, 1.0, 2.6)
    hy = -0.42
    for k, (x, y, s) in enumerate(((-0.2, 0.66, 1.0), (0.24, 0.73, 0.82), (0.55, 0.8, 0.7))):
        tw = wave(t, 2, k * 0.33)
        p.sparkle(x, y, 0.13 * s * (0.8 + 0.3 * tw), int(170 + 85 * tw), rot=10 * tw)
        p.dot(x, y, 2.2 * s, "accent", 255)
    crescent(p, -0.6, 0.48, 0.09, 30, 0.55, "ink")
    pyr = [(0.62, 0.28, 0.24, -0.36), (0.25, 0.42, 0.44, -0.39), (-0.32, 0.56, 0.58, -0.44)]
    for cx, hw, h, by in pyr:
        apex = (cx, by + h)
        fx = cx + hw * 0.25
        left = [(cx - hw, by), (fx, by), apex]
        right = [(fx, by), (cx + hw, by), apex]
        p.poly(left, "fill")
        p.poly(right, "fill")
        p.poly(left, "ink", 50, occlude=False)
        for j in range(1, 8):
            yy = by + h * j / 8
            k = j / 8
            p.line([(lerp(cx - hw, cx, k), yy), (lerp(fx, cx, k), yy)], 1.0, "ink", 110)
        p.line(left + [right[1]], 2.2, closed=False)
        p.line([right[1], apex], 2.2)
        p.line([(fx, by), apex], 1.4, "ink", 200)
    big = pyr[2]
    ap = (big[0], big[3] + big[2])
    beam = wave(t, 1)
    p.ray(*ap, 90, 0.02, 1.25, 0.03, 0.34, int(120 + 135 * beam))
    p.ray(*ap, 90, 0.02, 1.4, 0.012, 0.08, int(160 + 95 * beam))
    p.glow(*ap, 0.12 + 0.05 * beam, 255)
    p.disc(*ap, 0.03, "accent", 255, occlude=False)
    p.line([(-0.92, hy), (0.92, hy)], 2.0)
    for r, y in enumerate((-0.55, -0.67, -0.79)):
        hwid = math.sqrt(max(0.0, 0.98 ** 2 - y * y)) - 0.04
        off = (t + r * 0.33) % 1
        x = -hwid + (off - 1) * 0.3
        while x < hwid:
            x0, x1 = max(-hwid, x), min(hwid, x + 0.16)
            if x1 > x0:
                p.line([(x0, y), (x1, y + 0.01)], 1.2, "ink", 150)
            x += 0.3


@sigil("eleusis", "The Eleusinian Ear of Grain", "Eleusinian Mysteries", 4,
       "An ear of wheat reaped in silence between the torches of Demeter and Persephone: the final revelation of Eleusis",
       rings=("Greek Alphabet", "Zodiac"))
def eleusis(p, t, v):
    for side in (-1, 1):
        x = side * 0.62
        shaft = [(x - 0.03, -0.9), (x + 0.03, -0.9), (x + 0.07, 0.12), (x - 0.07, 0.12)]
        p.poly(shaft, "fill")
        p.line(shaft, 2.0, closed=True)
        for j in range(4):
            y = -0.7 + 0.22 * j
            p.line([(x - 0.045, y), (x + 0.045, y + 0.05)], 1.2, "ink", 180)
        cup = [(x - 0.11, 0.12), (x + 0.11, 0.12), (x + 0.08, 0.2), (x - 0.08, 0.2)]
        p.poly(cup, "fill")
        p.line(cup, 1.8, closed=True)
        for k, (sc, layer, vv) in enumerate(((1.0, "accent", 170), (0.6, "ink", 255))):
            tip = (x + 0.05 * math.sin(TAU * (2 * t + side * 0.25)), 0.2 + 0.46 * sc * (1 + 0.12 * math.sin(TAU * (3 * t + side * 0.3 + k * 0.5))))
            flame = bezier3((x - 0.1 * sc, 0.2), (x - 0.12 * sc, 0.32 * sc + 0.2), (tip[0] - 0.04, tip[1] - 0.15 * sc), tip, 16) + \
                bezier3(tip, (tip[0] + 0.03, tip[1] - 0.2 * sc), (x + 0.13 * sc, 0.3 * sc + 0.2), (x + 0.1 * sc, 0.2), 16)[1:]
            p.poly(flame, layer, vv, occlude=False)
        p.glow(x, 0.4, 0.3, int(190 + 65 * wave(t, 3, side * 0.2)))
    sway = 2.5 * math.sin(TAU * t)
    p.glow(0.03, 0.42, 0.42, int(110 + 50 * wave(t, 3)), "light")
    with p.tf(dy=-0.95, rot=sway):
        # culm with two nodes
        stalk = bezier3((0, 0), (0.0, 0.5), (0.04, 0.9), (0.03, 1.2), 40)
        p.poly(thick(stalk, [lerp(0.03, 0.018, i / 40) for i in range(41)]), "fill")
        p.poly(thick(stalk, [lerp(0.03, 0.018, i / 40) for i in range(41)]), "ink", 50, occlude=False)
        p.line(thick(stalk, [lerp(0.03, 0.018, i / 40) for i in range(41)]), 1.2, closed=True)
        for nu in (0.32, 0.62):
            q = path_point(stalk, nu)
            p.line([(q[0] - 0.022, q[1]), (q[0] + 0.022, q[1] + 0.008)], 1.6, "ink", 230)
        # lanceolate leaves curling away from the nodes
        for side, nu, reach, droop in ((-1, 0.32, 0.5, 0.25), (1, 0.62, 0.42, 0.2), (1, 0.12, 0.36, 0.3)):
            b0 = path_point(stalk, nu)
            leaf = bezier3(b0, (b0[0] + side * 0.05, b0[1] + 0.25), (b0[0] + side * reach * 0.8, b0[1] + 0.42),
                           (b0[0] + side * reach, b0[1] + 0.3 - droop + 0.02 * math.sin(TAU * t + side)), 30)
            w_ = [0.055 * math.sin(math.pi * min(1.0, (i / 30) * 1.15)) ** 0.7 + 0.002 for i in range(31)]
            lp = thick(leaf, w_)
            p.poly(lp, "fill")
            p.poly(lp, "ink", 45, occlude=False)
            p.line(lp, 1.1, closed=True)
            p.line(leaf[2:-3], 0.6, "ink", 170)
        # the ear: rachis nodding slightly, spikelets in two alternating rows
        rach = bezier3((0.03, 1.18), (0.035, 1.4), (0.06, 1.6), (0.1, 1.78), 30)
        spikes = []
        for j in range(13):
            u = j / 12
            q = path_point(rach, 0.02 + 0.92 * u)
            q2 = path_point(rach, min(1.0, 0.02 + 0.92 * u + 0.02))
            ang = math.degrees(math.atan2(q2[1] - q[1], q2[0] - q[0]))
            side = 1 if j % 2 else -1
            size = 0.105 * (1 - 0.45 * u) + 0.02
            spikes.append((q, ang, side, size, u))
        # awns first (behind): long, fine, curving outward and up
        for q, ang, side, size, u in spikes:
            a_ = ang - 90 + side * (-28)
            tip = polar(size * 0.95, a_ + 90, *q)
            L_ = 0.2 + 0.3 * math.sin(math.pi * (0.25 + 0.7 * u))
            flutter = 3 * math.sin(TAU * (t * 2 + u))
            aw = bezier(tip, polar(L_ * 0.5, a_ + 90 - side * 3, *tip), polar(L_, a_ + 90 - side * (9 + flutter), *tip), 12)
            p.line(aw, 0.7, "ink", 200)
        for q, ang, side, size, u in spikes:
            a_ = ang - 90 + side * (-28)
            with p.tf(dx=q[0], dy=q[1], rot=a_):
                for dx_, sc in ((side * 0.012, 0.9), (0.0, 1.0)):  # two florets per spikelet
                    g = [(dx_ + size * 0.36 * sc * math.sin(math.pi * h_) ** 0.75 * (1 - 0.3 * h_), size * sc * h_) for h_ in (i_ / 20 for i_ in range(21))] + \
                        [(dx_ - size * 0.36 * sc * math.sin(math.pi * h_) ** 0.75 * (1 - 0.3 * h_), size * sc * h_) for h_ in (i_ / 20 for i_ in range(20, -1, -1))]
                    p.poly(g, "fill")
                    p.poly(g, "ink", 70, occlude=False)
                    p.line(g, 1.1, closed=True)
                    p.line([(dx_, size * sc * 0.15), (dx_ + size * 0.04, size * sc * 0.85)], 0.6, "ink", 170)
        p.line(rach, 1.4, "ink", 220)
        p.sparkle(*path_point(rach, 1.0), 0.06, int(150 + 100 * wave(t, 2)))


@sigil("orphic_egg", "The Orphic Egg", "Orphic Mysteries", 5,
       "The cosmic egg of the Orphics with the serpent of creation coiled about it, from which Phanes, the first-born light, broke forth",
       rings=("Greek Alphabet", "Zodiac", "Planetary Metals"))
def orphic_egg(p, t, v):
    cy, rx, ry = -0.06, 0.5, 0.74
    half = lambda y: rx * math.sqrt(max(0.0, 1 - ((y - cy) / ry) ** 2)) * (1 - 0.12 * (y - cy) / ry)  # noqa: E731
    egg = [(rx * math.sin(s) * (1 - 0.12 * math.cos(s)), cy + ry * math.cos(s)) for s in (TAU * i / 180 for i in range(180))]
    y_bot, y_top, turns = -0.66, 0.6, 2.25
    pts, dep, wid = [], [], []
    for i in range(241):
        u = i / 240
        y = lerp(y_bot, y_top, u)
        th = TAU * (turns * u + t)
        hw = half(y) + 0.07
        pts.append((hw * math.sin(th), y + 0.11 * math.cos(th)))
        dep.append(math.cos(th))
        wid.append(lerp(0.004, 0.17, min(1.0, u * 1.5) ** 0.8) * (1 - 0.25 * max(0, u - 0.88) / 0.12))
    runs, idx = [], 0
    for front, run in helix_runs(pts, dep):
        runs.append((front, run, wid[idx:idx + len(run)]))
        idx += len(run) - 1
    for front, run, w in runs:
        if not front:
            serpent_run(p, run, w, front=False)
    p.poly(egg, "fill")
    for k in range(1, 6):
        y = cy - ry + 2 * ry * k / 6
        h = half(y)
        p.line([(h * math.cos(a), y + 0.04 * math.sin(a)) for a in (math.pi * j / 30 for j in range(31))], 1.0, "faint", 255)
    p.line(egg, 2.8, closed=True)
    p.disc(0, cy, 0.05 * (1 + 0.5 * wave(t, 2)), "accent", 200, occlude=False)
    p.glow(0, cy, 0.3, int(120 + 70 * wave(t, 2)))
    for front, run, w in runs:
        if front:
            serpent_run(p, run, w, lw=2.0)
    x, y = pts[-1]
    x0, y0 = pts[-6]
    heading = math.degrees(math.atan2(y - y0, x - x0))
    snake_head_top(p, x, y, lerp(heading, 90, 0.6), wid[-1], t)
