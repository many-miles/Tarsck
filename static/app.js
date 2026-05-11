let tasks = [],
  activeTaskId = null,
  suggestedId = null,
  timerInterval = null,
  timerStartTs = null,
  activeEntryId = null;
let activityTypeByTask = {};

const ATYPES = ["DESIGNING", "CODING", "DEBUGGING", "TESTING", "REVIEWING"];
const STYPES = ["OPEN", "IN_PROGRESS", "BLOCKED", "COMPLETE"];
async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "API error");
  return data;
}
function toast(msg, isErr = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.toggle("error", isErr);
  el.classList.add("show");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove("show"), 3000);
}
async function loadTasks() {
  const data = await api("GET", "/api/tasks");
  tasks = data.tasks;
  suggestedId = data.suggestion;
  renderSidebar();
  const cnt = document.getElementById("task-count");
  if (cnt)
    cnt.textContent = `${tasks.filter((t) => t.status !== "COMPLETE").length} active`;
  if (activeTaskId) {
    const t = tasks.find((t) => t.id === activeTaskId);
    if (t) {
      const preservedNotes = document.getElementById("ctx-notes")?.value || "";
      renderDetail(t);
      const notesEL = document.getElementById("ctx-notes");
      if (notesEL) notesEL.value = preservedNotes;
    } else {
      showEmpty();
    }
  }
}
function renderSidebar() {
  const list = document.getElementById("task-list");
  list.innerHTML = "";
  if (!tasks.length) {
    list.innerHTML =
      '<div style="text-align:center;color:var(--muted);padding:32px 16px;font-size:13px;">No tasks yet.<br>Click + New Task to begin.</div>';
    return;
  }
  tasks.forEach((t) => {
    const card = document.createElement("div");
    card.className =
      "task-card" +
      (t.id === activeTaskId ? " active" : "") +
      (t.id === suggestedId ? " suggested" : "") +
      (t.status === "COMPLETE" ? " complete" : "");
    card.dataset.id = t.id;
    const dots = [1, 2, 3, 4, 5]
      .map((i) => `<span class="${i <= t.complexity ? "filled" : ""}"></span>`)
      .join("");
    card.innerHTML = `
      <div class="task-card-title">${esc(t.title)}</div>
      <div class="task-card-meta">
        <span class="badge badge-status-${t.status}">${fmtS(t.status)}</span>
        <span class="badge badge-type">${t.activity_type}</span>
        ${t.status !== "COMPLETE" ? `<span class="badge badge-score">${(t.priority_score * 100).toFixed(0)}%</span>` : ""}
        ${t.total_time !== "0m" ? `<span class="badge badge-time">${t.total_time}</span>` : ""}
        <div class="complexity-dots">${dots}</div>
      </div>`;
    card.addEventListener("click", () => selectTask(t.id));
    list.appendChild(card);
  });
}
async function selectTask(id) {
  if (activeTaskId === id) return;
  const currentSelect = document.getElementById("activity-select");
  if (currentSelect && activeTaskId)
    activityTypeByTask[activeTaskId] = currentSelect.value;
  if (activeTaskId) {
    const notes = document.getElementById("ctx-notes")?.value || "";
    try {
      await api("POST", "/api/tasks/switch", {
        from_id: activeTaskId,
        to_id: id,
        working_notes: notes,
      });
    } catch (_) {}
  }
  activeTaskId = id;
  const task = tasks.find((t) => t.id === id);
  if (task) renderDetail(task);
  try {
    const snap = await api("GET", `/api/tasks/${id}/snapshot`);
    if (snap.snapshot) applySnap(snap.snapshot);
  } catch (_) {}
  renderSidebar();
}
function applySnap(snap) {
  const n = document.getElementById("ctx-notes");
  if (n) n.value = snap.working_notes || "";
  const m = document.getElementById("ctx-saved");
  if (m && snap.saved_at)
    m.textContent = `Last saved: ${new Date(snap.saved_at).toLocaleString()}`;
}
function renderDetail(task) {
  clearInterval(timerInterval);
  timerInterval = null;
  if (!task.timer_active) {
    timerStartTs = null;
    activeEntryId = null;
  }
  const panel = document.getElementById("detail-panel");
  const dots = [1, 2, 3, 4, 5]
    .map((i) => `<span class="${i <= task.complexity ? "filled" : ""}"></span>`)
    .join("");
  const isComplete = task.status === "COMPLETE";
  const isRunning = !!task.timer_active;
  const timeRows =
    Object.entries(task.time_by_type || {})
      .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`)
      .join("") ||
    '<tr><td colspan="2" style="color:var(--muted)">No time logged yet.</td></tr>';
  const pr = task.priority_result;
  const bars = pr
    ? `
    <div class="score-bar-wrap"><div class="score-bar-label"><span>Deadline Urgency</span><span>${(pr.deadline_component * 100).toFixed(0)}%</span></div><div class="score-bar"><div class="score-bar-fill fill-deadline" style="width:${pr.deadline_component * 100}%"></div></div></div>
    <div class="score-bar-wrap"><div class="score-bar-label"><span>Complexity</span><span>${(pr.complexity_component * 100).toFixed(0)}%</span></div><div class="score-bar"><div class="score-bar-fill fill-complexity" style="width:${pr.complexity_component * 100}%"></div></div></div>
    <div class="score-bar-wrap"><div class="score-bar-label"><span>Idle Time</span><span>${(pr.idle_component * 100).toFixed(0)}%</span></div><div class="score-bar"><div class="score-bar-fill fill-idle" style="width:${pr.idle_component * 100}%"></div></div></div>
    <div style="font-size:12px;color:var(--muted);margin-top:6px;">Score: <strong>${(task.priority_score * 100).toFixed(1)}%</strong>${task.priority_rank ? ` · Rank #${task.priority_rank}` : ""}</div>`
    : '<p style="color:var(--muted);font-size:13px">Task is complete — not ranked.</p>';
  const linkItems = (task.code_links || [])
    .map(
      (l) =>
        `<li class="link-item"><span title="${esc(l.path_or_url)}">${esc(l.path_or_url)}</span><button class="btn btn-sm btn-ghost" onclick="deleteLink(${l.id})">✕</button></li>`,
    )
    .join("");
  panel.innerHTML = `
    <div class="task-detail-header">
      <div class="task-detail-main">
        <div class="task-detail-title">${esc(task.title)}</div>
        <div class="task-detail-meta">
          <span class="badge badge-status-${task.status}">${fmtS(task.status)}</span>
          <span class="badge badge-type">${task.activity_type}</span>
          ${task.deadline ? `<span class="badge badge-type">${task.deadline}</span>` : ""}
          <div class="complexity-dots" title="Complexity ${task.complexity}/5">${dots}</div>
          ${task.total_time !== "0m" ? `<span class="badge badge-time">${task.total_time}</span>` : ""}
        </div>
        ${task.description ? `<p style="margin-top:10px;font-size:13.5px;color:var(--muted)">${esc(task.description)}</p>` : ""}
      </div>
      <div class="detail-actions">
        ${!isComplete ? `<button class="btn btn-secondary" onclick="openEditModal(${task.id})">Edit</button>` : ""}
        ${!isComplete ? `<button class="btn btn-success" onclick="completeTask(${task.id})">Complete</button>` : ""}
        <button class="btn btn-danger btn-sm" onclick="deleteTask(${task.id})">Delete</button>
      </div>
    </div>
    ${
      !isComplete
        ? `
    <div class="card"><h3>Dev Activity Timer</h3>
      <div class="timer-display" id="timer-display">00:00:00</div>
      <div class="timer-controls">
        ${
          !isRunning
            ? `<button class="btn btn-primary" onclick="startTimer(${task.id})">▶ Start</button>`
            : `<select class="form-control" id="activity-select" style="width:160px">${ATYPES.map((a) => `<option value="${a}" ${a === (activityTypeByTask[task.id] || task.activity_type) ? "selected" : ""}>${a}</option>`).join("")}</select>
            <button class="btn btn-warn" onclick="stopTimer(${task.timer_active})">⏹ Stop & Log</button>`
        }
      </div>
    </div>`
        : ""
    }
    <div class="card"><h3>Time by Activity</h3>
      <table class="time-table"><thead><tr><th>Activity</th><th>Time Logged</th></tr></thead><tbody>${timeRows}</tbody></table>
    </div>
    <div class="card"><h3>Priority Score Breakdown</h3>${bars}</div>
    <div class="card"><h3>Code File Links</h3>
      <ul class="link-list" id="link-list">${linkItems}</ul>
      <div class="link-add-row">
        <input class="form-control" id="link-input" placeholder="/path/to/file.py or https://github.com/…"/>
        <button class="btn btn-secondary" onclick="addLink(${task.id})">+ Add</button>
      </div>
    </div>
    <div class="card"><h3>Context Snapshot</h3>
      <textarea class="snapshot-notes" id="ctx-notes" placeholder="Working notes, hypothesis, where you left off…" rows="4"></textarea>
      <div class="snapshot-meta" id="ctx-saved"></div>
      <div class="switch-bar">
        <button class="btn btn-secondary" onclick="saveSnapshot(${task.id})">Save Snapshot</button>
        <span style="color:var(--muted);font-size:12px">Snapshots are also saved automatically when switching tasks.</span>
      </div>
    </div>`;
  if (isRunning && task.timer_active) {
    activeEntryId = task.timer_active;
    timerStartTs = task.timer_start
      ? new Date(task.timer_start).getTime()
      : Date.now();
    startTimerDisplay();
  }
}
function showEmpty() {
  document.getElementById("detail-panel").innerHTML =
    `<div class="empty-state"><p>Select a task to view details</p><button class="btn btn-primary" onclick="openNewTaskModal()">+ New Task</button></div>`;
}
function startTimerDisplay() {
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const el = document.getElementById("timer-display");
    if (!el) {
      clearInterval(timerInterval);
      return;
    }
    el.textContent = fmtSec(Math.floor((Date.now() - timerStartTs) / 1000));
  }, 1000);
}
async function startTimer(tid) {
  try {
    const d = await api("POST", `/api/tasks/${tid}/timer/start`);
    activeEntryId = d.entry_id;
    toast("Timer started");
    await loadTasks();
  } catch (e) {
    toast(e.message, true);
  }
}
async function stopTimer(eid) {
  const atype = document.getElementById("activity-select")?.value || "CODING";
  try {
    const d = await api("POST", `/api/timer/${eid}/stop`, {
      activity_type: atype,
    });
    clearInterval(timerInterval);
    activeEntryId = null;
    toast(`Logged ${d.duration_fmt} of ${atype}`);
    await loadTasks();
  } catch (e) {
    toast(e.message, true);
  }
}
async function saveSnapshot(tid) {
  const notes = document.getElementById("ctx-notes")?.value || "";
  try {
    await api("POST", `/api/tasks/${tid}/snapshot`, {
      working_notes: notes,
    });
    document.getElementById("ctx-saved").textContent =
      `Last saved: ${new Date().toLocaleString()}`;
    toast("Snapshot saved");
  } catch (e) {
    toast(e.message, true);
  }
}
async function addLink(tid) {
  const inp = document.getElementById("link-input");
  const path = inp.value.trim();
  if (!path) {
    toast("Enter a file path or URL", true);
    return;
  }
  try {
    await api("POST", `/api/tasks/${tid}/links`, { path_or_url: path });
    inp.value = "";
    await loadTasks();
    toast("Link added");
  } catch (e) {
    toast(e.message, true);
  }
}
async function deleteLink(lid) {
  try {
    await api("DELETE", `/api/links/${lid}`);
    await loadTasks();
  } catch (e) {
    toast(e.message, true);
  }
}
async function completeTask(id) {
  try {
    await api("POST", `/api/tasks/${id}/complete`);
    toast("Task complete ✓");
    activeTaskId = null;
    await loadTasks();
    showEmpty();
  } catch (e) {
    toast(e.message, true);
  }
}
async function deleteTask(id) {
  if (!confirm("Delete this task and all its data?")) return;
  try {
    await api("DELETE", `/api/tasks/${id}`);
    toast("Task deleted");
    activeTaskId = null;
    await loadTasks();
    showEmpty();
  } catch (e) {
    toast(e.message, true);
  }
}
function openNewTaskModal() {
  showModal({
    title: "New Task",
    fields: taskFields(),
    onSubmit: async (d) => {
      await api("POST", "/api/tasks", d);
      toast("Task created");
      await loadTasks();
    },
  });
}
function openEditModal(id) {
  const task = tasks.find((t) => t.id === id);
  if (!task) return;
  showModal({
    title: "Edit Task",
    fields: taskFields(task),
    onSubmit: async (d) => {
      await api("PUT", `/api/tasks/${id}`, d);
      toast("Updated");
      await loadTasks();
    },
  });
}
function taskFields(t = {}) {
  return `
    <div class="form-group"><label>Title *</label><input class="form-control" name="title" required value="${esc(t.title || "")}" placeholder="e.g. Fix login bug"></div>
    <div class="form-group"><label>Description</label><textarea class="form-control" name="description" rows="2">${esc(t.description || "")}</textarea></div>
    <div class="form-row">
      <div class="form-group"><label>Deadline</label><input class="form-control" name="deadline" type="date" value="${t.deadline || ""}"></div>
      <div class="form-group"><label>Complexity (1–5)</label><input class="form-control" name="complexity" type="number" min="1" max="5" value="${t.complexity || 3}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Status</label><select class="form-control" name="status">${STYPES.map((s) => `<option value="${s}" ${t.status === s ? "selected" : ""}>${fmtS(s)}</option>`).join("")}</select></div>
      <div class="form-group"><label>Primary Activity</label><select class="form-control" name="activity_type">${ATYPES.map((a) => `<option value="${a}" ${t.activity_type === a ? "selected" : ""}>${a}</option>`).join("")}</select></div>
    </div>`;
}
function showModal({ title, fields, onSubmit }) {
  const ov = document.createElement("div");
  ov.className = "modal-overlay";
  ov.innerHTML = `<div class="modal"><h2>${title}</h2><form id="modal-form">${fields}<div class="modal-actions"><button type="button" class="btn btn-secondary" id="mc">Cancel</button><button type="submit" class="btn btn-primary">Save</button></div></form></div>`;
  document.body.appendChild(ov);
  ov.querySelector("#mc").onclick = () => ov.remove();
  ov.addEventListener("click", (e) => {
    if (e.target === ov) ov.remove();
  });
  ov.querySelector("#modal-form").onsubmit = async (e) => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target).entries());
    try {
      await onSubmit(d);
      ov.remove();
    } catch (err) {
      toast(err.message, true);
    }
  };
  setTimeout(() => ov.querySelector("input,textarea")?.focus(), 50);
}
function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
function fmtS(s) {
  return (
    {
      OPEN: "Open",
      IN_PROGRESS: "In Progress",
      BLOCKED: "Blocked",
      COMPLETE: "Complete",
    }[s] || s
  );
}
function fmtSec(s) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return [h, m, sec].map((n) => String(n).padStart(2, "0")).join(":");
}
document.addEventListener("DOMContentLoaded", async () => {
  showEmpty();
  await loadTasks();
  document
    .getElementById("btn-new-task")
    .addEventListener("click", openNewTaskModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "n" && !e.target.closest("input,textarea,select"))
      openNewTaskModal();
  });
});
