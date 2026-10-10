# Codex Arcanum

Animated GIF NFT collection: **777 "plates"** of symbols from the world's
mystery traditions, styled after the engraved folio plates of works like
Manly P. Hall's *The Secret Teachings of All Ages* (1928). Every plate is
drawn procedurally from geometry. No scans or artwork are copied, so the
images carry no third-party rights. Each GIF is a seamless 60-frame loop
(512×512, 70 ms/frame, ≈4.2 s) of about 1–3 MB.

```
python3 gen.py                    # 36-plate preview -> out/
python3 gen.py --count 777        # full collection (~15 min on 11 cores, ~1.6 GB)
python3 gen.py --only 7 42        # re-render specific plates
python3 gen.py --all-figures      # one plate per figure/form, for QA
python3 gen.py --base-uri ipfs://<CID>/   # set image URIs once uploaded
```

Output in `out/`: `<id>.gif`, `<id>.json` (ERC-721 / OpenSea metadata),
`metadata.csv` (OpenSea Studio upload schema, same as rot-gen),
`gallery.html` (local preview), `contact-sheet.png`, `thumbs/`.

## Website

`docs/` is the GitHub Pages site (https://m4s4t0-v01d.github.io/codex-arcanum/):
the cyber temple of Hermes Trismegistus. The visitor knocks three times at
the temple doors, then ascends the seven planetary spheres of the
*Poimandres* (Moon → Saturn) to the Eighth, with Hermes narrating in the
first person. The background is a WebGL nebula shader and a 2D orrery with
glyph rain, recoloured per sphere. Each gate holds one part of the
collection:

| Gate | Sphere | Content |
|---|---|---|
| I | Moon | Hero, cycling plates |
| II | Mercury | The concept |
| III | Venus | The Opus palettes |
| IV | Sun | The 28 Mysteries as a wheel of lunar mansions |
| V | Mars | Full-supply rarity |
| VI | Jupiter | Filterable gallery |
| VII | Saturn | Specs and the provenance seal |
| VIII | Ogdoad | Three-card oracle draw, mint (to be announced) |

Extras: a "Speak with Hermes" console (type `help`), synthesized sound
(off by default), and an easter egg (type the word of the stone). Rebuild
the site with:

```
python3 build_site.py          # renders missing showcase plates, then writes docs/
python3 build_site.py --fresh  # re-render every showcase plate
```

The page template is `site/index.template.html`. The builder injects the data
(rarity counts come from the full 777 roll) and writes `docs/manifest.json`.
The provenance hash shown on the site is the SHA-256 of that file's `tokens`
list serialised as compact JSON with sorted keys (`separators=(",", ":")`,
`ensure_ascii=False`).

Requires Python 3 + Pillow + numpy + fontTools, `gifsicle`, and the Noto
fonts in `/usr/share/fonts/noto/` (Symbols, Symbols 2, Runic, Ogham, Egyptian
Hieroglyphs, Hebrew, Devanagari, Serif, Serif Display, Math).

## Traits

| Trait | Values |
|---|---|
| **Mystery** (28 figures) | Eye of Providence, Ouroboros, Squaring of the Circle, Hieroglyphic Monad, Tree of Life, Sri Yantra, Flower of Life, Metatron's Cube, Platonic Solid, Seal of Solomon, Eye of Horus, Ankh beneath the Aten, Caduceus, Rose Cross, Taijitu & Trigrams, Wheel of the Dharma, Pentalpha, Philosophical Egg, Tetractys, Triple Spiral, Enneagram, Chymical Wedding (Sol & Luna), Serpent Power, Astrolabe, Valknut, Pyramids of Giza, Eleusinian Ear of Grain, Orphic Egg |
| **Tradition** | Follows from the figure (Freemasonry, Kabbalah, Tantra, Taoism, Norse, Eleusinian, Orphic, Pythagorean, …) |
| **Form** | Variants for some figures: Radiant Delta / Unfinished Pyramid, Flower / Seed, and the five Platonic solids plus the Star Tetrahedron |
| **Opus** (palette, named after the stages of the Great Work) | Nigredo, Folio (parchment), Albedo, Lapis Lazuli, Rubedo, Viriditas, Citrinitas, Tyrian Purple, Vermilion, Verdigris, **Cauda Pavonis** (iridescent, ~2%) |
| **Halo** | None, Rays of Glory, Emanation, Sacred Lattice, Nimbus, Celestial Spheres |
| **Glyph Ring** | Zodiac, Planetary Metals, Alchemical Elements, Elder Futhark, Hebrew, Greek, Ogham, Hieroglyphs, Bagua, Om Mani Padme Hum, Emerald Tablet inscription, VITRIOL inscription, None |
| **Frame** | Folio Plate (with plate number), Seal, Cartouche, Lancet Arch, Bare |
| **Motto** | 16 Latin/Greek mottos (SOLVE ET COAGULA, ORDO AB CHAO, ΓΝΩΘΙ ΣΕΑΥΤΟΝ, …), or None |

Glyph rings are weighted ×4 toward the figure's own tradition, so Hebrew
tends to go with the Tree of Life, runes with the Valknut, and hieroglyphs
with the Egyptian plates. Mixed pairings still happen.

Traits depend only on `(seed, token id)`. The whole supply is rolled in id
order and any duplicate combination is re-rolled, so every token is unique,
and a preview run and the full run always agree. Changing `--seed` or
`--supply` reshuffles everything.

## Code map

- `arcana/pen.py`: supersampled (2×) multi-layer pen in unit coordinates
  (layers: `faint`, `fill`, `ink`, `accent`), font fallback per glyph.
- `arcana/sigils.py`: the 28 figures. Each draws itself at loop phase `t`,
  and every motion is seamless (rotations by the symmetry angle, integer-
  frequency oscillations).
- `arcana/layers.py`: halos, glyph rings, frames, mottos (+ their weights).
- `arcana/palettes.py`: the Opus palettes (+ weights).
- `arcana/render.py`: background (stars, nebula, or parchment foxing),
  bloom, metal gradient with a glint that sweeps across once per loop,
  global-palette GIF encoding + `gifsicle -O3 --lossy`.
- `arcana/traits.py`: rolls, names ("Plate XLII: The Ouroboros"),
  descriptions.

To add a figure, decorate a function with `@sigil(...)` in `sigils.py`.
`--all-figures` will then pick it up.
