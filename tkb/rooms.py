"""Ràng buộc phòng học: đủ sức chứa, đúng loại, và ghép cặp phòng (Kuhn)."""


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
