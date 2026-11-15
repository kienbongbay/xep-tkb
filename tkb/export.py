"""Xuất kết quả: file CSV và bảng thời khóa biểu in ra màn hình."""
import csv

from .constants import DAYS, PERIODS_PER_DAY


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
