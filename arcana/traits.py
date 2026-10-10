"""Deterministic trait rolls. A token's traits depend only on (collection
seed, token id), and duplicates are resolved by rolling the whole supply in
id order — so a 24-piece preview and the full run agree on every token."""
import hashlib
import math
import random

from .layers import FRAMES, HALOS, MOTTOS, RINGS
from .palettes import PALETTES
from .sigils import SIGILS

AFFINITY = 4.0  # weight multiplier for rings that belong to the figure's tradition


def roman(n):
    out = ""
    for v, s in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                 (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += s
            n -= v
    return out


def pick(rng, table):
    keys = list(table)
    return rng.choices(keys, weights=[table[k] for k in keys])[0]


def roll(token_id, seed, salt=0):
    rng = random.Random(f"{seed}:{token_id}:{salt}")
    sig = SIGILS[pick(rng, {k: s["weight"] for k, s in SIGILS.items()})]
    variant = pick(rng, dict(sig["variants"])) if sig["variants"] else None
    opus = pick(rng, {k: p["weight"] for k, p in PALETTES.items()})
    halo = pick(rng, {k: w for k, (w, _) in HALOS.items()})
    ring_w = {k: r["weight"] * (AFFINITY if k in sig["rings"] else 1.0) for k, r in RINGS.items()}
    ring = pick(rng, ring_w)
    frame = pick(rng, {k: w for k, (w, _) in FRAMES.items()})
    mottos = {k: w for k, (w, _) in MOTTOS.items()}
    if sig["key"] == "ouroboros":
        mottos.pop("ΕΝ ΤΟ ΠΑΝ")  # already written inside the serpent
    motto = pick(rng, mottos)
    traits = {"Mystery": sig["name"], "Tradition": sig["tradition"]}
    if variant:
        traits["Form"] = variant
    traits.update({"Opus": opus, "Halo": halo, "Glyph Ring": ring, "Frame": frame, "Motto": motto})
    return dict(id=token_id, sigil=sig["key"], variant=variant, traits=traits,
                roman=roman(token_id),
                seed=int(hashlib.sha256(f"{seed}:{token_id}:{salt}".encode()).hexdigest()[:12], 16))


# Initiatory degrees, highest first: (name, number of plates at supply 777).
DEGREES = [("Hierophant", 7), ("Magus", 40), ("Adept", 110), ("Initiate", 220), ("Neophyte", 400)]
SCORED = ["Figure", "Opus", "Halo", "Glyph Ring", "Frame", "Motto"]


def _scored(t):
    tr = t["traits"]
    out = {k: tr[k] for k in SCORED if k in tr}
    out["Figure"] = tr["Mystery"] + (" / " + tr["Form"] if "Form" in tr else "")
    return out


def assign_degrees(toks):
    """Rank every token by trait rarity and slice the ranking into exact
    counts per degree, scaled to the supply. Each trait contributes its
    surprisal (-log frequency) divided by that trait's average surprisal,
    so every trait category weighs the same."""
    n = len(toks)
    vals = {tid: _scored(t) for tid, t in toks.items()}
    freq = {k: {} for k in SCORED}
    for v in vals.values():
        for k, x in v.items():
            freq[k][x] = freq[k].get(x, 0) + 1
    sur = {k: {x: -math.log(c / n) for x, c in freq[k].items()} for k in SCORED}
    mean = {k: sum(sur[k][v[k]] for v in vals.values()) / n for k in SCORED}
    score = {tid: sum(sur[k][x] / mean[k] for k, x in v.items()) for tid, v in vals.items()}
    ranked = sorted(toks, key=lambda i: (-score[i], i))
    total = sum(c for _, c in DEGREES)
    cuts, acc = [], 0
    for name, c in DEGREES:
        acc += c
        cuts.append((name, round(acc * n / total)))
    for pos, tid in enumerate(ranked):
        name = next(nm for nm, cut in cuts if pos < cut)
        toks[tid]["traits"]["Degree"] = name
        toks[tid]["degree_level"] = len(DEGREES) - [d for d, _ in DEGREES].index(name)
        toks[tid]["rarity"] = round(score[tid], 3)
        toks[tid]["rank"] = pos + 1


def roll_collection(supply, seed):
    seen, out = set(), {}
    for tid in range(1, supply + 1):
        salt = 0
        while True:
            tok = roll(tid, seed, salt)
            sig = tuple(sorted(tok["traits"].items()))
            if sig not in seen:
                break
            salt += 1
        seen.add(sig)
        out[tid] = tok
    assign_degrees(out)
    return out


def describe(tok):
    sig = SIGILS[tok["sigil"]]
    tr = tok["traits"]
    pal = PALETTES[tr["Opus"]]
    lines = [f"{sig['lore']}.", f"Struck in {tr['Opus']}: {pal['lore']}."]
    if "Degree" in tr:
        lines.append(f"Degree of {tr['Degree']}, rank {tok['rank']} of the folio.")
    if tr["Motto"] != "None":
        lines.append(f"“{tr['Motto']}”: {MOTTOS[tr['Motto']][1]}.")
    return " ".join(lines)


def token_name(tok):
    return f"Plate {tok['roman']}: {tok['traits']['Mystery']}"
