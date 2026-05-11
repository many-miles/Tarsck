import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db_init import get_connection


class TaskRepository:
    def get_all(self):
        c = get_connection()
        rows = c.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        c.close()
        return [dict(r) for r in rows]

    def get_by_id(self, id):
        c = get_connection()
        r = c.execute("SELECT * FROM tasks WHERE id=?", (id,)).fetchone()
        c.close()
        return dict(r) if r else None

    def insert(self, d):
        c = get_connection()
        cur = c.execute(
            "INSERT INTO tasks(title,description,deadline,complexity,status,activity_type) VALUES(?,?,?,?,?,?)",
            (
                d.get("title", ""),
                d.get("description", ""),
                d.get("deadline") or None,
                int(d.get("complexity", 3)),
                d.get("status", "OPEN"),
                d.get("activity_type", "CODING"),
            ),
        )
        c.commit()
        id = cur.lastrowid
        c.close()
        return id

    def update(self, id, d):
        fields = []
        vals = []
        allowed = [
            "title",
            "description",
            "deadline",
            "complexity",
            "status",
            "activity_type",
            "priority_score",
        ]
        for k in allowed:
            if k in d:
                fields.append(f"{k}=?")
                vals.append(d[k])
        if not fields:
            return
        vals.append(id)
        c = get_connection()
        c.execute(f"UPDATE tasks SET {','.join(fields)} WHERE id=?", vals)
        c.commit()
        c.close()

    def touch(self, id):
        c = get_connection()
        c.execute("UPDATE tasks SET last_active=datetime('now') WHERE id=?", (id,))
        c.commit()
        c.close()

    def delete(self, id):
        c = get_connection()
        c.execute("DELETE FROM tasks WHERE id=?", (id,))
        c.commit()
        c.close()

    def mark_complete(self, id):
        c = get_connection()
        c.execute("UPDATE tasks SET status='COMPLETE' WHERE id=?", (id,))
        c.commit()
        c.close()

    def add_code_link(self, tid, path):
        c = get_connection()
        cur = c.execute(
            "INSERT INTO code_links(task_id,path_or_url) VALUES(?,?)", (tid, path)
        )
        c.commit()
        id = cur.lastrowid
        c.close()
        return id

    def get_code_links(self, tid):
        c = get_connection()
        rows = c.execute(
            "SELECT * FROM code_links WHERE task_id=? ORDER BY added_at", (tid,)
        ).fetchall()
        c.close()
        return [dict(r) for r in rows]

    def delete_code_link(self, id):
        c = get_connection()
        c.execute("DELETE FROM code_links WHERE id=?", (id,))
        c.commit()
        c.close()
