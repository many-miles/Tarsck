import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "tarsck.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            deadline TEXT DEFAULT NULL,
            complexity INTEGER DEFAULT 3 CHECK(complexity BETWEEN 1 AND 5),
            status TEXT DEFAULT 'OPEN' CHECK(status IN ('OPEN','IN_PROGRESS','BLOCKED','COMPLETE')),
            activity_type TEXT DEFAULT 'CODING' CHECK(activity_type IN ('DESIGNING','CODING','DEBUGGING','TESTING','REVIEWING')),
            created_at TEXT DEFAULT (datetime('now')),
            last_active TEXT DEFAULT (datetime('now')),
            priority_score REAL DEFAULT 0.0
        );
        CREATE TABLE IF NOT EXISTS time_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            start_time TEXT NOT NULL,
            end_time TEXT DEFAULT NULL,
            duration_secs INTEGER DEFAULT 0,
            activity_type TEXT DEFAULT 'CODING' CHECK(activity_type IN ('DESIGNING','CODING','DEBUGGING','TESTING','REVIEWING'))
        );
        CREATE TABLE IF NOT EXISTS context_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            working_notes TEXT DEFAULT '',
            file_links_json TEXT DEFAULT '[]',
            saved_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS code_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            path_or_url TEXT NOT NULL,
            added_at TEXT DEFAULT (datetime('now'))
        );
    """
    )
    conn.commit()
    conn.close()
    print(f"DB ready: {DB_PATH}")


if __name__ == "__main__":
    init_db()
