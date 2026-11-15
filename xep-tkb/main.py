#!/usr/bin/env python3
"""
Hệ thống tự động xếp thời khóa biểu
====================================
Ý tưởng:
  1. Mỗi TIẾT HỌC của một lớp học phần là một ĐỈNH của đồ thị.
  2. Hai đỉnh có CẠNH (xung đột) nếu cùng giảng viên, cùng nhóm sinh viên,
     hoặc là hai tiết của cùng một lớp học phần.
  3. MÀU = khung giờ (ngày, tiết). Tô màu bằng DSATUR (tham lam theo độ bão hòa).
  4. Khi chọn màu cho một đỉnh, kiểm tra thêm các ràng buộc "cứng":
       - giảng viên bận ở khung giờ đó
       - còn phòng phù hợp (sức chứa, loại phòng) -> ghép cặp cực đại (Kuhn)
     và chấm điểm "mềm" để chọn khung giờ tốt nhất (rải đều các ngày, ít tiết sớm/muộn).

Chạy:  python3 timetable.py [data.json] [--out thoikhoabieu.csv]
Nếu không có data.json sẽ dùng dữ liệu mẫu.
"""
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field

DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
PERIODS_PER_DAY = 10  # tiết 1..10


# ----------------------------------------------------------------- Dữ liệu
@dataclass
class Room:
    id: str
    capacity: int
    kind: str = "ly_thuyet"  # ly_thuyet | may_tinh | thuc_hanh ...


@dataclass
class Section:
    id: str            # mã lớp học phần
    name: str
    teacher: str
    group: str         # lớp sinh hoạt / nhóm sinh viên
    students: int
    sessions: int      # số buổi/tuần
    length: int = 3    # số tiết liên tiếp mỗi buổi
    room_kind: str = "ly_thuyet"


@dataclass
class Problem:
    rooms: list
    sections: list
    # teacher -> tập khung giờ bận {(day, start_period)} hoặc cả ngày (day, None)
    teacher_busy: dict = field(default_factory=dict)


# Khung giờ bắt đầu hợp lệ cho mỗi buổi: các "khối" để tránh buổi học vắt qua trưa.
def start_periods(length):
    blocks = [(1, 5), (6, 10)]  # sáng: tiết 1-5, chiều: tiết 6-10
    res = []
    for a, b in blocks:
        res.extend(range(a, b - length + 2))
    return res


# ------------------------------------------------------------ Đồ thị xung đột
@dataclass
class Vertex:
    vid: int
    sec: Section
    idx: int  # buổi thứ mấy của lớp học phần


def build_graph(problem):
    verts = []
    for s in problem.sections:
        for k in range(s.sessions):
            verts.append(Vertex(len(verts), s, k))
    adj = defaultdict(set)
    by_teacher, by_group, by_sec = defaultdict(list), defaultdict(list), defaultdict(list)
    for v in verts:
        by_teacher[v.sec.teacher].append(v.vid)
        by_group[v.sec.group].append(v.vid)
        by_sec[v.sec.id].append(v.vid)
    for bucket in (by_teacher, by_group, by_sec):
        for ids in bucket.values():
            for i in ids:
                for j in ids:
                    if i != j:
                        adj[i].add(j)
    return verts, adj


# --------------------------------------------------------- Ghép phòng (Kuhn)
def can_use(room, sec):
    return room.kind == sec.room_kind and room.capacity >= sec.students


def match_rooms(vertices_in_slot, rooms):
    """Kiểm tra mọi đỉnh trong cùng một khung giờ có thể được gán phòng khác nhau.
    Trả về dict vid -> room hoặc None nếu không ghép được."""
    owner = {}  # room.id -> vid

    def try_assign(v, seen):
        for r in rooms:
            if not can_use(r, v.sec) or r.id in seen:
                continue
            seen.add(r.id)
            if r.id not in owner or try_assign(owner[r.id], seen):
                owner[r.id] = v
                return True
        return False

    # đỉnh khó (nhiều sinh viên) trước
    for v in sorted(vertices_in_slot, key=lambda x: -x.sec.students):
        if not try_assign(v, set()):
            return None
    return {v.vid: next(r for r in rooms if r.id == rid) for rid, v in owner.items()}


# -------------------------------------------------------------- Bộ xếp lịch
class Scheduler:
    def __init__(self, problem):
        self.p = problem
        self.verts, self.adj = build_graph(problem)
        self.color = {}        # vid -> (day, start)
        self.room_of = {}      # vid -> Room
        # slot -> list[Vertex]; slot chiếm các tiết [start, start+length)
        self.occupied = defaultdict(list)  # (day, period) -> list[Vertex]
        self.rooms_by_id = {r.id: r for r in problem.rooms}

    # -- tiện ích
    def covered(self, v, slot):
        d, s = slot
        return [(d, s + i) for i in range(v.sec.length)]

    def teacher_free(self, v, slot):
        busy = self.p.teacher_busy.get(v.sec.teacher, set())
        for d, p in self.covered(v, slot):
            if (d, p) in busy or (d, None) in busy:
                return False
        return True

    def neighbor_free(self, v, slot):
        """Không cạnh nào của v bị chồng thời gian."""
        mine = set(self.covered(v, slot))
        for u in self.adj[v.vid]:
            if u in self.color:
                other = set(self.covered(self.verts[u], self.color[u]))
                if mine & other:
                    return False
        return True

    def rooms_ok(self, v, slot):
        """Với mỗi tiết bị phủ, tập đỉnh cùng tiết + v phải ghép được phòng."""
        for cell in self.covered(v, slot):
            group = self.occupied[cell] + [v]
            if match_rooms(group, self.p.rooms) is None:
                return False
        return True

    def soft_cost(self, v, slot):
        d, s = slot
        cost = 0
        # rải đều các buổi của cùng lớp học phần vào ngày khác nhau
        for u in self.adj[v.vid]:
            if u in self.color and self.verts[u].sec.id == v.sec.id:
                ud, _ = self.color[u]
                if ud == d:
                    cost += 50
                elif abs(ud - d) == 1:
                    cost += 5
        # nhóm sinh viên: tránh học quá nhiều tiết trong 1 ngày
        load = sum(1 for cell, vs in self.occupied.items()
                   if cell[0] == d for x in vs if x.sec.group == v.sec.group)
        cost += load * 2
        # tránh tiết sớm 1 và tiết muộn
        if s == 1:
            cost += 3
        if s + v.sec.length - 1 >= 9:
            cost += 4
        # ưu tiên Thứ 7 cuối cùng
        if d == 5:
            cost += 15
        # thưa thớt các giảng viên: tránh giảng viên dạy kín 1 ngày
        tload = sum(1 for cell, vs in self.occupied.items()
                    if cell[0] == d for x in vs if x.sec.teacher == v.sec.teacher)
        cost += tload
        return cost

    def candidate_slots(self, v):
        for d in range(len(DAYS)):
            for s in start_periods(v.sec.length):
                yield (d, s)

    # -- DSATUR: chọn đỉnh có nhiều "màu hàng xóm" khác nhau nhất, hòa thì bậc lớn nhất
    def saturation(self, vid):
        return len({self.color[u] for u in self.adj[vid] if u in self.color})

    def pick_vertex(self, remaining):
        return max(remaining, key=lambda i: (
            self.saturation(i), len(self.adj[i]), self.verts[i].sec.students))

    def place(self, v, slot):
        self.color[v.vid] = slot
        for cell in self.covered(v, slot):
            self.occupied[cell].append(v)

    def unplace(self, v):
        slot = self.color.pop(v.vid)
        for cell in self.covered(v, slot):
            self.occupied[cell].remove(v)

    def try_vertex(self, v):
        options = []
        for slot in self.candidate_slots(v):
            if not self.teacher_free(v, slot):
                continue
            if not self.neighbor_free(v, slot):
                continue
            options.append((self.soft_cost(v, slot), slot))
        options.sort()
        for _, slot in options:
            if self.rooms_ok(v, slot):
                self.place(v, slot)
                return True
        return False

    def run(self):
        remaining = {v.vid for v in self.verts}
        failed = []
        while remaining:
            vid = self.pick_vertex(remaining)
            remaining.remove(vid)
            if not self.try_vertex(self.verts[vid]):
                failed.append(vid)

        # Thử cứu các đỉnh thất bại bằng "đá" (kick) một đỉnh đã xếp rồi xếp lại
        failed = self.repair(failed)

        # Gán phòng cuối cùng cho từng tiết
        self.assign_rooms()
        return [self.verts[i] for i in failed]

    def repair(self, failed, rounds=200):
        import random
        rng = random.Random(1)
        for _ in range(rounds):
            if not failed:
                break
            vid = failed.pop(0)
            v = self.verts[vid]
            # chọn ngẫu nhiên một đỉnh đã xếp, có chung xung đột với v, gỡ ra
            cand = [u for u in self.adj[vid] if u in self.color]
            if not cand:
                failed.append(vid)
                continue
            u = self.verts[rng.choice(cand)]
            old = self.color[u.vid]
            self.unplace(u)
            if self.try_vertex(v):
                if not self.try_vertex(u):
                    failed.append(u.vid)
            else:
                self.place(u, old)
                failed.append(vid)
        return failed

    def assign_rooms(self):
        """Mỗi lớp học phần-buổi cần MỘT phòng cho cả buổi: chọn phòng nhỏ nhất
        phù hợp và rảnh trong mọi tiết của buổi."""
        used = defaultdict(set)  # (day, period) -> set(room.id)
        order = sorted(self.color, key=lambda i: -self.verts[i].sec.students)
        for vid in order:
            v, slot = self.verts[vid], self.color[vid]
            cells = self.covered(v, slot)
            rooms = sorted((r for r in self.p.rooms if can_use(r, v.sec)),
                           key=lambda r: r.capacity)
            chosen = next((r for r in rooms
                           if all(r.id not in used[c] for c in cells)), None)
            if chosen is None:
                # dự phòng: dùng ghép cặp theo từng tiết (phòng có thể khác nhau)
                chosen = Room("?", 0)
            for c in cells:
                used[c].add(chosen.id)
            self.room_of[vid] = chosen


# ---------------------------------------------------------------- Kiểm tra
def validate(sch):
    errors = []
    cells = defaultdict(list)
    for vid, slot in sch.color.items():
        v = sch.verts[vid]
        for c in sch.covered(v, slot):
            cells[c].append(v)
    for c, vs in cells.items():
        t, g, r = defaultdict(int), defaultdict(int), defaultdict(int)
        for v in vs:
            t[v.sec.teacher] += 1
            g[v.sec.group] += 1
            r[sch.room_of[v.vid].id] += 1
        for k, n in t.items():
            if n > 1:
                errors.append(f"GV {k} trùng lịch tại {DAYS[c[0]]} tiết {c[1]}")
        for k, n in g.items():
            if n > 1:
                errors.append(f"Nhóm {k} trùng lịch tại {DAYS[c[0]]} tiết {c[1]}")
        for k, n in r.items():
            if n > 1 and k != "?":
                errors.append(f"Phòng {k} trùng lịch tại {DAYS[c[0]]} tiết {c[1]}")
    for vid in sch.color:
        v, rm = sch.verts[vid], sch.room_of[vid]
        if rm.id == "?":
            errors.append(f"{v.sec.id} buổi {v.idx+1}: không gán được phòng")
        elif not can_use(rm, v.sec):
            errors.append(f"{v.sec.id}: phòng {rm.id} không phù hợp")
    return errors


# ------------------------------------------------------------------- Xuất
def export_csv(sch, path):
    rows = []
    for vid, (d, s) in sorted(sch.color.items(), key=lambda kv: (kv[1], kv[0])):
        v = sch.verts[vid]
        rows.append([DAYS[d], s, s + v.sec.length - 1, v.sec.id, v.sec.name,
                     v.sec.teacher, v.sec.group, sch.room_of[vid].id])
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Thứ", "Tiết bắt đầu", "Tiết kết thúc", "Mã LHP", "Môn học",
                    "Giảng viên", "Lớp", "Phòng"])
        w.writerows(rows)


def print_group_table(sch, group):
    grid = {}
    for vid, (d, s) in sch.color.items():
        v = sch.verts[vid]
        if v.sec.group == group:
            for i in range(v.sec.length):
                grid[(d, s + i)] = f"{v.sec.id}@{sch.room_of[vid].id}"
    print(f"\n=== Thời khóa biểu lớp {group} ===")
    print("Tiết | " + " | ".join(f"{d:^14}" for d in DAYS))
    for p in range(1, PERIODS_PER_DAY + 1):
        print(f"{p:>4} | " + " | ".join(f"{grid.get((d, p), ''):^14}" for d in range(len(DAYS))))


# ------------------------------------------------------------- Dữ liệu mẫu
def sample_problem():
    rooms = [Room("A101", 60), Room("A102", 60), Room("A201", 40), Room("A202", 40),
             Room("B101", 90), Room("LAB1", 40, "may_tinh"), Room("LAB2", 40, "may_tinh")]
    secs = [
        Section("MAT101", "Giải tích 1", "GV_An", "CNTT1", 55, 2, 3),
        Section("MAT102", "Đại số tuyến tính", "GV_Binh", "CNTT1", 55, 2, 3),
        Section("PHY101", "Vật lý đại cương", "GV_Cuong", "CNTT1", 55, 2, 3),
        Section("INT101", "Nhập môn lập trình", "GV_Dung", "CNTT1", 40, 2, 3, "may_tinh"),
        Section("MAT101B", "Giải tích 1", "GV_An", "CNTT2", 58, 2, 3),
        Section("ENG101", "Tiếng Anh 1", "GV_Em", "CNTT2", 58, 2, 3),
        Section("INT102", "Cấu trúc dữ liệu", "GV_Dung", "CNTT2", 38, 2, 3, "may_tinh"),
        Section("PHY101B", "Vật lý đại cương", "GV_Cuong", "CNTT2", 58, 2, 3),
        Section("INT201", "Cơ sở dữ liệu", "GV_Giang", "KHMT1", 38, 2, 3, "may_tinh"),
        Section("INT202", "Hệ điều hành", "GV_Hoa", "KHMT1", 38, 2, 3),
        Section("MAT201", "Xác suất thống kê", "GV_Binh", "KHMT1", 38, 2, 3),
        Section("ENG201", "Tiếng Anh 2", "GV_Em", "KHMT1", 38, 2, 3),
        Section("INT301", "Học máy", "GV_Giang", "KHMT2", 35, 2, 3, "may_tinh"),
        Section("INT302", "Mạng máy tính", "GV_Hoa", "KHMT2", 35, 2, 3),
        Section("ECO101", "Kinh tế vi mô", "GV_Khang", "KT1", 85, 2, 3),
        Section("ECO102", "Kinh tế vĩ mô", "GV_Khang", "KT1", 85, 2, 3),
        Section("MAT103", "Toán kinh tế", "GV_An", "KT1", 85, 2, 3),
    ]
    busy = {
        "GV_An": {(5, None)},              # bận cả Thứ 7
        "GV_Binh": {(0, 1), (0, 2), (0, 3), (0, 4), (0, 5)},  # bận sáng Thứ 2
        "GV_Khang": {(2, None)},           # bận cả Thứ 4
    }
    return Problem(rooms, secs, busy)


def load_problem(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    rooms = [Room(**r) for r in d["rooms"]]
    secs = [Section(**s) for s in d["sections"]]
    busy = {}
    for t, items in d.get("teacher_busy", {}).items():
        busy[t] = {(x[0], x[1]) for x in items}
    return Problem(rooms, secs, busy)


# ------------------------------------------------------- Nhập dữ liệu từ bàn phím
def ask(prompt, default=None, cast=str, check=None):
    """Hỏi đến khi nhập hợp lệ. Enter để lấy giá trị mặc định (nếu có)."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        if raw == "":
            print("  ! Không được để trống.")
            continue
        try:
            val = cast(raw)
        except ValueError:
            print("  ! Giá trị không hợp lệ, nhập lại.")
            continue
        if check and not check(val):
            print("  ! Giá trị ngoài phạm vi cho phép, nhập lại.")
            continue
        return val


def parse_busy(text):
    """'2:1-5, 5:all, 3:7' -> {(0,1)..(0,5), (3,None), (1,7)}  (thứ 2..7 -> ngày 0..5)"""
    res = set()
    for tok in text.split(","):
        tok = tok.strip()
        if not tok:
            continue
        d, _, p = tok.partition(":")
        day = int(d) - 2
        if not 0 <= day < len(DAYS):
            raise ValueError
        p = p.strip().lower()
        if p in ("all", ""):
            res.add((day, None))
        elif "-" in p:
            a, b = (int(x) for x in p.split("-"))
            if not 1 <= a <= b <= PERIODS_PER_DAY:
                raise ValueError
            res.update((day, x) for x in range(a, b + 1))
        else:
            x = int(p)
            if not 1 <= x <= PERIODS_PER_DAY:
                raise ValueError
            res.add((day, x))
    return res


def interactive_problem():
    print("=== NHẬP DỮ LIỆU XẾP THỜI KHÓA BIỂU ===")
    print("(Mỗi buổi học chỉ được bắt đầu trong buổi sáng tiết 1-5 hoặc chiều tiết 6-10)\n")

    print("--- 1. PHÒNG HỌC ---")
    print("Loại phòng gợi ý: ly_thuyet, may_tinh, thuc_hanh (tự đặt tên khác cũng được)")
    n_rooms = ask("Số phòng học", cast=int, check=lambda x: x > 0)
    rooms = []
    for i in range(1, n_rooms + 1):
        print(f"Phòng #{i}")
        rid = ask("  Mã phòng")
        while any(r.id == rid for r in rooms):
            print("  ! Mã phòng đã tồn tại.")
            rid = ask("  Mã phòng")
        cap = ask("  Sức chứa", cast=int, check=lambda x: x > 0)
        kind = ask("  Loại phòng", default="ly_thuyet")
        rooms.append(Room(rid, cap, kind))

    print("\n--- 2. LỚP HỌC PHẦN ---")
    n_secs = ask("Số lớp học phần", cast=int, check=lambda x: x > 0)
    secs = []
    for i in range(1, n_secs + 1):
        print(f"Lớp học phần #{i}")
        sid = ask("  Mã lớp học phần")
        while any(s.id == sid for s in secs):
            print("  ! Mã đã tồn tại.")
            sid = ask("  Mã lớp học phần")
        name = ask("  Tên môn học", default=sid)
        teacher = ask("  Giảng viên")
        group = ask("  Lớp / nhóm sinh viên")
        students = ask("  Sĩ số", cast=int, check=lambda x: x > 0)
        sessions = ask("  Số buổi/tuần", default=2, cast=int, check=lambda x: 1 <= x <= 6)
        length = ask("  Số tiết mỗi buổi (tối đa 5)", default=3, cast=int,
                     check=lambda x: 1 <= x <= 5)
        kind = ask("  Loại phòng cần", default="ly_thuyet")
        if not any(can_use(r, Section(sid, name, teacher, group, students,
                                      sessions, length, kind)) for r in rooms):
            print("  ! CẢNH BÁO: không có phòng nào đủ sức chứa/đúng loại cho lớp này.")
        secs.append(Section(sid, name, teacher, group, students, sessions, length, kind))

    print("\n--- 3. GIẢNG VIÊN BẬN ---")
    print("Định dạng: thứ:tiết, cách nhau dấu phẩy. Thứ từ 2 đến 7.")
    print("  Ví dụ: 2:1-5   (bận tiết 1-5 Thứ 2)    5:all   (bận cả Thứ 5)    3:7  (bận tiết 7 Thứ 3)")
    print("  Có thể ghép:  2:1-5, 7:all      Enter để bỏ qua (không bận).")
    busy = {}
    for t in sorted({s.teacher for s in secs}):
        while True:
            raw = input(f"  Lịch bận của {t}: ").strip()
            try:
                b = parse_busy(raw)
            except ValueError:
                print("  ! Sai định dạng, nhập lại (ví dụ 2:1-5, 7:all).")
                continue
            if b:
                busy[t] = b
            break

    problem = Problem(rooms, secs, busy)

    if input("\nLưu dữ liệu vừa nhập ra data.json để lần sau dùng lại? (y/N): ").strip().lower() == "y":
        data = {
            "rooms": [r.__dict__ for r in rooms],
            "sections": [s.__dict__ for s in secs],
            "teacher_busy": {t: sorted([list(x) for x in v], key=lambda z: (z[0], z[1] or 0))
                             for t, v in busy.items()},
        }
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Đã lưu data.json")
    return problem


def main():
    args = sys.argv[1:]
    out = "thoikhoabieu.csv"
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1]
        del args[i:i + 2]
    if "--demo" in args:
        problem = sample_problem()
    elif args:
        problem = load_problem(args[0])
    else:
        problem = interactive_problem()

    sch = Scheduler(problem)
    failed = sch.run()
    total = len(sch.verts)
    print(f"Đã xếp {total - len(failed)}/{total} buổi học")
    for v in failed:
        print(f"  CHƯA XẾP ĐƯỢC: {v.sec.id} buổi {v.idx + 1}")

    errs = validate(sch)
    print("Kiểm tra ràng buộc:", "OK, không xung đột" if not errs else f"{len(errs)} lỗi")
    for e in errs:
        print("  -", e)

    export_csv(sch, out)
    print(f"Đã xuất file: {out}")
    for g in sorted({s.group for s in problem.sections})[:2]:
        print_group_table(sch, g)


if __name__ == "__main__":
    main()
