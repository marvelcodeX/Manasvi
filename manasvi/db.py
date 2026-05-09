import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

from werkzeug.security import check_password_hash, generate_password_hash


def init_db(database_path):
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mood_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                mood TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                conversation_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        migrate_legacy_users(conn)


def migrate_legacy_users(conn):
    columns = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "id" not in columns:
        conn.execute("ALTER TABLE users RENAME TO users_legacy")
        conn.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        legacy_rows = conn.execute("SELECT username, password FROM users_legacy").fetchall()
        for username, password in legacy_rows:
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), datetime.utcnow().isoformat()),
            )
        conn.execute("DROP TABLE users_legacy")


@contextmanager
def get_connection(database_path):
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_user(database_path, username, email, password):
    with get_connection(database_path) as conn:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, email, generate_password_hash(password), datetime.utcnow().isoformat()),
        )


def authenticate_user(database_path, username, password):
    with get_connection(database_path) as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        return dict(user)
    return None


def get_user_by_id(database_path, user_id):
    with get_connection(database_path) as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(user) if user else None


def save_message(database_path, user_id, conversation_id, role, content):
    with get_connection(database_path) as conn:
        conn.execute(
            """
            INSERT INTO chat_history (user_id, conversation_id, created_at, role, content)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, conversation_id, datetime.utcnow().isoformat(), role, content),
        )


def get_chat_history(database_path, user_id, conversation_id, limit=12):
    with get_connection(database_path) as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM chat_history
            WHERE user_id = ? AND conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, conversation_id, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def get_conversations(database_path, user_id):
    with get_connection(database_path) as conn:
        rows = conn.execute(
            """
            SELECT conversation_id, MIN(created_at) AS started_at, MAX(created_at) AS last_message_at
            FROM chat_history
            WHERE user_id = ?
            GROUP BY conversation_id
            ORDER BY MAX(id) DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_mood(database_path, user_id, mood, note=""):
    with get_connection(database_path) as conn:
        conn.execute(
            "INSERT INTO mood_logs (user_id, date, mood, note) VALUES (?, ?, ?, ?)",
            (user_id, date.today().isoformat(), mood, note),
        )


def get_moods(database_path, user_id, limit=30):
    with get_connection(database_path) as conn:
        rows = conn.execute(
            """
            SELECT date, mood, note
            FROM mood_logs
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]
