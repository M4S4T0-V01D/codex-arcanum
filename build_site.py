#!/usr/bin/env python3
"""Build the GitHub Pages site into docs/.

  python3 build_site.py            # render showcase plates (skips existing) + write site
  python3 build_site.py --fresh    # re-render every showcase plate

Showcase = the first 36 tokens plus one token per figure/form, so every
Mystery has a live plate on the site. Rarity numbers come from the full
777-token roll, not just the showcase.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from arcana.layers import MOTTOS
from arcana.palettes import PALETTES
from arcana.sigils import SIGILS
from arcana.traits import describe, roll_collection, token_name
from gen import TRAIT_ORDER, render_one

SEED = "codex-arcanum-1928"
SUPPLY = 777
SITE_URL = "https://m4s4t0-v01d.github.io/codex-arcanum/"
REPO_URL = "https://github.com/M4S4T0-V01D/codex-arcanum"
DOCS = "docs"
PLATES = os.path.join(DOCS, "plates")


def showcase_ids(allt):
    ids = list(range(1, 37))
    want = {(k, v) for k, s in SIGILS.items() for v in ([v for v, _ in s["variants"]] or [None])}
    figure_pick = {}
    for tid, tok in allt.items():
        key = (tok["sigil"], tok["variant"])
        if key in want:
            want.discard(key)
            figure_pick[key] = tid
            if tid not in ids:
                ids.append(tid)
    return sorted(ids), figure_pick


def small_gif(src, dst):
    subprocess.run(["gifsicle", "--resize", "256x256", "--colors", "256", "-O3", "--lossy=45",
                    src, "-o", dst], check=True)


def og_image(ids, out):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), (10, 8, 6))
    d = ImageDraw.Draw(im)
    for i, tid in enumerate(ids[:3]):
        th = Image.open(os.path.join(PLATES, "thumbs", f"{tid}.png")).convert("RGB").resize((330, 330), Image.LANCZOS)
        im.paste(th, (60 + i * 365, 230))
    glow = Image.new("L", (W, H), 0)
    f = ImageFont.truetype("/usr/share/fonts/noto/NotoSerifDisplay-Medium.ttf", 92)
    fs = ImageFont.truetype("/usr/share/fonts/noto/NotoSerif-Regular.ttf", 28)
    title = "C O D E X   A R C A N V M"
    ImageDraw.Draw(glow).text((W / 2, 110), title, font=f, fill=255, anchor="mm")
    im.paste((255, 176, 80), (0, 0), glow.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.5)))
    d.text((W / 2, 110), title, font=f, fill=(240, 212, 140), anchor="mm")
    d.text((W / 2, 188), "777 animated plates of the ancient mysteries", font=fs, fill=(200, 184, 150), anchor="mm")
    d.rectangle((20, 20, W - 21, H - 21), outline=(120, 92, 48), width=2)
    im.save(out, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()

    allt = roll_collection(SUPPLY, SEED)
    ids, figure_pick = showcase_ids(allt)
    os.makedirs(os.path.join(PLATES, "thumbs"), exist_ok=True)
    os.makedirs(os.path.join(PLATES, "sm"), exist_ok=True)

    todo = [allt[i] for i in ids if a.fresh or not os.path.exists(os.path.join(PLATES, f"{i}.gif"))]
    job = dict(size=512, frames=60, delay=70, lossy=30, out=PLATES)
    with ProcessPoolExecutor(a.workers) as ex:
        for n, (tid, size) in enumerate(ex.map(render_one, [(t, job) for t in todo]), 1):
            print(f"[{n}/{len(todo)}] plate {tid} ({size / 1e6:.2f} MB)", flush=True)
    for i in ids:
        sm = os.path.join(PLATES, "sm", f"{i}.gif")
        if a.fresh or not os.path.exists(sm):
            small_gif(os.path.join(PLATES, f"{i}.gif"), sm)

    # token metadata for the showcase (same JSON as gen.py writes)
    meta_dir = os.path.join(DOCS, "metadata")
    os.makedirs(meta_dir, exist_ok=True)
    for i in ids:
        tok = allt[i]
        with open(os.path.join(meta_dir, f"{i}.json"), "w", encoding="utf-8") as f:
            json.dump({"name": token_name(tok), "description": describe(tok),
                       "image": f"{SITE_URL}plates/{i}.gif",
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
        "tokens": [{"id": i, "name": token_name(allt[i]), "desc": describe(allt[i]),
                    "traits": {k: allt[i]["traits"][k] for k in TRAIT_ORDER if k in allt[i]["traits"]}}
                   for i in ids],
        "mysteries": [{"key": k, "name": s["name"], "tradition": s["tradition"], "lore": s["lore"],
                       "forms": [v for v, _ in s["variants"]],
                       "plate": next((figure_pick[(k, v)] for v in ([v for v, _ in s["variants"]] or [None])
                                      if (k, v) in figure_pick), None),
                       "count": counts["Mystery"][s["name"]]} for k, s in SIGILS.items()],
        "opus": [{"name": n, "lore": p["lore"], "count": counts["Opus"][n],
                  "bg": ["#%02x%02x%02x" % c for c in p["bg"]],
                  "ink": None if p["ink"] == "iridescent" else ["#%02x%02x%02x" % c for c in p["ink"]],
                  "accent": "#%02x%02x%02x" % p["accent"]} for n, p in PALETTES.items()],
        "mottos": {k: v[1] for k, v in MOTTOS.items() if v[1]},
    }
    hero = [t for t in (7, 30, 4, 23, 32, 13, 1, 31, 25, 36) if t in ids]
    data["hero"] = hero
    og_image([hero[0], hero[1], hero[2]], os.path.join(DOCS, "og.png"))

    with open("site/index.template.html", encoding="utf-8") as f:
        page = f.read()
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
