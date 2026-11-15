"""Dữ liệu mẫu để chạy thử."""
from .models import Problem, Room, Section


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
