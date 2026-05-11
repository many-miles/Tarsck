import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from flask import Blueprint, request, jsonify
from repositories.task_repository import TaskRepository
from repositories.time_repository import TimeRepository
from priority_scorer import SuggestionEngine

task_bp = Blueprint("tasks", __name__)
repo = TaskRepository()
time_repo = TimeRepository()
engine = SuggestionEngine()


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


def _enrich(t):
    t["code_links"] = repo.get_code_links(t["id"])
    bt = time_repo.get_total_by_type(t["id"])
    tot = time_repo.get_grand_total(t["id"])
    t["time_by_type"] = {k: _fmt(v) for k, v in bt.items()}
    t["total_time"] = _fmt(tot)
    ae = time_repo.get_active_entry(t["id"])
    t["timer_active"] = ae["id"] if ae else None
    t["timer_start"] = ae["start_time"] if ae else None
    return t


@task_bp.route("/api/tasks", methods=["GET"])
def get_tasks():
    tasks = repo.get_all()
    ranked = engine.get_ranked_list(tasks)
    enriched = [_enrich(t) for t in ranked]
    sug = engine.get_top_suggestion(tasks)
    return jsonify({"tasks": enriched, "suggestion": sug["id"] if sug else None})


@task_bp.route("/api/tasks", methods=["POST"])
def create_task():
    d = request.get_json()
    if not d or not d.get("title", "").strip():
        return jsonify({"error": "Title required"}), 400
    id = repo.insert(d)
    return jsonify(_enrich(repo.get_by_id(id))), 201


@task_bp.route("/api/tasks/<int:id>", methods=["PUT"])
def update_task(id):
    if not repo.get_by_id(id):
        return jsonify({"error": "Not found"}), 404
    repo.update(id, request.get_json())
    repo.touch(id)
    return jsonify(_enrich(repo.get_by_id(id)))


@task_bp.route("/api/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):
    if not repo.get_by_id(id):
        return jsonify({"error": "Not found"}), 404
    repo.delete(id)
    return jsonify({"deleted": id})


@task_bp.route("/api/tasks/<int:id>/complete", methods=["POST"])
def complete_task(id):
    if not repo.get_by_id(id):
        return jsonify({"error": "Not found"}), 404
    repo.mark_complete(id)
    return jsonify(_enrich(repo.get_by_id(id)))


@task_bp.route("/api/tasks/<int:id>/links", methods=["POST"])
def add_link(id):
    if not repo.get_by_id(id):
        return jsonify({"error": "Not found"}), 404
    d = request.get_json() or {}
    path = d.get("path_or_url", "").strip()
    if not path:
        return jsonify({"error": "path_or_url required"}), 400
    lid = repo.add_code_link(id, path)
    return jsonify({"id": lid, "task_id": id, "path_or_url": path}), 201


@task_bp.route("/api/links/<int:lid>", methods=["DELETE"])
def delete_link(lid):
    repo.delete_code_link(lid)
    return jsonify({"deleted": lid})
