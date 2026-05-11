import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db_init import get_connection


class ContextRepository:
    def save_snapshot(self, tid, notes, links_json):
        c = get_connection()
        c.execute("DELETE FROM context_snapshots WHERE task_id=?", (tid,))
        c.execute(
            "INSERT INTO context_snapshots(task_id,working_notes,file_links_json) VALUES(?,?,?)",
            (tid, notes, links_json),
        )
        c.commit()
        c.close()

    def get_latest(self, tid):
        c = get_connection()
        r = c.execute(
            "SELECT * FROM context_snapshots WHERE task_id=? ORDER BY saved_at DESC LIMIT 1",
            (tid,),
        ).fetchone()
        c.close()
        return dict(r) if r else None

    def delete(self, tid):
        c = get_connection()
        c.execute("DELETE FROM context_snapshots WHERE task_id=?", (tid,))
        c.commit()
        c.close()
