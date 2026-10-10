// Export the allowlist from D1 into the private allowlist repo and push it.
// Uses your local wrangler + git logins, so no GitHub token lives in the cloud.
//   npm run export            (from gate-worker/)
import { execFileSync } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import { PHASES, buildCsvs } from "../src/csv.js";

const REPO = process.env.ALLOWLIST_REPO || "M4S4T0-V01D/codex-arcanum-allowlist";
const DIR = process.env.ALLOWLIST_DIR || join(homedir(), "Documents/Projects/codex-arcanum-allowlist");

const out = execFileSync("npx", ["wrangler", "d1", "execute", "codex-arcanum-gate", "--remote", "--json",
  "--command", "SELECT * FROM entries ORDER BY created"], { encoding: "utf8", maxBuffer: 1 << 28 });
const rows = JSON.parse(out)[0].results;
if (!existsSync(DIR)) execFileSync("gh", ["repo", "clone", REPO, DIR], { stdio: "inherit" });
const git = (...a) => execFileSync("git", ["-C", DIR, ...a], { encoding: "utf8" });
const fresh = !git("ls-remote", "--heads", "origin").trim();
if (fresh) git("checkout", "-q", "-B", "main");
else git("pull", "-q", "--rebase", "origin", "main");
if (!existsSync(join(DIR, "README.md"))) writeFileSync(join(DIR, "README.md"), `# Codex Arcanum allowlist (private)

Written by \`gate-worker\` in the codex-arcanum repo: \`npm run export\`, or the worker's
10-minute cron once a GITHUB_TOKEN secret is set.

| File | What |
|---|---|
| ${Object.values(PHASES).map(p => `\`${p.file}\` | ${p.label} (${p.kind}): one 0x address per row, for an OpenSea Studio allowlist`).join(" |\n| ")} |
| \`entries.csv\` | Everything: address, X handle, seat, how it was earned (thoth / signup), wins, times |

Keep this repo private: it links wallets to X handles.
`);
for (const [path, content] of Object.entries(buildCsvs(rows))) writeFileSync(join(DIR, path), content);
execFileSync("git", ["-C", DIR, "add", "-A"]);
const changed = execFileSync("git", ["-C", DIR, "status", "--porcelain"], { encoding: "utf8" }).trim();
if (!changed) { console.log(`No changes (${rows.length} entries).`); process.exit(0); }
execFileSync("git", ["-C", DIR, "commit", "-q", "-m", `Allowlist: ${rows.length} entries`]);
execFileSync("git", ["-C", DIR, "push", "-q", "-u", "origin", "main"], { stdio: "inherit" });
const n = k => rows.filter(r => r.phase === k).length;
console.log(`Exported ${rows.length} entries (Inner Sanctum ${n("sanctum")}, Outer Court ${n("court")}) to ${REPO}.`);
