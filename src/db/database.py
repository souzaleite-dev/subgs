"""
Camada de persistencia (SQLite) do SENTINELA ORBITAL.

Tabelas:
  - sensor_readings : leituras dos sensores de solo (ESP32 simulado)
  - detections      : resultados da classificacao de imagens orbitais (CNN)
  - alerts          : alertas gerados pela fusao sensor + imagem
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Permite "from config.config import ..." independentemente do cwd
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import DB_PATH, ensure_dirs


SCHEMA = """
CREATE TABLE IF NOT EXISTS sensor_readings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT    NOT NULL,
    estacao       TEXT    NOT NULL,
    temp_ar       REAL,
    umid_ar       REAL,
    temp_solo     REAL,
    umid_solo     REAL,
    fumaca_ppm    REAL,
    risco_sensor  REAL,
    nivel         TEXT
);

CREATE TABLE IF NOT EXISTS detections (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT    NOT NULL,
    imagem        TEXT,
    classe        TEXT    NOT NULL,
    confianca     REAL    NOT NULL,
    prob_floresta REAL,
    prob_desmate  REAL,
    prob_agua     REAL
);

CREATE TABLE IF NOT EXISTS alerts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT    NOT NULL,
    estacao       TEXT,
    risco_total   REAL,
    nivel         TEXT,
    origem        TEXT,
    mensagem      TEXT
);
"""


def get_conn() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cria as tabelas caso ainda nao existam."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Inserts
# ---------------------------------------------------------------------------
def insert_sensor_reading(r: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO sensor_readings
               (ts, estacao, temp_ar, umid_ar, temp_solo, umid_solo,
                fumaca_ppm, risco_sensor, nivel)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                r.get("ts", _now()), r["estacao"], r["temp_ar"], r["umid_ar"],
                r["temp_solo"], r["umid_solo"], r["fumaca_ppm"],
                r["risco_sensor"], r["nivel"],
            ),
        )


def insert_detection(d: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO detections
               (ts, imagem, classe, confianca, prob_floresta,
                prob_desmate, prob_agua)
               VALUES (?,?,?,?,?,?,?)""",
            (
                d.get("ts", _now()), d.get("imagem"), d["classe"], d["confianca"],
                d.get("prob_floresta"), d.get("prob_desmate"), d.get("prob_agua"),
            ),
        )


def insert_alert(a: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO alerts
               (ts, estacao, risco_total, nivel, origem, mensagem)
               VALUES (?,?,?,?,?,?)""",
            (
                a.get("ts", _now()), a.get("estacao"), a["risco_total"],
                a["nivel"], a.get("origem"), a.get("mensagem"),
            ),
        )


# ---------------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------------
def fetch_recent(table: str, limit: int = 100) -> list[dict]:
    allowed = {"sensor_readings", "detections", "alerts"}
    if table not in allowed:
        raise ValueError(f"tabela invalida: {table}")
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def latest_sensor() -> dict | None:
    rows = fetch_recent("sensor_readings", 1)
    return rows[0] if rows else None


def latest_detection() -> dict | None:
    rows = fetch_recent("detections", 1)
    return rows[0] if rows else None


if __name__ == "__main__":
    init_db()
    print(f"Banco inicializado em: {DB_PATH}")
