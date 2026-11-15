// Dữ liệu mẫu hiển thị lần đầu mở trang
const SAMPLE = {
  rooms: [
    { id: "A101", capacity: 60, kind: "ly_thuyet" }, { id: "A102", capacity: 60, kind: "ly_thuyet" },
    { id: "A201", capacity: 40, kind: "ly_thuyet" }, { id: "A202", capacity: 40, kind: "ly_thuyet" },
    { id: "B101", capacity: 90, kind: "ly_thuyet" }, { id: "LAB1", capacity: 40, kind: "may_tinh" },
    { id: "LAB2", capacity: 40, kind: "may_tinh" }
  ],
  sections: [
    ["MAT101", "Giải tích 1", "GV_An", "CNTT1", 55, 2, 3, "ly_thuyet"],
    ["MAT102", "Đại số tuyến tính", "GV_Binh", "CNTT1", 55, 2, 3, "ly_thuyet"],
    ["PHY101", "Vật lý đại cương", "GV_Cuong", "CNTT1", 55, 2, 3, "ly_thuyet"],
    ["INT101", "Nhập môn lập trình", "GV_Dung", "CNTT1", 40, 2, 3, "may_tinh"],
    ["MAT101B", "Giải tích 1", "GV_An", "CNTT2", 58, 2, 3, "ly_thuyet"],
    ["ENG101", "Tiếng Anh 1", "GV_Em", "CNTT2", 58, 2, 3, "ly_thuyet"],
    ["INT102", "Cấu trúc dữ liệu", "GV_Dung", "CNTT2", 38, 2, 3, "may_tinh"],
    ["PHY101B", "Vật lý đại cương", "GV_Cuong", "CNTT2", 58, 2, 3, "ly_thuyet"],
    ["INT201", "Cơ sở dữ liệu", "GV_Giang", "KHMT1", 38, 2, 3, "may_tinh"],
    ["INT202", "Hệ điều hành", "GV_Hoa", "KHMT1", 38, 2, 3, "ly_thuyet"],
    ["MAT201", "Xác suất thống kê", "GV_Binh", "KHMT1", 38, 2, 3, "ly_thuyet"],
    ["ENG201", "Tiếng Anh 2", "GV_Em", "KHMT1", 38, 2, 3, "ly_thuyet"],
    ["INT301", "Học máy", "GV_Giang", "KHMT2", 35, 2, 3, "may_tinh"],
    ["INT302", "Mạng máy tính", "GV_Hoa", "KHMT2", 35, 2, 3, "ly_thuyet"],
    ["ECO101", "Kinh tế vi mô", "GV_Khang", "KT1", 85, 2, 3, "ly_thuyet"],
    ["ECO102", "Kinh tế vĩ mô", "GV_Khang", "KT1", 85, 2, 3, "ly_thuyet"],
    ["MAT103", "Toán kinh tế", "GV_An", "KT1", 85, 2, 3, "ly_thuyet"]
  ].map(a => ({ id: a[0], name: a[1], teacher: a[2], group: a[3], students: a[4], sessions: a[5], length: a[6], roomKind: a[7] })),
  busy: { GV_An: "7:all", GV_Binh: "2:1-5", GV_Khang: "4:all" }
};
