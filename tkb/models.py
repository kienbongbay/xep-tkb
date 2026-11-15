"""Các cấu trúc dữ liệu đầu vào: phòng học, lớp học phần, bài toán."""
from dataclasses import dataclass, field


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
