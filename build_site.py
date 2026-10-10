#!/usr/bin/env python3
"""Build the GitHub Pages site into docs/.

  python3 build_site.py            # render showcase plates (skips existing) + write site
  python3 build_site.py --fresh    # re-render every showcase plate

Showcase = the first 36 tokens plus one token per figure/form, so every
Mystery has a live plate on the site. Rarity numbers come from the full
777-token roll, not just the showcase.
"""
import argparse
import glob
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from arcana.layers import MOTTOS
from arcana.palettes import PALETTES
from arcana.sigils import SIGILS
from arcana.hierophants import ONE_OF_ONE
from arcana.traits import DEGREES, describe, roll_collection, token_name
from gen import TRAIT_ORDER, render_one

SEED = "codex-arcanum-1928"
SUPPLY = 777
SITE_URL = "https://m4s4t0-v01d.github.io/codex-arcanum/"
REPO_URL = "https://github.com/M4S4T0-V01D/codex-arcanum"
GATE_URL = "https://codex-arcanum-gate.masato-void.workers.dev"  # the gate worker (gate-worker/)
DOCS = "docs"
PLATES = os.path.join(DOCS, "plates")


def showcase_ids(allt):
    ids = list(range(1, 37)) + [i for i, t in allt.items() if t.get("one") and i > 36]
    want = {(k, v) for k, s in SIGILS.items() if not s.get("one") for v in ([v for v, _ in s["variants"]] or [None])}
    figure_pick = {}
    for tid, tok in allt.items():
        key = (tok["sigil"], tok["variant"])
        if key in want:
            want.discard(key)
            figure_pick[key] = tid
            if tid not in ids:
                ids.append(tid)
    opus_pick = {}
    for tid, tok in allt.items():
        o = tok["traits"]["Opus"]
        if o not in opus_pick and not tok.get("one"):
            # prefer a plate already in the showcase
            inside = next((i for i in ids if allt[i]["traits"]["Opus"] == o and not allt[i].get("one")), None)
            opus_pick[o] = inside or tid
            if opus_pick[o] not in ids:
                ids.append(opus_pick[o])
    return sorted(ids), figure_pick, opus_pick


def small_mp4(src, dst, size=360, crf=26):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", f"scale={size}:{size}:flags=lanczos",
                    "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", "-an", dst], check=True)


def poster(src_png, dst, size=540):
    im = Image.open(src_png).convert("RGB")
    im.thumbnail((size, size), Image.LANCZOS)
    im.save(dst, quality=88, optimize=True)


def card_stats(tok):
    """Side values (top, right, bottom, left) for the Game of Thoth, 1-9
    (10 written as A). Total power rises with the initiatory degree."""
    if tok.get("one"):
        return [9, 10, 9, 8] if tok["id"] % 2 else [10, 8, 9, 9]  # the Hierophants: mighty, never perfect
    rng = random.Random(f"thoth:{tok['id']}")
    lvl = tok["degree_level"]  # 1 Neophyte .. 5 Hierophant
    total = rng.randint(14, 17) + 3 * (lvl - 1)
    cap = 10 if lvl == 5 else 9
    sides = [1, 1, 1, 1]
    while sum(sides) < total:
        i = rng.randrange(4)
        if sides[i] < cap:
            sides[i] += 1
    return sides


def og_image(ids, out):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), (10, 8, 6))
    d = ImageDraw.Draw(im)
    for i, tid in enumerate(ids[:3]):
        th = Image.open(os.path.join(PLATES, "poster", f"{tid}.jpg")).convert("RGB").resize((330, 330), Image.LANCZOS)
        im.paste(th, (60 + i * 365, 230))
    glow = Image.new("L", (W, H), 0)
    f = ImageFont.truetype("/usr/share/fonts/noto/NotoSerifDisplay-Medium.ttf", 92)
    fs = ImageFont.truetype("/usr/share/fonts/noto/NotoSerif-Regular.ttf", 28)
    title = "C O D E X   A R C A N V M"
    ImageDraw.Draw(glow).text((W / 2, 110), title, font=f, fill=255, anchor="mm")
    im.paste((255, 176, 80), (0, 0), glow.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.5)))
    d.text((W / 2, 110), title, font=f, fill=(240, 212, 140), anchor="mm")
    d.text((W / 2, 188), "the cyber temple of Hermes Trismegistus  ·  777 animated plates", font=fs, fill=(200, 184, 150), anchor="mm")
    d.rectangle((20, 20, W - 21, H - 21), outline=(120, 92, 48), width=2)
    im.save(out, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()

    allt = roll_collection(SUPPLY, SEED)
    ids, figure_pick, opus_pick = showcase_ids(allt)
    os.makedirs(os.path.join(PLATES, "thumbs"), exist_ok=True)
    os.makedirs(os.path.join(PLATES, "sm"), exist_ok=True)

    os.makedirs(os.path.join(PLATES, "poster"), exist_ok=True)
    todo = [allt[i] for i in ids if a.fresh or not os.path.exists(os.path.join(PLATES, f"{i}.mp4"))]
    job = dict(size=1080, frames=105, fps=25, ss=2, crf=18, gif_size=0, lossy=0, out=PLATES)
    with ProcessPoolExecutor(a.workers) as ex:
        for n, (tid, sizes) in enumerate(ex.map(render_one, [(t, job) for t in todo]), 1):
            print(f"[{n}/{len(todo)}] plate {tid} (mp4 {sizes['.mp4'] / 1e6:.1f} MB)", flush=True)
    for i in ids:
        png, smp = os.path.join(PLATES, f"{i}.png"), os.path.join(PLATES, "sm", f"{i}.mp4")
        if os.path.exists(png):
            poster(png, os.path.join(PLATES, "poster", f"{i}.jpg"))
            os.remove(png)  # the full PNG stays out of the site; posters are enough
        if a.fresh or not os.path.exists(smp):
            small_mp4(os.path.join(PLATES, f"{i}.mp4"), smp)
    # drop media from the old GIF-based site
    for pat in ("*.gif", "sm/*.gif", "thumbs/*.png"):
        for old in glob.glob(os.path.join(PLATES, pat)):
            os.remove(old)

    # token metadata for the showcase (same JSON as gen.py writes)
    meta_dir = os.path.join(DOCS, "metadata")
    os.makedirs(meta_dir, exist_ok=True)
    for i in ids:
        tok = allt[i]
        with open(os.path.join(meta_dir, f"{i}.json"), "w", encoding="utf-8") as f:
            json.dump({"name": token_name(tok), "description": describe(tok),
                       "image": f"{SITE_URL}plates/poster/{i}.jpg",
                       "animation_url": f"{SITE_URL}plates/{i}.mp4",
                       "attributes": [{"trait_type": k, "value": tok["traits"][k]}
                                      for k in TRAIT_ORDER if k in tok["traits"]]},
                      f, ensure_ascii=False, indent=2)

    # full-supply trait manifest + provenance hash
    manifest = [{"id": t["id"], **t["traits"]} for t in allt.values()]
    canon = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    prov = hashlib.sha256(canon.encode()).hexdigest()
    with open(os.path.join(DOCS, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"collection": "Codex Arcanum", "supply": SUPPLY, "seed": SEED,
                   "sha256": prov, "tokens": manifest}, f, ensure_ascii=False)

    counts = {k: Counter(t["traits"].get(k) for t in allt.values() if k in t["traits"]) for k in TRAIT_ORDER}
    data = {
        "supply": SUPPLY, "seed": SEED, "provenance": prov, "repo": REPO_URL,
        "counts": {k: dict(c.most_common()) for k, c in counts.items()},
        "degrees": [{"name": n, "count": counts["Degree"][n]} for n, _ in DEGREES],
        "tokens": [{"id": i, "name": token_name(allt[i]), "desc": describe(allt[i]), "rank": allt[i]["rank"],
                    "level": allt[i]["degree_level"], "card": card_stats(allt[i]),
                    "traits": {k: allt[i]["traits"][k] for k in TRAIT_ORDER if k in allt[i]["traits"]}}
                   for i in ids],
        "mysteries": [{"key": k, "name": s["name"], "tradition": s["tradition"], "lore": s["lore"],
                       "forms": [v for v, _ in s["variants"]],
                       "plate": next((figure_pick[(k, v)] for v in ([v for v, _ in s["variants"]] or [None])
                                      if (k, v) in figure_pick), None),
                       "count": counts["Mystery"][s["name"]]} for k, s in SIGILS.items() if not s.get("one")],
        "hierophants": [{"id": i, "key": allt[i]["sigil"], "name": SIGILS[allt[i]["sigil"]]["name"],
                         "tradition": allt[i]["traits"]["Tradition"], "opus": allt[i]["traits"]["Opus"],
                         "lore": SIGILS[allt[i]["sigil"]]["lore"]} for i in sorted(ONE_OF_ONE)],
        "opus": [{"name": n, "lore": p["lore"], "count": counts["Opus"][n], "plate": opus_pick[n],
                  "bg": ["#%02x%02x%02x" % c for c in p["bg"]],
                  "ink": None if p["ink"] == "iridescent" else ["#%02x%02x%02x" % c for c in p["ink"]],
                  "accent": "#%02x%02x%02x" % p["accent"]} for n, p in PALETTES.items() if not p.get("one")],
        "mottos": {k: v[1] for k, v in MOTTOS.items() if v[1]},
    }
    hero = [t for t in (7, 30, 108, 4, 23, 144, 32, 13, 432, 1, 31, 333, 25, 42, 777) if t in ids]
    data["hero"] = hero
    # frame strips for the animated share card: 42 frames of each plate it may use, 7x6 grid at 330px
    os.makedirs(os.path.join(PLATES, "strip"), exist_ok=True)
    for i in sorted(set(hero) | set(ONE_OF_ONE)):
        dst = os.path.join(PLATES, "strip", f"{i}.jpg")
        if a.fresh or not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(os.path.join(PLATES, f"{i}.mp4")):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(PLATES, f"{i}.mp4"),
                            "-vf", "fps=10,scale=330:330:flags=lanczos,tile=7x6", "-frames:v", "1", "-q:v", "4", dst], check=True)
    og_image([hero[0], hero[1], hero[2]], os.path.join(DOCS, "og.png"))

    # the Game of Thoth: one card pool for the site and the gate worker, one engine for both
    pool = [{"id": t["id"], "name": t["name"], "sides": t["card"], "level": t["level"]} for t in data["tokens"]]
    with open("gate-worker/src/cards.json", "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False)
    with open("site/thoth-engine.js", encoding="utf-8") as f:
        engine = re.sub(r"^export ", "", f.read(), flags=re.M)

    with open("site/index.template.html", encoding="utf-8") as f:
        page = f.read()
    page = page.replace("/*__ENGINE__*/", engine).replace("__GATE_URL__", GATE_URL)
    page = page.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    page = page.replace("__SITE_URL__", SITE_URL).replace("__REPO_URL__", REPO_URL)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    shutil.copy("site/favicon.svg", os.path.join(DOCS, "favicon.svg"))
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(DOCS) for f in fs)
    print(f"site: {len(ids)} plates, {total / 1e6:.0f} MB in {DOCS}/  provenance {prov[:16]}…")


if __name__ == "__main__":
    main()
