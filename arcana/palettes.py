"""The "Opus" trait — each palette is named for a stage or substance of the
alchemical Great Work. Colours are RGB 0-255."""

GOLD = ((255, 230, 160), (178, 122, 46))

PALETTES = {
    "Nigredo": dict(
        weight=16, kind="dark", bg=((30, 25, 22), (5, 4, 5)), ink=GOLD,
        accent=(236, 226, 205), glow=(255, 176, 80), glow_k=0.55, fill=(12, 10, 10),
        faint=(196, 150, 80), stars=(255, 236, 200), nebula=(120, 70, 30),
        lore="the blackening, where every matter is first dissolved"),
    "Lapis Lazuli": dict(
        weight=13, kind="dark", bg=((30, 48, 122), (5, 9, 36)), ink=GOLD,
        accent=(150, 210, 255), glow=(255, 196, 110), glow_k=0.5, fill=(14, 24, 74),
        faint=(220, 180, 100), stars=(255, 214, 130), nebula=(60, 90, 200),
        lore="ground lapis, the stone of the night sky and of Egyptian heaven"),
    "Rubedo": dict(
        weight=10, kind="dark", bg=((118, 18, 24), (28, 4, 8)), ink=((255, 238, 186), (204, 140, 56)),
        accent=(255, 248, 232), glow=(255, 120, 60), glow_k=0.55, fill=(62, 8, 12),
        faint=(255, 170, 110), stars=(255, 220, 190), nebula=(200, 40, 30),
        lore="the reddening, the last stage, the Stone made perfect"),
    "Viriditas": dict(
        weight=10, kind="dark", bg=((14, 86, 62), (2, 20, 16)), ink=GOLD,
        accent=(190, 255, 214), glow=(240, 214, 110), glow_k=0.5, fill=(6, 44, 32),
        faint=(200, 220, 140), stars=(220, 255, 220), nebula=(40, 160, 110),
        lore="the greening power, the colour of the Emerald Tablet"),
    "Albedo": dict(
        weight=11, kind="dark", bg=((48, 56, 72), (9, 11, 17)), ink=((246, 249, 255), (132, 142, 166)),
        accent=(170, 214, 255), glow=(196, 220, 255), glow_k=0.55, fill=(18, 22, 32),
        faint=(170, 190, 220), stars=(230, 240, 255), nebula=(90, 110, 160),
        lore="the whitening, the lunar washing of the matter"),
    "Citrinitas": dict(
        weight=8, kind="dark", bg=((124, 78, 12), (32, 17, 4)), ink=((255, 252, 214), (234, 182, 60)),
        accent=(255, 255, 255), glow=(255, 214, 90), glow_k=0.55, fill=(58, 34, 6),
        faint=(255, 220, 140), stars=(255, 246, 200), nebula=(220, 150, 30),
        lore="the yellowing, the dawn of the solar light within the work"),
    "Folio": dict(
        weight=12, kind="paper", bg=((236, 220, 182), (170, 138, 92)), ink=((66, 42, 26), (30, 18, 12)),
        accent=(170, 42, 28), glow=(120, 74, 36), glow_k=0.22, fill=(238, 224, 188),
        faint=(120, 86, 52), stars=None, nebula=(150, 100, 50),
        lore="iron-gall ink on rag paper, as the old plates were printed"),
    "Tyrian Purple": dict(
        weight=7, kind="dark", bg=((76, 18, 78), (16, 4, 20)), ink=GOLD,
        accent=(255, 176, 224), glow=(255, 176, 120), glow_k=0.5, fill=(36, 8, 40),
        faint=(230, 170, 200), stars=(255, 220, 240), nebula=(150, 50, 160),
        lore="the dye of emperors and hierophants"),
    "Vermilion": dict(
        weight=6, kind="dark", bg=((18, 16, 18), (2, 2, 3)), ink=((255, 120, 70), (176, 34, 20)),
        accent=(255, 226, 190), glow=(255, 64, 30), glow_k=0.6, fill=(8, 6, 6),
        faint=(220, 70, 40), stars=(255, 170, 140), nebula=(140, 20, 10),
        lore="cinnabar, the red sulphide of mercury"),
    "Verdigris": dict(
        weight=5, kind="dark", bg=((22, 74, 76), (4, 18, 20)), ink=((255, 196, 156), (186, 96, 56)),
        accent=(130, 245, 225), glow=(255, 150, 100), glow_k=0.5, fill=(8, 36, 38),
        faint=(140, 220, 200), stars=(200, 255, 245), nebula=(40, 150, 140),
        lore="copper and its green rust, the metal of Venus"),
    "Cauda Pavonis": dict(
        weight=2, kind="dark", bg=((12, 16, 28), (2, 3, 6)), ink="iridescent",
        accent=(255, 255, 255), glow="iridescent", glow_k=0.6, fill=(6, 8, 14),
        faint=(150, 170, 220), stars=(220, 230, 255), nebula=(80, 60, 160),
        lore="the peacock's tail, the iridescence that heralds the Stone"),
}
