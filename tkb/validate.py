"""Kiểm tra thời khóa biểu đã xếp có vi phạm ràng buộc cứng nào không."""
from collections import defaultdict

from .constants import DAYS
from .rooms import can_use


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
