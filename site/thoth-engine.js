// The Game of Thoth: rules, deal and Hermes' AI.
// Shared by the site (build_site.py inlines this file, stripping `export`)
// and the gate worker (which imports it to replay and verify claimed wins).
// Everything here must be deterministic given the seed.

export const LOSHU = [4, 9, 2, 3, 5, 7, 8, 1, 6];
export const DIRS = [[-1, 0], [0, 1], [1, 0], [0, -1]]; // top, right, bottom, left

/** Seeded PRNG: xmur3 string hash -> mulberry32. */
export function rng32(str) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  let a = h >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const cardVal = (c, i, cell) => c.sides[i] + (cell === 4 ? 1 : 0);
const power = c => c.sides.reduce((x, y) => x + y, 0);

/** Captures made by `card` laid on `cell` (board not yet changed by them). */
export function captures(board, cell, card) {
  const r = Math.floor(cell / 3), col = cell % 3, direct = [];
  let ouro = false;
  DIRS.forEach(([dr, dc], i) => {
    const rr = r + dr, cc = col + dc;
    if (rr < 0 || rr > 2 || cc < 0 || cc > 2) return;
    const n = rr * 3 + cc, o = board[n];
    if (!o || o.owner === card.owner) return;
    const a = cardVal(card, i, cell), d = cardVal(o, (i + 2) % 4, n);
    if (a > d) direct.push(n);
    else if (a === 1 && d >= 9) { direct.push(n); ouro = true; } // the Ouroboros
  });
  const mirror = []; // Correspondence: as above, so below
  direct.forEach(n => {
    const rr = Math.floor(n / 3);
    if (rr === 1) return;
    const m = (2 - rr) * 3 + (n % 3), o = board[m];
    if (o && o.owner !== card.owner && m !== cell && !direct.includes(m) && !mirror.includes(m)) mirror.push(m);
  });
  return { direct, mirror, ouro };
}

/** Deal two balanced hands of five from `pool` ([{id, name, sides, level}], sorted by id). */
export function deal(seed, pool) {
  const rnd = rng32(seed + ":deal");
  let you, her, tries = 0;
  do {
    const p = pool.slice();
    for (let i = p.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [p[i], p[j]] = [p[j], p[i]]; }
    you = p.slice(0, 5); her = p.slice(5, 10); tries++;
  } while (Math.abs(you.reduce((s, c) => s + power(c), 0) - her.reduce((s, c) => s + power(c), 0)) > 6 && tries < 40);
  const mk = (c, owner) => ({ id: c.id, name: c.name, sides: c.sides.slice(), level: c.level, owner });
  return { you: you.map(c => mk(c, "you")), her: her.map(c => mk(c, "her")), first: rnd() < 0.5 ? "you" : "her" };
}

/** Hermes' move: greedy captures, wary of exposing weak edges, a little noise. */
export function aiChoose(board, hand, rnd) {
  let best = null;
  hand.forEach((c, i) => board.forEach((o, cell) => {
    if (o) return;
    const b = board.slice(), card = { ...c, owner: "her" };
    b[cell] = card;
    const res = captures(b, cell, card);
    let sc = (res.direct.length + res.mirror.length) * 10 + (cell === 4 ? 1.5 : 0);
    const r = Math.floor(cell / 3), col = cell % 3;
    DIRS.forEach(([dr, dc], k) => {
      const rr = r + dr, cc = col + dc;
      if (rr < 0 || rr > 2 || cc < 0 || cc > 2 || b[rr * 3 + cc]) return;
      const v = cardVal(card, k, cell);
      sc -= Math.max(0, 7 - v) * 0.7 + (v >= 9 ? 1 : 0);
    });
    sc -= power(c) * 0.04;
    sc += rnd() * 1.2;
    if (!best || sc > best.sc) best = { i, cell, sc };
  }));
  return best;
}

/** Lay hand[who][idx] on cell and apply every capture. Returns the capture result. */
export function apply(board, hands, who, idx, cell) {
  const card = hands[who].splice(idx, 1)[0];
  card.owner = who;
  board[cell] = card;
  const res = captures(board, cell, card);
  res.direct.concat(res.mirror).forEach(n => { board[n].owner = who; });
  return res;
}

export const score = (board, hands) => ({
  you: board.filter(c => c && c.owner === "you").length + hands.you.length,
  her: board.filter(c => c && c.owner === "her").length + hands.her.length,
});

/** Replay a whole game from its seed and the player's moves ([{card, cell}]). */
export function replay(seed, pool, moves) {
  const d = deal(seed, pool), hands = { you: d.you, her: d.her }, board = Array(9).fill(null);
  const ai = rng32(seed + ":ai");
  let turn = d.first, mi = 0;
  while (board.some(c => !c)) {
    if (turn === "her") {
      const m = aiChoose(board, hands.her, ai);
      apply(board, hands, "her", m.i, m.cell);
    } else {
      const mv = moves[mi++];
      if (!mv) return { ok: false, reason: "the game is unfinished" };
      const idx = hands.you.findIndex(c => c.id === mv.card);
      if (idx < 0 || !Number.isInteger(mv.cell) || mv.cell < 0 || mv.cell > 8 || board[mv.cell]) {
        return { ok: false, reason: "an illegal move" };
      }
      apply(board, hands, "you", idx, mv.cell);
    }
    turn = turn === "you" ? "her" : "you";
  }
  if (mi !== moves.length) return { ok: false, reason: "moves after the end" };
  return { ok: true, ...score(board, hands) };
}
