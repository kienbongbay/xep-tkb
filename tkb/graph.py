"""Đồ thị xung đột: mỗi buổi học là một đỉnh, hai buổi xung đột thì có cạnh."""
from collections import defaultdict
from dataclasses import dataclass

from .models import Section


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
