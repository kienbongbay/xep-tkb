"""Đọc và ghi dữ liệu bài toán dạng JSON (file data.json)."""
import json

from .models import Problem, Room, Section


def load_problem(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    rooms = [Room(**r) for r in d["rooms"]]
    secs = [Section(**s) for s in d["sections"]]
    busy = {}
    for t, items in d.get("teacher_busy", {}).items():
        busy[t] = {(x[0], x[1]) for x in items}
    return Problem(rooms, secs, busy)


def save_problem(problem, path="data.json"):
    data = {
        "rooms": [r.__dict__ for r in problem.rooms],
        "sections": [s.__dict__ for s in problem.sections],
        "teacher_busy": {
            t: sorted([list(x) for x in v], key=lambda z: (z[0], z[1] or 0))
            for t, v in problem.teacher_busy.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
