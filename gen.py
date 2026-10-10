#!/usr/bin/env python3
"""Codex Arcanum: generate animated GIF plates + NFT metadata.

  python3 gen.py                         # 36-plate preview into out/
  python3 gen.py --count 777             # full run
  python3 gen.py --only 7 42 108         # re-render specific plates
  python3 gen.py --all-figures           # one plate per figure/form (QA sheet)
"""
import argparse
import csv
import html
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

from PIL import Image

from arcana import draw_plate
from arcana.render import render_frames, save_gif
from arcana.sigils import SIGILS
from arcana.traits import describe, roll_collection, token_name

COLLECTION = "Codex Arcanum"
TRAIT_ORDER = ["Mystery", "Tradition", "Form", "Opus", "Halo", "Glyph Ring", "Frame", "Motto"]


def parse():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--supply", type=int, default=777, help="collection size used for trait rolls (default 777)")
    ap.add_argument("--count", type=int, default=36, help="how many plates to render, from --start")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--only", type=int, nargs="*", help="render just these token ids")
    ap.add_argument("--all-figures", action="store_true", help="pick one token per figure/form for QA")
    ap.add_argument("--seed", default="codex-arcanum-1928")
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--delay", type=int, default=70, help="ms per frame (GIF stores 10ms steps)")
    ap.add_argument("--lossy", type=int, default=30, help="gifsicle --lossy level (0 = lossless)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--out", default="out")
    ap.add_argument("--base-uri", default="ipfs://REPLACE_WITH_IMAGES_CID/",
                    help="prefix for the image field in each token JSON")
    return ap.parse_args()


def render_one(job):
    tok, a = job
    frames = render_frames(tok, a["size"], a["frames"], draw_fn=draw_plate)
    path = os.path.join(a["out"], f"{tok['id']}.gif")
    save_gif(frames, path, a["delay"], a["lossy"])
    thumb = frames[0].copy()
    thumb.thumbnail((256, 256), Image.LANCZOS)
    thumb.save(os.path.join(a["out"], "thumbs", f"{tok['id']}.png"))
    return tok["id"], os.path.getsize(path)


def attributes(tok):
    return [{"trait_type": k, "value": tok["traits"][k]} for k in TRAIT_ORDER if k in tok["traits"]]


def write_metadata(toks, a):
    for tok in toks:
        meta = {
            "name": token_name(tok),
            "description": describe(tok),
            "image": f"{a.base_uri}{tok['id']}.gif",
            "attributes": attributes(tok),
        }
        with open(os.path.join(a.out, f"{tok['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    # OpenSea Studio CSV schema (same layout as rot-gen's drop/)
    with open(os.path.join(a.out, "metadata.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tokenID", "name", "description", "file_name"] + [f"attributes[{k}]" for k in TRAIT_ORDER])
        for tok in toks:
            w.writerow([tok["id"], token_name(tok), describe(tok), f"{tok['id']}.gif"] +
                       [tok["traits"].get(k, "") for k in TRAIT_ORDER])


def write_gallery(toks, a):
    cards = []
    for tok in toks:
        tr = "".join(f"<li><b>{html.escape(k)}</b> {html.escape(tok['traits'][k])}</li>"
                     for k in TRAIT_ORDER if k in tok["traits"])
        cards.append(f'<figure><img loading="lazy" src="{tok["id"]}.gif" width="256" height="256" alt="">'
                     f'<figcaption><h2>{html.escape(token_name(tok))}</h2><ul>{tr}</ul>'
                     f'<p>{html.escape(describe(tok))}</p></figcaption></figure>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{COLLECTION}</title>
<style>
body{{margin:0;background:#0b0907;color:#e9dcc0;font:14px/1.45 Georgia,serif}}
header{{padding:28px 20px 8px;text-align:center}} h1{{font-weight:400;letter-spacing:.3em;margin:0}}
header p{{opacity:.6;margin:.4em 0 0}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:18px;padding:20px}}
figure{{margin:0;background:#15110d;border:1px solid #3a2e1f;padding:7px}}
img{{width:100%;height:auto;display:block;image-rendering:auto}}
h2{{font-size:15px;font-weight:400;margin:8px 0 4px;color:#f3d98e}}
ul{{list-style:none;padding:0;margin:0;font-size:12px;columns:2}} li b{{opacity:.55;font-weight:400}}
figcaption p{{font-size:12px;opacity:.7;margin:6px 0 2px}}
</style></head><body><header><h1>{COLLECTION.upper()}</h1>
<p>{len(toks)} plates rendered · supply {a.supply}</p></header><main>{''.join(cards)}</main></body></html>"""
    with open(os.path.join(a.out, "gallery.html"), "w", encoding="utf-8") as f:
        f.write(page)


def write_sheet(toks, a):
    ims = []
    for tok in toks:
        pth = os.path.join(a.out, "thumbs", f"{tok['id']}.png")
        if os.path.exists(pth):
            ims.append(Image.open(pth))
    if not ims:
        return
    cols = 6
    S = ims[0].width
    sheet = Image.new("RGB", (cols * S, ((len(ims) + cols - 1) // cols) * S))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * S, (i // cols) * S))
    sheet.save(os.path.join(a.out, "contact-sheet.png"))


def main():
    a = parse()
    os.makedirs(os.path.join(a.out, "thumbs"), exist_ok=True)
    allt = roll_collection(a.supply, a.seed)
    if a.only:
        ids = [i for i in a.only if i in allt]
    elif a.all_figures:
        want, ids = set(), []
        for k, s in SIGILS.items():
            for v in [v for v, _ in s["variants"]] or [None]:
                want.add((k, v))
        for tid, tok in allt.items():
            if (tok["sigil"], tok["variant"]) in want:
                want.discard((tok["sigil"], tok["variant"]))
                ids.append(tid)
        if want:
            print("not present in this supply:", sorted(f"{k}/{v}" for k, v in want))
    else:
        ids = [i for i in range(a.start, a.start + a.count) if i in allt]
    toks = [allt[i] for i in ids]
    job_args = dict(size=a.size, frames=a.frames, delay=a.delay, lossy=a.lossy, out=a.out)
    t0 = time.time()
    total = 0
    with ProcessPoolExecutor(a.workers) as ex:
        for n, (tid, size) in enumerate(ex.map(render_one, [(t, job_args) for t in toks]), 1):
            total += size
            print(f"[{n}/{len(toks)}] #{tid} {allt[tid]['traits']['Mystery']} ({size / 1e6:.2f} MB)", flush=True)
    write_metadata(toks, a)
    write_gallery(toks, a)
    write_sheet(toks, a)
    print(f"{len(toks)} plates, {total / 1e6:.1f} MB, {time.time() - t0:.0f}s -> {a.out}/")


if __name__ == "__main__":
    main()
