# TARSCK — Developer Task Management System

---

## What Is Tarsck?

Tarsck is a task management tool built specifically for developers. The name embeds the initials **RSC** (Ruben Sauer Cloete) into the word "task" — T-a-**R**-**S**-**C**-k.

---

## The Four Differentiating Features

### 1. Context Snapshots

When you switch from one task to another, Tarsck automatically saves your working notes and any file paths you had open. When you come back to that task later, it restores them. This addresses the developer problem of losing your mental context.

### 2. Code File Linking

You can attach file paths (`/src/auth/login.py`) or repository URLs (`https://github.com/...`) directly to a task. These links are stored in the database and shown in the task detail panel so you can jump straight to the relevant code.

### 3. Development Activity Timer

The built-in timer lets you tag time by activity type: **DESIGNING**, **CODING**, **DEBUGGING**, **TESTING**, or **REVIEWING**. When you stop the timer you pick the category, and Tarsck builds up a breakdown per task so you can see where your time goes.

### 4. Automated Priority Scoring

Every task gets a priority score from 0 to 100% calculated from three weighted factors:

- **Deadline urgency** (50%) — how close the deadline is, scaled over 30 days
- **Complexity** (30%) — the task's complexity rating from 1 to 5
- **Idle time** (20%) — how long since you last touched the task, scaled over 14 days

The task with the highest score gets an **Suggested** badge in the sidebar. Completed tasks are excluded from scoring.

---

## Setup and Run

```bash
git clone https://github.com/many-miles/Tarsck.git
cd Tarsck
pip3 install flask
python3 app.py
```

Open your browser at: **<http://localhost:5000>**

The database (`tarsck.db`) is created automatically on first run.

---

## File Structure

```text
tarsck/
│
├── app.py
├── db_init.py
├── priority_scorer.py
├── tarsck.db
│
├── controllers/
│   ├── __init__.py
│   ├── task_controller.py
│   ├── time_controller.py
│   └── context_controller.py
│
├── repositories/
│   ├── __init__.py
│   ├── task_repository.py
│   ├── time_repository.py
│   └── context_repository.py
│
├── static/
│   ├── app.js
│   └── styles.css
│
├── templates/
│    └── index.html
│
└── docs/
    └── ProjectDiagrams.html         # Diagrams as presented in the Project Report
```

---

## API Endpoints

### Task Management

```text
GET     |   api/tasks                          |   Get all tasks with ranking and suggestions
POST    |   api/tasks                          |   Create a new task
PUT     |   api/tasks/<int:id>                 |   Update a task
DELETE  |   api/tasks/<int:id>                 |   Delete a task
POST    |   api/tasks/<int:id>/complete        |   Mark task as complete

### Code Links

POST    |   api/tasks/<int:id>/links           |   Add a code file/URL link to a task
DELETE  |   api/links/<int:lid>                |   Delete a code link

### Context Snapshots

POST    |   api/tasks/switch                   |   Switch between tasks (saves context from one, restores to another)
GET     |   api/tasks/<int:tid>/snapshot       |   Get saved snapshot for a task
POST    |   api/tasks/<int:tid>/snapshot       |   Save working notes snapshot
DELETE  |   api/tasks/<int:tid>/snapshot       |   Clear snapshot for a task

### Time Tracking

POST    |   api/tasks/<int:tid>/timer/start    |   Start timer for a task
POST    |   api/timer/<int:eid>/stop           |   Stop timer entry (specify activity_type)
GET     |   api/tasks/<int:tid>/time-summary   |   Get time breakdown by activity type
```
