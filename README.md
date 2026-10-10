# Codex Arcanum

Animated NFT collection: **777 "plates"** of symbols from the world's
mystery traditions, styled after the engraved folio plates of works like
Manly P. Hall's *The Secret Teachings of All Ages* (1928). Every plate is
drawn procedurally from geometry. No scans or artwork are copied, so the
images carry no third-party rights.

Each plate is a seamless 4.2 s loop (105 frames at 25 fps), written three ways:

| File | What | Metadata field |
|---|---|---|
| `<id>.mp4` | 1080×1080 H.264 master, about 3–4 MB | `animation_url` |
| `<id>.gif` | 720×720, palette-optimised, ordered dither | `image` |
| `<id>.png` | full-size poster (first frame) | |

Rendering: line-work is supersampled 2×. Light is a separate pass: tapered
beams with bright cores, radial streaks and haze, glows and sparkles. Ink
gets a gold-leaf relief and a drop shadow, solid fills carry engraved
hatching, and bloom is three blurs.

```
python3 gen.py                    # 36-plate preview -> out/
python3 gen.py --count 777        # full collection (~1.5 h on 11 cores)
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
| ✶ | Ogdoad | **The Game of Thoth**: a card duel against Hermes |

**The Game of Thoth.** Plates are cards with four edge values (1–9, A = 10)
whose total rises with the Degree (`card_stats` in `build_site.py`). Players
take turns laying cards on the 3×3 Magic Square of Saturn. A card whose
edge beats the facing edge of an adjacent enemy card captures it. Three
Hermetic laws apply:
- **Correspondence:** a capture in the top or bottom row also turns the
  mirrored enemy card in the opposite row.
- **The Ouroboros:** a 1 captures a 9 or an A.
- **The Quintessence:** the centre cell gives +1 to every edge.

Hermes plays a greedy, risk-aware AI. The visitor's record is kept in
localStorage.

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

## The Seven Hierophants (1/1s)

Seven hand-composed one-of-ones (`arcana/hierophants.py`) at fixed token ids.
Each uses a symbol found nowhere else in the collection, its own palette,
and an ornate Hierophant frame. They are the top Degree, so the other 770
plates are ranked into Magus 40 · Adept 110 · Initiate 220 · Neophyte 400.

| Token | Plate | Tradition | Palette |
|---|---|---|---|
| VII | The Eye of Ra: winged sun disc, uraei, the Aten's ankh-rays, a hieroglyph wall | Egyptian | Solar Lapis |
| XLII | The Emerald Tablet: the full Latin text, lit line by line | Hermeticism | Smaragdine |
| CVIII | AUM on a lotus throne, a 108-bead mala, the Gayatri | Vedic | Saffron Night |
| CXLIV | The Ophanim: gyroscopic wheels full of blinking eyes, seraph wings | Merkabah | Seraph Fire |
| CCCXXXIII | Yggdrasil: nine worlds, Jörmungandr, aurora | Norse | World Ash |
| CDXXXII | The Phoenix rising from a burning nest | Alchemy / Egypt | Phoenix Flame |
| DCCLXXVII | The Sun Stone: day signs, solar rays, twin fire serpents | Mesoamerican | Obsidian Sun |

## Traits

| Trait | Values |
|---|---|
| **Degree** | Hierophant (7: the 1/1s), Magus (40), Adept (110), Initiate (220), Neophyte (400). Exact counts: every other token is ranked by trait rarity (each trait's surprisal normalised so no category dominates) and the ranking is sliced. Each plate carries an engraved degree seal; the Hierophant's burns |
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

## The gate (allowlist) — `gate-worker/`

A Cloudflare Worker (`codex-arcanum-gate.masato-void.workers.dev`) with a D1
database. It runs the allowlist for the mint on OpenSea (Robinhood Chain).

| Phase | Name | How you get in |
|---|---|---|
| I · GTD | **The Inner Sanctum** | Beat Hermes at the Game of Thoth. The knucklebones seat a verified winner here with probability `GTD_ODDS` (0.25) while seats remain (`GTD_CAP`, 150); otherwise in the Court |
| II · FCFS | **The Outer Court** | Sign the Book of Names (@X + EVM address) or win a game |
| III · Public | **The Open Gate** | Everyone, at the public mint |

**Wins are verified, not trusted.** `POST /thoth/start` deals each game
server-side from a random seed and signs `seed.iat` with HMAC (`GAME_SECRET`).
`POST /thoth/claim` checks the signature and age (3 h), then **replays the whole
game** with the shared engine (`site/thoth-engine.js`, which the site inlines at
build time) using the player's recorded moves. Only a genuine win is accepted,
and each seed can be claimed once. A wallet keeps the best seat it has won.
Also enforced:
- per-IP hourly rate limits
- address validation (0x + 40 hex; no ENS)
- X-handle validation
- a honeypot field
- CORS limited to the Pages origin

**Exports.** Entries go to the **private** repo `M4S4T0-V01D/codex-arcanum-allowlist`
(it links wallets to X handles, so keep it private):

- `phase-1-inner-sanctum-gtd.csv` and `phase-2-outer-court-fcfs.csv`: one 0x address
  per row, for OpenSea Studio allowlists. Check Studio's own template when you
  upload, in case it expects a different header.
- `entries.csv`: everything (address, @X, seat, source, wins, times).

```
cd gate-worker
npm run export        # D1 -> CSVs -> commit + push to the private repo (uses your wrangler + gh logins)
npx wrangler deploy   # after changing the worker or the card pool
```

**Share cards.** Every entry gets a permanent number in the Book of Names
(`num`, in order of inscription; `book_no` in `entries.csv`). After a signup
or a verified Thoth win, the site draws a 1600×900 "page of the Book" in the
browser: № number, @handle, seat, a plate, a wax seal. It offers a
**Post on X** button: on phones the image attaches through the share sheet;
on desktop it is saved and X opens with the post text, ready to attach.
The card is an **animated GIF** (800×450, 42 frames, the plate playing its
full loop), encoded in the browser with gifenc from per-plate frame strips
that `build_site.py` writes to `docs/plates/strip/` (7×6 grid, 330px). A
PNG still is offered too, and the site falls back to it if the GIF fails.

Every animation is a seamless loop: rotations step by the figure's own
symmetry, and pulses run at whole-number frequencies. To check, render
frame 0 and frame 1.0 and compare them; they must match.

For automatic exports every 10 minutes, give the worker a fine-grained GitHub
token with *Contents: read & write* on the allowlist repo only:
`npx wrangler secret put GITHUB_TOKEN`. Until then, `npm run export` does
the same job by hand.

`build_site.py` writes `gate-worker/src/cards.json`, the same card pool the
site uses. Redeploy the worker whenever it changes. To rename the phases,
edit `gate-worker/src/csv.js` (`PHASES`) and the phase panel in
`site/index.template.html`.
