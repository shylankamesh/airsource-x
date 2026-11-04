"""SQLite store for canonical observations and ingestion audit history."""
from __future__ import annotations
import json, sqlite3
from pathlib import Path
import pandas as pd
from .ingestion import CANONICAL_COLUMNS, validate_canonical

SCHEMA_VERSION=1

class ObservationStore:
    def __init__(self, path: str | Path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        con=sqlite3.connect(self.path, timeout=30)
        con.row_factory=sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def _init(self):
        with self._connect() as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("CREATE TABLE IF NOT EXISTS schema_meta (version INTEGER NOT NULL)")
            if con.execute("SELECT COUNT(*) FROM schema_meta").fetchone()[0]==0:
                con.execute("INSERT INTO schema_meta(version) VALUES (?)", (SCHEMA_VERSION,))
            version=con.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()[0]
            if version != SCHEMA_VERSION: raise RuntimeError(f"Unsupported database schema version {version}")
            cols=", ".join(f'"{c}" TEXT' for c in CANONICAL_COLUMNS)
            con.execute(f"CREATE TABLE IF NOT EXISTS observations ({cols}, PRIMARY KEY(observation_id))")
            con.execute("""CREATE TABLE IF NOT EXISTS ingestion_runs (
              run_id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, started_at TEXT NOT NULL,
              completed_at TEXT NOT NULL, status TEXT NOT NULL, rows_received INTEGER NOT NULL,
              rows_inserted INTEGER NOT NULL, rows_ignored INTEGER NOT NULL, metadata_json TEXT NOT NULL,
              error TEXT)""")
            con.execute("CREATE INDEX IF NOT EXISTS idx_obs_time ON observations(observed_at)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_obs_source ON observations(source, data_class)")

    def ingest(self, frame: pd.DataFrame, metadata: dict) -> dict:
        validate_canonical(frame)
        source=str(metadata.get("provider") or (frame.source.dropna().iloc[0] if len(frame) else "unknown"))
        now=pd.Timestamp.now(tz="UTC").isoformat()
        inserted=0
        try:
            with self._connect() as con:
                for row in frame[CANONICAL_COLUMNS].to_dict("records"):
                    clean={k:(None if pd.isna(v) else (v.isoformat() if hasattr(v,"isoformat") else str(v))) for k,v in row.items()}
                    before=con.total_changes
                    con.execute(f"INSERT OR IGNORE INTO observations ({','.join(CANONICAL_COLUMNS)}) VALUES ({','.join('?' for _ in CANONICAL_COLUMNS)})", [clean[k] for k in CANONICAL_COLUMNS])
                    inserted += con.total_changes-before
                ignored=len(frame)-inserted
                con.execute("INSERT INTO ingestion_runs(source,started_at,completed_at,status,rows_received,rows_inserted,rows_ignored,metadata_json,error) VALUES (?,?,?,?,?,?,?,?,NULL)",
                  (source,now,pd.Timestamp.now(tz="UTC").isoformat(),"success",len(frame),inserted,ignored,json.dumps(metadata,default=str)))
            return {"rows_received":len(frame),"rows_inserted":inserted,"rows_ignored":ignored,"status":"success"}
        except Exception as exc:
            with self._connect() as con:
                con.execute("INSERT INTO ingestion_runs(source,started_at,completed_at,status,rows_received,rows_inserted,rows_ignored,metadata_json,error) VALUES (?,?,?,?,?,?,?,?,?)",
                  (source,now,pd.Timestamp.now(tz="UTC").isoformat(),"failed",len(frame),0,len(frame),json.dumps(metadata,default=str),str(exc)))
            raise

    def observations(self, *, source: str | None=None, data_class: str | None=None, limit: int=10000) -> pd.DataFrame:
        if limit<1 or limit>100000: raise ValueError("limit must be 1..100000")
        sql="SELECT * FROM observations WHERE 1=1"; args=[]
        if source: sql+=" AND source=?"; args.append(source)
        if data_class: sql+=" AND data_class=?"; args.append(data_class)
        sql+=" ORDER BY observed_at DESC LIMIT ?"; args.append(limit)
        with self._connect() as con: return pd.read_sql_query(sql,con,params=args)

    def ingestion_history(self, limit: int=100) -> pd.DataFrame:
        with self._connect() as con: return pd.read_sql_query("SELECT * FROM ingestion_runs ORDER BY run_id DESC LIMIT ?",con,params=(limit,))

    def source_health(self) -> pd.DataFrame:
        with self._connect() as con:
            return pd.read_sql_query("SELECT source, MAX(completed_at) last_retrieved_at, SUM(rows_inserted) rows_inserted, SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) failures FROM ingestion_runs GROUP BY source ORDER BY source",con)
