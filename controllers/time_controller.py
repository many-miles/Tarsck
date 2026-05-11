import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from flask import Blueprint, request, jsonify
from repositories.time_repository import TimeRepository
from repositories.task_repository import TaskRepository
from datetime import datetime

time_bp = Blueprint("time", __name__)
repo = TimeRepository()
task_repo = TaskRepository()
VALID = {"DESIGNING", "CODING", "DEBUGGING", "TESTING", "REVIEWING"}


def _fmt(s):
    if not s:
        return "0m"
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if sec and not h:
        parts.append(f"{sec}s")
    return " ".join(parts) or "0m"


@time_bp.route("/api/tasks/<int:tid>/timer/start", methods=["POST"])
def start_timer(tid):
    if not task_repo.get_by_id(tid):
        return jsonify({"error": "Not found"}), 404
    ex = repo.get_active_entry(tid)
    if ex:
        now = datetime.now()
        diff = int((now - datetime.fromisoformat(ex["start_time"])).total_seconds())
        preserved_type = ex.get("activity_type") or "CODING"
        repo.stop(ex["id"], now.isoformat(), diff, preserved_type)
    start = datetime.now().isoformat()
    eid = repo.insert(tid, start)
    task_repo.touch(tid)
    return jsonify({"entry_id": eid, "start_time": start}), 201


@time_bp.route("/api/timer/<int:eid>/stop", methods=["POST"])
def stop_timer(eid):
    d = request.get_json() or {}
    atype = d.get("activity_type", "CODING").upper()
    if atype not in VALID:
        atype = "CODING"
    row = repo.get_by_id(eid)
    if not row:
        return jsonify({"error": "Not found"}), 404
    start = datetime.fromisoformat(row["start_time"])
    end = datetime.now()
    dur = int((end - start).total_seconds())
    repo.stop(eid, end.isoformat(), dur, atype)
    task_repo.touch(row["task_id"])
    return jsonify(
        {
            "entry_id": eid,
            "duration_secs": dur,
            "duration_fmt": _fmt(dur),
            "activity_type": atype,
        }
    )


@time_bp.route("/api/tasks/<int:tid>/time-summary", methods=["GET"])
def time_summary(tid):
    if not task_repo.get_by_id(tid):
        return jsonify({"error": "Not found"}), 404
    bt = repo.get_total_by_type(tid)
    tot = repo.get_grand_total(tid)
    return jsonify(
        {
            "task_id": tid,
            "total": _fmt(tot),
            "total_secs": tot,
            "by_type": {k: {"secs": v, "fmt": _fmt(v)} for k, v in bt.items()},
        }
    )
