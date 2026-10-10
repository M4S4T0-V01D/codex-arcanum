-- One row per wallet. phase = 'sanctum' (GTD) or 'court' (FCFS); a wallet keeps the best seat it has won.
CREATE TABLE IF NOT EXISTS entries (
  address TEXT PRIMARY KEY,
  x TEXT,
  phase TEXT NOT NULL,
  source TEXT NOT NULL,
  wins INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL,
  num INTEGER  -- place in the Book of Names, in order of inscription
);
CREATE UNIQUE INDEX IF NOT EXISTS entries_num ON entries(num);
-- Every verified game seed can be claimed once.
CREATE TABLE IF NOT EXISTS claims (seed TEXT PRIMARY KEY, address TEXT NOT NULL, ts INTEGER NOT NULL);
-- Rate-limit buckets (route:ip:hour).
CREATE TABLE IF NOT EXISTS hits (k TEXT PRIMARY KEY, n INTEGER NOT NULL, exp INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
