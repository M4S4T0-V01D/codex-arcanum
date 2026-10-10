// CSV files for the allowlist repo. Shared by the worker's cron export and
// scripts/export.mjs, so both always write identical files.
export const PHASES = {
  sanctum: { label: "The Inner Sanctum", kind: "GTD", file: "phase-1-inner-sanctum-gtd.csv" },
  court: { label: "The Outer Court", kind: "FCFS", file: "phase-2-outer-court-fcfs.csv" },
};

const esc = v => {
  const s = v == null ? "" : String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
const iso = ms => new Date(ms).toISOString();

/** rows: entries table rows -> { path: content } */
export function buildCsvs(rows) {
  const out = {};
  for (const [key, ph] of Object.entries(PHASES)) {
    // OpenSea allowlists take plain 0x addresses, one per row (no ENS names).
    out[ph.file] = "address\n" + rows.filter(r => r.phase === key).map(r => r.address).join("\n") + "\n";
  }
  out["entries.csv"] = "book_no,address,x_handle,phase,phase_kind,source,wins,created_utc,updated_utc\n" + rows.map(r =>
    [r.num, r.address, r.x ? "@" + r.x : "", PHASES[r.phase].label, PHASES[r.phase].kind, r.source, r.wins, iso(r.created), iso(r.updated)]
      .map(esc).join(",")).join("\n") + "\n";
  return out;
}
