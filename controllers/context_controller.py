import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from flask import Blueprint, request, jsonify
from repositories.context_repository import ContextRepository
from repositories.task_repository import TaskRepository

ctx_bp = Blueprint("context", __name__)
repo = ContextRepository()
task_repo = TaskRepository()


@ctx_bp.route("/api/tasks/switch", methods=["POST"])
def switch_task():
    d = request.get_json() or {}
    from_id = d.get("from_id")
    to_id = d.get("to_id")
    notes = d.get("working_notes", "")
    if from_id and task_repo.get_by_id(from_id):
        persistent_links = [
            cl["path_or_url"]
            for cl in task_repo.get_code_links(from_id)
        ]
        repo.save_snapshot(from_id, notes, json.dumps(persistent_links))
        task_repo.touch(from_id)
    snap = None
    if to_id and task_repo.get_by_id(to_id):
        s = repo.get_latest(to_id)
        if s:
            snap = {
                "task_id": s["task_id"],
                "working_notes": s["working_notes"],
                "file_links": json.loads(s["file_links_json"] or "[]"),
                "saved_at": s["saved_at"],
            }
        task_repo.touch(to_id)
    return jsonify({"saved_from": from_id, "arriving_snapshot": snap})


@ctx_bp.route("/api/tasks/<int:tid>/snapshot", methods=["GET"])
def get_snapshot(tid):
    if not task_repo.get_by_id(tid):
        return jsonify({"error": "Not found"}), 404
    s = repo.get_latest(tid)
    if not s:
        return jsonify({"snapshot": None})
    return jsonify(
        {
            "snapshot": {
                "task_id": s["task_id"],
                "working_notes": s["working_notes"],
                "file_links": json.loads(s["file_links_json"] or "[]"),
                "saved_at": s["saved_at"],
            }
        }
    )


@ctx_bp.route("/api/tasks/<int:tid>/snapshot", methods=["POST"])
def save_snapshot(tid):
    if not task_repo.get_by_id(tid):
        return jsonify({"error": "Not found"}), 404
    d = request.get_json() or {}
    persistent_links = [
        cl["path_or_url"]
        for cl in task_repo.get_code_links(tid)
    ]
    repo.save_snapshot(
        tid, d.get("working_notes", ""), json.dumps(persistent_links))
    return jsonify({"saved": True, "task_id": tid})


@ctx_bp.route("/api/tasks/<int:tid>/snapshot", methods=["DELETE"])
def clear_snapshot(tid):
    repo.delete(tid)
    return jsonify({"cleared": tid})
