"""Bộ xếp lịch: DSATUR chọn đỉnh, tham lam chọn khung giờ và phòng."""
from collections import defaultdict

from .constants import DAYS, start_periods
from .graph import build_graph
from .models import Room
from .rooms import can_use, match_rooms


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
