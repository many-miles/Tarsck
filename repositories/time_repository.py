import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db_init import get_connection


class TimeRepository:
    def insert(self, tid, start):
        c = get_connection()
        cur = c.execute(
            "INSERT INTO time_entries(task_id,start_time) VALUES(?,?)", (tid, start)
        )
        c.commit()
        id = cur.lastrowid
        c.close()
        return id

    def stop(self, id, end, dur, atype):
        c = get_connection()
        c.execute(
            "UPDATE time_entries SET end_time=?,duration_secs=?,activity_type=? WHERE id=?",
            (end, dur, atype, id),
        )
        c.commit()
        c.close()

    def get_active_entry(self, tid):
        c = get_connection()
        r = c.execute(
            "SELECT * FROM time_entries WHERE task_id=? AND end_time IS NULL ORDER BY start_time DESC LIMIT 1",
            (tid,),
        ).fetchone()
        c.close()
        return dict(r) if r else None

    def get_by_id(self, id):
        c = get_connection()
        r = c.execute(
            "SELECT * FROM time_entries WHERE id=?", (id,)
            ).fetchone()
        c.close()
        return dict(r) if r else None

    def get_total_by_type(self, tid):
        c = get_connection()
        rows = c.execute(
            "SELECT activity_type,SUM(duration_secs) as total FROM time_entries WHERE task_id=? AND end_time IS NOT NULL GROUP BY activity_type",
            (tid,),
        ).fetchall()
        c.close()
        return {r["activity_type"]: r["total"] for r in rows}

    def get_grand_total(self, tid):
        c = get_connection()
        r = c.execute(
            "SELECT COALESCE(SUM(duration_secs),0) as total FROM time_entries WHERE task_id=? AND end_time IS NOT NULL",
            (tid,),
        ).fetchone()
        c.close()
        return r["total"] if r else 0
