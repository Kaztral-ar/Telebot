import sqlite3
from config import DATABASE_PATH


def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id TEXT NOT NULL,
            channel_name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, channel_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            content TEXT,
            media_file_id TEXT,
            media_type TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER,
            channel_id TEXT NOT NULL,
            channel_name TEXT,
            scheduled_time TEXT NOT NULL,
            content TEXT,
            media_file_id TEXT,
            media_type TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS event_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT,
            channel_id TEXT,
            post_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY,
            timezone TEXT DEFAULT 'UTC',
            default_channel TEXT,
            notifications INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


# ── Channels ────────────────────────────────────────────────────────────────

def add_channel(user_id, channel_id, channel_name):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO channels (user_id, channel_id, channel_name) VALUES (?,?,?)",
            (user_id, channel_id, channel_name)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_channels(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM channels WHERE user_id=? ORDER BY added_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return rows


def delete_channel(user_id, channel_id):
    conn = get_conn()
    conn.execute("DELETE FROM channels WHERE user_id=? AND channel_id=?", (user_id, channel_id))
    conn.commit()
    conn.close()


# ── Posts ────────────────────────────────────────────────────────────────────

def save_post(user_id, title, content, media_file_id=None, media_type=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO posts (user_id, title, content, media_file_id, media_type)
           VALUES (?,?,?,?,?)""",
        (user_id, title, content, media_file_id, media_type)
    )
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    return post_id


def get_posts(user_id, status=None):
    conn = get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM posts WHERE user_id=? AND status=? ORDER BY created_at DESC",
            (user_id, status)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM posts WHERE user_id=? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
    conn.close()
    return rows


def get_post(post_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    conn.close()
    return row


def delete_post(post_id, user_id):
    conn = get_conn()
    conn.execute("DELETE FROM posts WHERE id=? AND user_id=?", (post_id, user_id))
    conn.commit()
    conn.close()


# ── Scheduled Posts ──────────────────────────────────────────────────────────

def schedule_post(user_id, channel_id, channel_name, scheduled_time, content,
                  media_file_id=None, media_type=None, post_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO scheduled_posts
           (user_id, post_id, channel_id, channel_name, scheduled_time, content, media_file_id, media_type)
           VALUES (?,?,?,?,?,?,?,?)""",
        (user_id, post_id, channel_id, channel_name, scheduled_time, content, media_file_id, media_type)
    )
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_scheduled_posts(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM scheduled_posts WHERE user_id=? AND status='pending' ORDER BY scheduled_time ASC",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_pending_scheduled():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM scheduled_posts WHERE status='pending' ORDER BY scheduled_time ASC"
    ).fetchall()
    conn.close()
    return rows


def mark_scheduled_sent(sched_id):
    conn = get_conn()
    conn.execute(
        "UPDATE scheduled_posts SET status='sent' WHERE id=?", (sched_id,)
    )
    conn.commit()
    conn.close()


def mark_scheduled_failed(sched_id):
    conn = get_conn()
    conn.execute(
        "UPDATE scheduled_posts SET status='failed' WHERE id=?", (sched_id,)
    )
    conn.commit()
    conn.close()


def delete_scheduled(sched_id, user_id):
    conn = get_conn()
    conn.execute(
        "DELETE FROM scheduled_posts WHERE id=? AND user_id=? AND status='pending'",
        (sched_id, user_id)
    )
    conn.commit()
    conn.close()


# ── Event Log ────────────────────────────────────────────────────────────────

def log_event(user_id, event_type, description, channel_id=None, post_id=None):
    conn = get_conn()
    conn.execute(
        """INSERT INTO event_log (user_id, event_type, description, channel_id, post_id)
           VALUES (?,?,?,?,?)""",
        (user_id, event_type, description, channel_id, post_id)
    )
    conn.commit()
    conn.close()


def get_events(user_id, limit=30):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM event_log WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return rows


def clear_events(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM event_log WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


# ── Settings ─────────────────────────────────────────────────────────────────

def get_settings(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        conn.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = conn.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row


def update_setting(user_id, key, value):
    conn = get_conn()
    conn.execute(f"UPDATE settings SET {key}=? WHERE user_id=?", (value, user_id))
    if conn.execute("SELECT changes()").fetchone()[0] == 0:
        conn.execute("INSERT INTO settings (user_id) VALUES (?)", (user_id,))
        conn.execute(f"UPDATE settings SET {key}=? WHERE user_id=?", (value, user_id))
    conn.commit()
    conn.close()
