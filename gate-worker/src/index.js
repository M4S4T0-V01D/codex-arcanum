// The gate of the temple: deals verified games of Thoth, seats winners in the
// Inner Sanctum (GTD) or the Outer Court (FCFS), takes signups for the Book of
// Names, and exports the lists as CSV to the private allowlist repo.
import { deal, replay } from "../../site/thoth-engine.js";
import POOL from "./cards.json";
import { PHASES, buildCsvs } from "./csv.js";

const GAME_TTL_MS = 3 * 60 * 60 * 1000;
const LIMITS = { start: 60, claim: 20, signup: 6 }; // per IP per hour

const ADDRESS = /^0x[0-9a-fA-F]{40}$/;
const HANDLE = /^[A-Za-z0-9_]{1,15}$/;

export default {
  async fetch(req, env) {
    const cors = corsHeaders(req, env);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    const url = new URL(req.url);
    try {
      let body = null;
      if (req.method === "POST") {
        if (!cors["Access-Control-Allow-Origin"]) return json({ error: "Unknown origin." }, 403, cors);
        body = await req.json().catch(() => null);
        if (!body || typeof body !== "object") return json({ error: "Send JSON." }, 400, cors);
      }
      const route = `${req.method} ${url.pathname}`;
      if (route === "GET /stats") return json(await stats(env), 200, cors);
      if (route === "POST /thoth/start") return json(await start(req, env), 200, cors);
      if (route === "POST /thoth/claim") return json(await claim(req, env, body), 200, cors);
      if (route === "POST /signup") return json(await signup(req, env, body), 200, cors);
      return json({ error: "No door by that name." }, 404, cors);
    } catch (e) {
      if (e instanceof Refusal) return json({ error: e.message }, e.status, cors);
      console.error(e);
      return json({ error: "The temple is troubled. Try again." }, 500, cors);
    }
  },

  async scheduled(_event, env, ctx) {
    ctx.waitUntil(Promise.all([exportToGitHub(env), env.DB.prepare("DELETE FROM hits WHERE exp < ?").bind(Date.now()).run()]));
  },
};

class Refusal extends Error {
  constructor(message, status = 400) { super(message); this.status = status; }
}

function corsHeaders(req, env) {
  const origin = req.headers.get("Origin") || "";
  const allowed = (env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);
  const ok = allowed.includes(origin);
  return {
    ...(ok ? { "Access-Control-Allow-Origin": origin } : {}),
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

const json = (data, status, headers) =>
  new Response(JSON.stringify(data), { status, headers: { ...headers, "Content-Type": "application/json" } });

async function limit(req, env, route) {
  const ip = req.headers.get("CF-Connecting-IP") || "unknown";
  const hour = Math.floor(Date.now() / 3600000);
  const k = `${route}:${ip}:${hour}`;
  const row = await env.DB.prepare(
    "INSERT INTO hits (k, n, exp) VALUES (?, 1, ?) ON CONFLICT(k) DO UPDATE SET n = n + 1 RETURNING n",
  ).bind(k, (hour + 2) * 3600000).first();
  if (row.n > LIMITS[route]) throw new Refusal("Too many knocks. Rest a while, and return within the hour.", 429);
}

// ---- signatures -------------------------------------------------------------
const enc = new TextEncoder();
async function hmac(secret, msg) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(msg));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, "0")).join("");
}
function sameString(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}
// every change bumps the revision; the exporter records the revision it wrote
const BUMP = env => env.DB.prepare("INSERT INTO meta (k, v) VALUES ('rev', '1') ON CONFLICT(k) DO UPDATE SET v = CAST(v AS INTEGER) + 1");
const randomHex = n => [...crypto.getRandomValues(new Uint8Array(n))].map(b => b.toString(16).padStart(2, "0")).join("");

// ---- routes -----------------------------------------------------------------
async function stats(env) {
  const rows = (await env.DB.prepare("SELECT phase, COUNT(*) AS n FROM entries GROUP BY phase").all()).results;
  const n = Object.fromEntries(rows.map(r => [r.phase, r.n]));
  return { sanctum: n.sanctum || 0, court: n.court || 0, sanctumCap: +env.GTD_CAP, phases: PHASES };
}

async function start(req, env) {
  await limit(req, env, "start");
  const seed = randomHex(16), iat = Date.now();
  const sig = await hmac(env.GAME_SECRET, `${seed}.${iat}`);
  const d = deal(seed, POOL);
  return { seed, iat, sig, you: d.you, her: d.her, first: d.first };
}

function cleanEntry(body, needHandle) {
  if (body.hp) throw new Refusal("The temple does not admit automata.");
  const address = String(body.address || "").trim();
  if (!ADDRESS.test(address)) throw new Refusal("That is not an EVM address. It should be 0x followed by 40 hex characters (ENS names cannot be used).");
  const raw = String(body.x || "").trim().replace(/^@/, "").replace(/^https?:\/\/(www\.)?(x|twitter)\.com\//i, "");
  if (needHandle && !raw) throw new Refusal("Give your @ on X.");
  if (raw && !HANDLE.test(raw)) throw new Refusal("That is not an X handle: up to 15 letters, numbers or underscores.");
  return { address: address.toLowerCase(), x: raw || null };
}

async function claim(req, env, body) {
  await limit(req, env, "claim");
  const { address, x } = cleanEntry(body, false);
  const { seed, iat, sig, moves } = body;
  if (typeof seed !== "string" || !Number.isFinite(iat) || !Array.isArray(moves) || moves.length > 5) {
    throw new Refusal("Hermes does not recognise this game.");
  }
  if (!sameString(sig, await hmac(env.GAME_SECRET, `${seed}.${iat}`))) throw new Refusal("Hermes did not deal this game.", 403);
  if (Date.now() - iat > GAME_TTL_MS) throw new Refusal("This game has grown cold. Win a fresh one.", 410);
  const game = replay(seed, POOL, moves.map(m => ({ card: +m.card, cell: +m.cell })));
  if (!game.ok) throw new Refusal(`Hermes replayed your game and found ${game.reason}.`, 403);
  if (game.you <= game.her) throw new Refusal("Hermes replayed your game. It was not a victory.", 403);

  const now = Date.now();
  const taken = await env.DB.prepare("INSERT INTO claims (seed, address, ts) VALUES (?, ?, ?) ON CONFLICT(seed) DO NOTHING RETURNING seed")
    .bind(seed, address, now).first();
  if (!taken) throw new Refusal("This victory has already been claimed.", 409);

  const prev = await env.DB.prepare("SELECT phase FROM entries WHERE address = ?").bind(address).first();
  const seated = (await env.DB.prepare("SELECT COUNT(*) AS n FROM entries WHERE phase = 'sanctum'").first()).n;
  const roll = crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32;
  const won = roll < +env.GTD_ODDS && seated < +env.GTD_CAP ? "sanctum" : "court";
  const phase = prev && prev.phase === "sanctum" ? "sanctum" : won;
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO entries (address, x, phase, source, wins, created, updated) VALUES (?, ?, ?, 'thoth', 1, ?, ?)
      ON CONFLICT(address) DO UPDATE SET phase = ?, wins = wins + 1, updated = ?, x = COALESCE(?, x),
      source = CASE WHEN source = 'signup' THEN 'signup+thoth' ELSE source END`)
      .bind(address, x, phase, now, now, phase, now, x),
    BUMP(env),
  ]);
  return {
    phase, ...PHASES[phase], score: [game.you, game.her],
    kept: !!prev && prev.phase === "sanctum" && won !== "sanctum",
    upgraded: !!prev && prev.phase === "court" && phase === "sanctum",
  };
}

async function signup(req, env, body) {
  await limit(req, env, "signup");
  const { address, x } = cleanEntry(body, true);
  const now = Date.now();
  const prev = await env.DB.prepare("SELECT phase, x FROM entries WHERE address = ?").bind(address).first();
  if (prev) {
    if (!prev.x) await env.DB.prepare("UPDATE entries SET x = ?, updated = ? WHERE address = ?").bind(x, now, address).run();
    return { phase: prev.phase, ...PHASES[prev.phase], already: true };
  }
  await env.DB.batch([
    env.DB.prepare("INSERT INTO entries (address, x, phase, source, wins, created, updated) VALUES (?, ?, 'court', 'signup', 0, ?, ?)")
      .bind(address, x, now, now),
    BUMP(env),
  ]);
  return { phase: "court", ...PHASES.court, already: false };
}

// ---- export to the private allowlist repo ------------------------------------
function b64(str) {
  const bytes = enc.encode(str);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

async function exportToGitHub(env) {
  if (!env.GITHUB_TOKEN || !env.GITHUB_REPO) return; // the local `npm run export` does the same job
  const [rev, done] = await Promise.all(["rev", "exported"].map(k => env.DB.prepare("SELECT v FROM meta WHERE k = ?").bind(k).first()));
  if (!rev || (done && done.v === rev.v)) return;
  const rows = (await env.DB.prepare("SELECT * FROM entries ORDER BY created").all()).results;
  const gh = (path, init = {}) => fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`, {
    ...init,
    headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "codex-arcanum-gate", ...(init.headers || {}) },
  });
  for (const [path, content] of Object.entries(buildCsvs(rows))) {
    const cur = await gh(path);
    const sha = cur.ok ? (await cur.json()).sha : undefined;
    const put = await gh(path, {
      method: "PUT",
      body: JSON.stringify({ message: `Allowlist: ${rows.length} entries`, content: b64(content), ...(sha ? { sha } : {}) }),
    });
    if (!put.ok) { console.error("export failed", path, put.status, await put.text()); return; }
  }
  await env.DB.prepare("INSERT INTO meta (k, v) VALUES ('exported', ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v").bind(rev.v).run();
}
