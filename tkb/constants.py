"""Hằng số chung: các thứ trong tuần, số tiết mỗi ngày, khung giờ bắt đầu hợp lệ."""

DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
PERIODS_PER_DAY = 10  # tiết 1..10


# Khung giờ bắt đầu hợp lệ cho mỗi buổi: các "khối" để tránh buổi học vắt qua trưa.
def start_periods(length):
    blocks = [(1, 5), (6, 10)]  # sáng: tiết 1-5, chiều: tiết 6-10
    res = []
    for a, b in blocks:
        res.extend(range(a, b - length + 2))
    return res
