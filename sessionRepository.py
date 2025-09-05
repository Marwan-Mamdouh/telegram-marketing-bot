import sqlite3
import json
import os

DB_NAME = "store.db"  # same DB you already use


def init_session_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sessions (
            user_id INTEGER PRIMARY KEY,
            state TEXT,
            data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()


def save_session(user_id: int, state: str, data: dict):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO sessions (user_id, state, data)
                     VALUES (?, ?, ?)
                     ON CONFLICT(user_id) DO UPDATE SET
                        state=excluded.state,
                        data=excluded.data,
                        updated_at=CURRENT_TIMESTAMP
        ''', (user_id, state, json.dumps(data, ensure_ascii=False)))
        conn.commit()


def get_session(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT state, data FROM sessions WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row:
            state, data = row
            return {"state": state, "data": json.loads(data)}
        return None


def delete_session(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        conn.commit()
