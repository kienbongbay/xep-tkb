// Kiểm tra dữ liệu nhập, gọi máy chủ (hoặc tự tính) để xếp lịch
function setStatus(msg, kind) {
  const el = $("#status"); el.textContent = msg; el.className = "status" + (kind ? " " + kind : "");
}

function collect() {
  const errs = [], busy = {};
  const rooms = state.rooms.map(r => ({ id: String(r.id).trim(), capacity: Number(r.capacity), kind: String(r.kind).trim() }));
  const sections = state.sections.map(s => ({
    id: String(s.id).trim(), name: String(s.name).trim() || String(s.id).trim(), teacher: String(s.teacher).trim(),
    group: String(s.group).trim(), students: Number(s.students), sessions: Number(s.sessions), length: Number(s.length), roomKind: String(s.roomKind).trim()
  }));
  if (!rooms.length) errs.push("Chưa có phòng học nào.");
  if (!sections.length) errs.push("Chưa có lớp học phần nào.");
  const ids = new Set();
  rooms.forEach((r, i) => {
    if (!r.id) errs.push("Phòng thứ " + (i + 1) + " chưa có mã.");
    else if (ids.has("r" + r.id)) errs.push("Mã phòng " + r.id + " bị trùng.");
    ids.add("r" + r.id);
    if (!(r.capacity > 0)) errs.push("Phòng " + (r.id || i + 1) + ": sức chứa phải lớn hơn 0.");
    if (!r.kind) errs.push("Phòng " + (r.id || i + 1) + ": chưa có loại phòng.");
  });
  sections.forEach((s, i) => {
    const n = s.id || "thứ " + (i + 1);
    if (!s.id) errs.push("Lớp học phần thứ " + (i + 1) + " chưa có mã.");
    else if (ids.has("s" + s.id)) errs.push("Mã lớp học phần " + s.id + " bị trùng.");
    ids.add("s" + s.id);
    if (!s.teacher) errs.push(n + ": chưa có giảng viên.");
    if (!s.group) errs.push(n + ": chưa có lớp sinh viên.");
    if (!(s.students > 0)) errs.push(n + ": sĩ số phải lớn hơn 0.");
    if (!(Number.isInteger(s.sessions) && s.sessions >= 1 && s.sessions <= 6)) errs.push(n + ": số buổi mỗi tuần từ 1 đến 6.");
    if (!(Number.isInteger(s.length) && s.length >= 1 && s.length <= 5)) errs.push(n + ": số tiết mỗi buổi từ 1 đến 5.");
    if (!s.roomKind) errs.push(n + ": chưa có loại phòng cần.");
  });
  for (const t of teachers()) {
    try { busy[t] = parseBusy(state.busy[t]); } catch (e) { errs.push("Lịch bận của " + t + ": " + e.message); }
  }
  return { errs, problem: { rooms, sections, busy } };
}

async function run(silent) {
  const { errs, problem } = collect();
  if (errs.length) {
    setStatus(errs.slice(0, 4).join(" ") + (errs.length > 4 ? " (và " + (errs.length - 4) + " lỗi khác)" : ""), "bad");
    return false;
  }
  const btn = $("#btn-run");
  btn.disabled = true;
  setStatus("Đang xếp lịch...");
  try {
    const busy = {};
    for (const t of teachers()) busy[t] = state.busy[t] || "";
    const res = await fetch("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rooms: problem.rooms, sections: problem.sections, busy })
    });
    const data = await res.json();
    if (!res.ok) { setStatus(data.error || "Máy chủ báo lỗi.", "bad"); return false; }
    result = data;
  } catch (e) {
    // Không có máy chủ Flask (ví dụ mở bằng Go Live): tự tính ngay trong trình duyệt
    const t0 = performance.now();
    result = schedule(problem);
    result.ms = Math.round(performance.now() - t0);
  } finally {
    btn.disabled = false;
  }
  renderResult();
  const left = result.unplaced.length;
  setStatus(left || result.errors.length ? "Đã xếp xong nhưng còn vấn đề, xem tab Thời khóa biểu." : "Đã xếp xong " + result.total + " buổi học, không có xung đột.", left || result.errors.length ? "bad" : "ok");
  if (!silent) showTab("ket-qua");
  return true;
}
$("#btn-run").addEventListener("click", () => run(false));
