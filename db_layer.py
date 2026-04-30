# db_layer.py

import sqlite3
import datetime
from config import DB_NAME

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # ---------------- HEARINGS TABLE ----------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hearings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            date TEXT NOT NULL,
            case_number TEXT,
            case_type TEXT,
            judge TEXT,
            hearing_type TEXT,
            num_parties INTEGER,
            num_pro_se INTEGER,
            notes TEXT
        )
        """
    )

    # ---------------- EVENTS TABLE ----------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hearing_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            detail TEXT,
            tag TEXT,
            FOREIGN KEY (hearing_id) REFERENCES hearings(id)
        )
        """
    )

    # Ensure new columns exist (safe no-op if already present)
    for col_def in [
        ("subcategory", "TEXT"),
        ("tag", "TEXT"),
    ]:
        try:
            cur.execute(f"ALTER TABLE events ADD COLUMN {col_def[0]} {col_def[1]}")
        except sqlite3.OperationalError:
            pass

    # ---------------- DOCKET TABLE ----------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS docket (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT,
            case_type TEXT,
            judge TEXT,
            hearing_type TEXT,
            used INTEGER DEFAULT 0
        )
        """
    )

    conn.commit()
    conn.close()

    # ---------------- INITIALIZE OTHER MODULE TABLES ----------------
    init_resource_hub_db()
    init_settings_db()


def create_hearing(date, case_number, case_type, judge, hearing_type,
                   num_parties, num_pro_se, notes=""):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO hearings (
            created_at, date, case_number, case_type, judge,
            hearing_type, num_parties, num_pro_se, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.datetime.now().isoformat(timespec="seconds"),
            date,
            case_number,
            case_type,
            judge,
            hearing_type,
            num_parties,
            num_pro_se,
            notes,
        ),
    )
    conn.commit()
    hearing_id = cur.lastrowid
    conn.close()
    return hearing_id


def update_hearing_notes(hearing_id, notes):
    if hearing_id is None:
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE hearings SET notes = ? WHERE id = ?", (notes, hearing_id))
    conn.commit()
    conn.close()


def log_event(hearing_id, category, subcategory, detail, tag=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (hearing_id, timestamp, category, subcategory, detail, tag)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            hearing_id,
            datetime.datetime.now().isoformat(timespec="seconds"),
            category,
            subcategory,
            detail,
            tag,
        ),
    )
    conn.commit()
    conn.close()


def get_events_for_hearing(hearing_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT timestamp, category, subcategory, detail, tag
        FROM events
        WHERE hearing_id = ?
        ORDER BY id ASC
        """,
        (hearing_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_hearing_metadata(hearing_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, created_at, date, case_number, case_type, judge,
               hearing_type, num_parties, num_pro_se, notes
        FROM hearings
        WHERE id = ?
        """,
        (hearing_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_hearing_summaries():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            h.id,
            h.created_at,
            h.date,
            h.case_number,
            h.case_type,
            h.judge,
            h.hearing_type,
            h.num_parties,
            h.num_pro_se,
            SUM(CASE WHEN e.category = 'CONFUSION' THEN 1 ELSE 0 END) AS confusion_count,
            SUM(CASE WHEN e.category = 'PROCEDURAL_ERROR' THEN 1 ELSE 0 END) AS procedural_error_count,
            SUM(CASE WHEN e.category = 'JUDGE_EXPLANATION' THEN 1 ELSE 0 END) AS judge_explanation_count,
            SUM(CASE WHEN e.category = 'EMOTIONAL_DISTRESS' THEN 1 ELSE 0 END) AS emotional_distress_count,
            COUNT(e.id) AS total_events
        FROM hearings h
        LEFT JOIN events e ON h.id = e.hearing_id
        GROUP BY h.id
        ORDER BY h.created_at ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_docket_entry(case_number, case_type, judge, hearing_type):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO docket (case_number, case_type, judge, hearing_type, used)
        VALUES (?, ?, ?, ?, 0)
        """,
        (case_number, case_type, judge, hearing_type),
    )
    conn.commit()
    conn.close()


def get_docket_entries(include_used=False):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if include_used:
        cur.execute(
            """
            SELECT id, case_number, case_type, judge, hearing_type, used
            FROM docket
            ORDER BY id ASC
            """
        )
    else:
        cur.execute(
            """
            SELECT id, case_number, case_type, judge, hearing_type, used
            FROM docket
            WHERE used = 0
            ORDER BY id ASC
            """
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_docket_used(docket_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE docket SET used = 1 WHERE id = ?", (docket_id,))
    conn.commit()
    conn.close()


def get_judge_profiles():
    """
    Aggregate events by judge: counts by category and total.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            h.judge,
            COUNT(e.id) AS total_events,
            SUM(CASE WHEN e.category = 'ACCESS_TO_UNDERSTANDING' THEN 1 ELSE 0 END) AS access_events,
            SUM(CASE WHEN e.category = 'PROCEDURAL_NAVIGATION' THEN 1 ELSE 0 END) AS procedural_events,
            SUM(CASE WHEN e.category = 'COURTROOM_DYNAMICS' THEN 1 ELSE 0 END) AS dynamics_events,
            SUM(CASE WHEN e.category = 'EMOTIONAL_EXPERIENCE' THEN 1 ELSE 0 END) AS emotional_events,
            SUM(CASE WHEN e.category = 'SYSTEMIC_BARRIER' THEN 1 ELSE 0 END) AS barrier_events
        FROM hearings h
        LEFT JOIN events e ON h.id = e.hearing_id
        WHERE h.judge IS NOT NULL AND h.judge <> ''
        GROUP BY h.judge
        ORDER BY h.judge ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows
# ---------------- RESOURCE HUB TABLES ----------------

def init_resource_hub_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Categories
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resource_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        )
    """)

    # Resources
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            title TEXT NOT NULL,
            tags TEXT,
            body_markdown TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES resource_categories(id)
        )
    """)

    # Pinned items
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resource_pins (
            resource_id INTEGER PRIMARY KEY,
            pinned INTEGER DEFAULT 1,
            FOREIGN KEY (resource_id) REFERENCES resources(id)
        )
    """)

    conn.commit()
    conn.close()
# ---------------- RESOURCE HUB HELPERS ----------------

# ---- CATEGORY FUNCTIONS ----

def create_category(name, sort_order=0):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO resource_categories (name, sort_order) VALUES (?, ?)",
        (name, sort_order),
    )
    conn.commit()
    conn.close()


def rename_category(category_id, new_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "UPDATE resource_categories SET name = ? WHERE id = ?",
        (new_name, category_id),
    )
    conn.commit()
    conn.close()


def delete_category(category_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Delete resources in this category
    cur.execute("DELETE FROM resources WHERE category_id = ?", (category_id,))

    # Delete the category
    cur.execute("DELETE FROM resource_categories WHERE id = ?", (category_id,))

    conn.commit()
    conn.close()


def list_categories():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, sort_order FROM resource_categories ORDER BY sort_order, name"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---- RESOURCE FUNCTIONS ----

def create_resource(category_id, title, tags, body_markdown):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO resources (category_id, title, tags, body_markdown)
        VALUES (?, ?, ?, ?)
        """,
        (category_id, title, tags, body_markdown),
    )
    conn.commit()
    conn.close()


def update_resource(resource_id, category_id, title, tags, body_markdown):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE resources
        SET category_id = ?, title = ?, tags = ?, body_markdown = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (category_id, title, tags, body_markdown, resource_id),
    )
    conn.commit()
    conn.close()


def delete_resource(resource_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Remove pin if exists
    cur.execute("DELETE FROM resource_pins WHERE resource_id = ?", (resource_id,))

    # Remove resource
    cur.execute("DELETE FROM resources WHERE id = ?", (resource_id,))

    conn.commit()
    conn.close()


def get_resource(resource_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, category_id, title, tags, body_markdown, created_at, updated_at
        FROM resources
        WHERE id = ?
        """,
        (resource_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def list_resources(category_id=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    if category_id is None:
        cur.execute(
            """
            SELECT id, category_id, title, tags, created_at, updated_at
            FROM resources
            ORDER BY updated_at DESC
            """
        )
    else:
        cur.execute(
            """
            SELECT id, category_id, title, tags, created_at, updated_at
            FROM resources
            WHERE category_id = ?
            ORDER BY updated_at DESC
            """,
            (category_id,),
        )

    rows = cur.fetchall()
    conn.close()
    return rows


# ---- SEARCH FUNCTIONS ----

def search_resources(query):
    q = f"%{query.lower()}%"
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, category_id, title, tags, created_at, updated_at
        FROM resources
        WHERE LOWER(title) LIKE ?
           OR LOWER(tags) LIKE ?
           OR LOWER(body_markdown) LIKE ?
        ORDER BY updated_at DESC
        """,
        (q, q, q),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


# ---- PINNING FUNCTIONS ----

def pin_resource(resource_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO resource_pins (resource_id, pinned) VALUES (?, 1)",
        (resource_id,),
    )
    conn.commit()
    conn.close()


def unpin_resource(resource_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM resource_pins WHERE resource_id = ?", (resource_id,))
    conn.commit()
    conn.close()


def is_pinned(resource_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT pinned FROM resource_pins WHERE resource_id = ?", (resource_id,)
    )
    row = cur.fetchone()
    conn.close()
    return bool(row)


def list_pinned_resources():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.category_id, r.title, r.tags, r.created_at, r.updated_at
        FROM resources r
        JOIN resource_pins p ON r.id = p.resource_id
        ORDER BY r.updated_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows
# ---------------- SETTINGS TABLE ----------------

def init_settings_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


def set_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO app_settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default


def get_all_settings():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM app_settings")
    rows = cur.fetchall()
    conn.close()
    return {k: v for k, v in rows}

def create_journal_entry(entry_type, title, content, linked_hearing_id=None, linked_docket_label=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO journal_entries (created_at, type, title, linked_hearing_id, linked_docket_label, content)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.datetime.now().isoformat(timespec="seconds"),
            entry_type,
            title,
            linked_hearing_id,
            linked_docket_label,
            content,
        ),
    )
    conn.commit()
    conn.close()