from __future__ import annotations
import sqlite3
from flask import g
from config import DATABASE_PATH

SCHEMA_PATH = __import__('pathlib').Path(__file__).resolve().parent / 'schema.sql'

def _connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    return db

def get_db():
    if 'db' not in g:
        g.db = _connect()
    return g.db

def close_db(_exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = _connect()
    try:
        db.executescript(SCHEMA_PATH.read_text(encoding='utf-8'))
        db.commit()
    finally:
        db.close()
