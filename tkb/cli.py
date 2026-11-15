"""Giao diện dòng lệnh: nhập dữ liệu từ bàn phím hoặc đọc file, rồi xếp lịch.

Chạy:
    python main.py              nhập dữ liệu từng bước
    python main.py data.json    đọc dữ liệu từ file JSON
    python main.py --demo       dùng dữ liệu mẫu
    thêm  --out ketqua.csv      để đổi tên file xuất
"""
import sys

from .busy import parse_busy
from .export import export_csv, print_group_table
from .models import Problem, Room, Section
from .rooms import can_use
from .samples import sample_problem
from .scheduler import Scheduler
from .storage import load_problem, save_problem
from .validate import validate


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
        save_problem(problem)
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
