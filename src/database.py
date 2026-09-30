import sqlite3
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "meetings.db"

def connect():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            organizer TEXT NOT NULL,
            meeting_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            meeting_type TEXT NOT NULL,
            location TEXT DEFAULT '',
            participants TEXT DEFAULT '',
            description TEXT DEFAULT '',
            agenda TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Scheduled',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            assignee TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Medium',
            due_date TEXT NOT NULL,
            meeting_id INTEGER,
            notes TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(meeting_id) REFERENCES meetings(id) ON DELETE SET NULL
        );
        """)

def _rows(query, params=()):
    with connect() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]

def get_meeting(meeting_id):
    rows = _rows("SELECT * FROM meetings WHERE id=?", (meeting_id,))
    return rows[0] if rows else None

def get_meetings(search="", status=None, meeting_type=None, upcoming_only=False, limit=200):
    where, params = [], []
    if search:
        where.append("(title LIKE ? OR organizer LIKE ? OR location LIKE ? OR participants LIKE ?)")
        s = f"%{search}%"
        params.extend([s,s,s,s])
    if status:
        where.append("status=?")
        params.append(status)
    if meeting_type:
        where.append("meeting_type=?")
        params.append(meeting_type)
    if upcoming_only:
        where.append("meeting_date >= ?")
        params.append(str(date.today()))
    sql = "SELECT * FROM meetings"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY meeting_date ASC, start_time ASC LIMIT ?"
    params.append(limit)
    return _rows(sql, params)

def add_meeting(data):
    with connect() as conn:
        cur = conn.execute("""
            INSERT INTO meetings
            (title, organizer, meeting_date, start_time, end_time, meeting_type,
             location, participants, description, agenda, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["title"], data["organizer"], data["meeting_date"], data["start_time"],
            data["end_time"], data["meeting_type"], data.get("location",""),
            data.get("participants",""), data.get("description",""),
            data.get("agenda",""), data.get("status","Scheduled")
        ))
        return cur.lastrowid

def update_meeting(meeting_id, data):
    allowed = ["title","organizer","meeting_date","start_time","end_time","meeting_type",
               "location","participants","description","agenda","status"]
    fields = [f for f in allowed if f in data]
    if not fields:
        return
    values = [data[f] for f in fields]
    values.append(meeting_id)
    sql = f"UPDATE meetings SET {', '.join(f'{f}=?' for f in fields)}, updated_at=CURRENT_TIMESTAMP WHERE id=?"
    with connect() as conn:
        conn.execute(sql, values)

def delete_meeting(meeting_id):
    with connect() as conn:
        conn.execute("DELETE FROM meetings WHERE id=?", (meeting_id,))

def get_action_items(status=None, limit=500):
    if status:
        return _rows("""
            SELECT a.*, m.title AS meeting_title
            FROM action_items a LEFT JOIN meetings m ON a.meeting_id=m.id
            WHERE a.status=? ORDER BY a.due_date ASC LIMIT ?
        """, (status, limit))
    return _rows("""
        SELECT a.*, m.title AS meeting_title
        FROM action_items a LEFT JOIN meetings m ON a.meeting_id=m.id
        ORDER BY a.due_date ASC LIMIT ?
    """, (limit,))

def add_action_item(data):
    with connect() as conn:
        cur = conn.execute("""
            INSERT INTO action_items
            (title, assignee, priority, due_date, meeting_id, notes, status)
            VALUES (?,?,?,?,?,?,?)
        """, (
            data["title"], data["assignee"], data.get("priority","Medium"),
            data["due_date"], data.get("meeting_id"), data.get("notes",""),
            data.get("status","Open")
        ))
        return cur.lastrowid

def update_action_item(action_id, data):
    allowed = ["title","assignee","priority","due_date","meeting_id","notes","status"]
    fields = [f for f in allowed if f in data]
    if not fields:
        return
    values = [data[f] for f in fields]
    values.append(action_id)
    with connect() as conn:
        conn.execute(
            f"UPDATE action_items SET {', '.join(f'{f}=?' for f in fields)} WHERE id=?",
            values
        )

def delete_action_item(action_id):
    with connect() as conn:
        conn.execute("DELETE FROM action_items WHERE id=?", (action_id,))

def get_stats():
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM meetings").fetchone()[0]
        upcoming = conn.execute(
            "SELECT COUNT(*) FROM meetings WHERE meeting_date >= ? AND status='Scheduled'",
            (str(date.today()),)
        ).fetchone()[0]
        completed = conn.execute(
            "SELECT COUNT(*) FROM meetings WHERE status='Completed'"
        ).fetchone()[0]
        actions = conn.execute("SELECT COUNT(*) FROM action_items").fetchone()[0]
        open_actions = conn.execute(
            "SELECT COUNT(*) FROM action_items WHERE status!='Completed'"
        ).fetchone()[0]
    return {
        "total": total, "upcoming": upcoming, "completed": completed,
        "actions": actions, "open_actions": open_actions
    }

def export_data():
    return {
        "meetings": _rows("SELECT * FROM meetings ORDER BY meeting_date, start_time"),
        "action_items": _rows("SELECT * FROM action_items ORDER BY due_date")
    }
