"""Cầu nối giữa trang web và thuật toán: kiểm tra dữ liệu gửi lên rồi xếp lịch."""
import time

from .busy import parse_busy
from .models import Problem, Room, Section
from .rooms import can_use
from .scheduler import Scheduler
from .validate import validate


class BadInput(Exception):
    """Dữ liệu người dùng gửi lên không hợp lệ (trả về HTTP 400)."""


def to_int(value, label, lo=1, hi=None):
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise BadInput(f"{label}: phải là số nguyên")
    if n < lo or (hi is not None and n > hi):
        rng = f"từ {lo} đến {hi}" if hi is not None else f"từ {lo} trở lên"
        raise BadInput(f"{label}: phải {rng}")
    return n


def to_text(value, label):
    text = str(value if value is not None else "").strip()
    if not text:
        raise BadInput(f"{label}: không được để trống")
    return text


def build_problem(data):
    raw_rooms = data.get("rooms")
    raw_secs = data.get("sections")
    if not isinstance(raw_rooms, list) or not raw_rooms:
        raise BadInput("Chưa có phòng học nào.")
    if not isinstance(raw_secs, list) or not raw_secs:
        raise BadInput("Chưa có lớp học phần nào.")

    rooms, seen = [], set()
    for i, r in enumerate(raw_rooms, 1):
        rid = to_text(r.get("id"), f"Phòng thứ {i}: mã phòng")
        if rid in seen:
            raise BadInput(f"Mã phòng {rid} bị trùng.")
        seen.add(rid)
        rooms.append(Room(rid,
                          to_int(r.get("capacity"), f"Phòng {rid}: sức chứa"),
                          to_text(r.get("kind"), f"Phòng {rid}: loại phòng")))

    secs, seen = [], set()
    for i, s in enumerate(raw_secs, 1):
        sid = to_text(s.get("id"), f"Lớp học phần thứ {i}: mã")
        if sid in seen:
            raise BadInput(f"Mã lớp học phần {sid} bị trùng.")
        seen.add(sid)
        secs.append(Section(
            id=sid,
            name=str(s.get("name") or sid).strip() or sid,
            teacher=to_text(s.get("teacher"), f"{sid}: giảng viên"),
            group=to_text(s.get("group"), f"{sid}: lớp sinh viên"),
            students=to_int(s.get("students"), f"{sid}: sĩ số"),
            sessions=to_int(s.get("sessions"), f"{sid}: số buổi mỗi tuần", 1, 6),
            length=to_int(s.get("length"), f"{sid}: số tiết mỗi buổi", 1, 5),
            room_kind=to_text(s.get("roomKind"), f"{sid}: loại phòng cần"),
        ))

    busy = {}
    for teacher, text in (data.get("busy") or {}).items():
        try:
            parsed = parse_busy(str(text or ""))
        except ValueError:
            raise BadInput(f"Lịch bận của {teacher} sai định dạng (ví dụ 2:1-5, 7:all).")
        if parsed:
            busy[teacher] = parsed
    return Problem(rooms, secs, busy)


def sec_dict(sec):
    return {"id": sec.id, "name": sec.name, "teacher": sec.teacher, "group": sec.group}


def solve(data):
    """Nhận dict từ trang web, trả về dict kết quả."""
    problem = build_problem(data)
    sch = Scheduler(problem)
    t0 = time.perf_counter()
    failed = sch.run()
    ms = round((time.perf_counter() - t0) * 1000)

    sessions = []
    for vid, (day, start) in sorted(sch.color.items(), key=lambda kv: (kv[1], kv[0])):
        v = sch.verts[vid]
        sessions.append({
            "day": day,
            "start": start,
            "end": start + v.sec.length - 1,
            "idx": v.idx,
            "sec": sec_dict(v.sec),
            "room": {"id": sch.room_of[vid].id},
        })

    unplaced = []
    for v in failed:
        if any(can_use(r, v.sec) for r in problem.rooms):
            why = "không còn khung giờ trống phù hợp"
        else:
            why = "không có phòng đủ sức chứa và đúng loại"
        unplaced.append({"sec": sec_dict(v.sec), "idx": v.idx, "why": why})

    return {
        "total": len(sch.verts),
        "sessions": sessions,
        "unplaced": unplaced,
        "errors": validate(sch),
        "ms": ms,
    }
