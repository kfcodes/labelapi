from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

BASE_DIR = Path(__file__).resolve().parents[1]  # -> app/
ENV_FILE = BASE_DIR / "env" / "db.env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=False)

DRIVER = os.getenv("DB_DRIVER", "mariadb+pymysql")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
NAME = os.getenv("DB_NAME")
USER = os.getenv("DB_USER")
PASS = os.getenv("DB_PASSWORD")

_missing = [
    k
    for k, v in {
        "DB_HOST": HOST,
        "DB_PORT": PORT,
        "DB_NAME": NAME,
        "DB_USER": USER,
        "DB_PASSWORD": PASS,
    }.items()
    if not v
]
if _missing:
    raise RuntimeError(
        f"Database env vars missing: {', '.join(_missing)} (looked in {ENV_FILE})"
    )

CONNECTION_STRING = f"{DRIVER}://{USER}:{PASS}@{HOST}:{PORT}/{NAME}"


@lru_cache(maxsize=1)
def db() -> Engine:
    print("CONNECTION STRING")
    print(CONNECTION_STRING)
    return create_engine(CONNECTION_STRING, pool_pre_ping=True)


def dispose_engine() -> None:
    eng = db()
    eng.dispose()
    db.cache_clear()
