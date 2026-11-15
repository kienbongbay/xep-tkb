"""Đọc chuỗi lịch bận của giảng viên, ví dụ "2:1-5, 7:all"."""
from .constants import DAYS, PERIODS_PER_DAY


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
