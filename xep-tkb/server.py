"""
Máy chủ web cho hệ thống xếp thời khóa biểu.
KHÔNG cần cài thêm thư viện nào, chỉ dùng thư viện có sẵn của Python.

Chạy:   python server.py
Rồi trình duyệt tự mở trang. Nhấn Ctrl+C trong terminal để tắt.

Cấu trúc thư mục:
    main.py          code xếp lịch (Scheduler, DSATUR, ...)
    server.py        file này: phát trang web và nhận dữ liệu từ trang
    web/index.html   giao diện
"""
import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from main import Problem, Room, Scheduler, Section, can_use, parse_busy, validate

BASE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(BASE, "web", "index.html")
FIRST_PORT = 8000


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


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, obj):
        self._send(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path in ("/", "/index.html"):
            try:
                with open(INDEX, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                msg = ("Không tìm thấy web/index.html.\n"
                       "Hãy giữ nguyên cấu trúc thư mục: server.py nằm cạnh thư mục web.")
                self._send(404, msg.encode("utf-8"), "text/plain; charset=utf-8")
        else:
            self._send(404, "Không tìm thấy trang này.".encode("utf-8"), "text/plain; charset=utf-8")

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/schedule":
            self._json(404, {"error": "Không tìm thấy."})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            self._json(400, {"error": "Dữ liệu gửi lên không hợp lệ."})
            return
        try:
            self._json(200, solve(data))
        except BadInput as e:
            self._json(400, {"error": str(e)})
        except Exception as e:  # lỗi bất ngờ trong thuật toán: báo cho trang thay vì treo
            self._json(500, {"error": f"Lỗi khi xếp lịch: {e}"})

    def log_message(self, fmt, *args):
        print("  " + (fmt % args))


def make_server():
    for port in range(FIRST_PORT, FIRST_PORT + 20):
        try:
            return ThreadingHTTPServer(("127.0.0.1", port), Handler), port
        except OSError:
            continue
    raise SystemExit("Không mở được cổng nào từ %d đến %d. Hãy tắt chương trình đang chiếm cổng." % (FIRST_PORT, FIRST_PORT + 19))


def main():
    if not os.path.exists(INDEX):
        raise SystemExit("Không thấy web/index.html. Giữ nguyên cấu trúc: server.py nằm cạnh thư mục web.")
    server, port = make_server()
    url = f"http://127.0.0.1:{port}/"
    print("=" * 56)
    print(" Xếp thời khóa biểu đang chạy tại:", url)
    print(" Nhấn Ctrl+C để tắt.")
    print("=" * 56)
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã tắt.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
