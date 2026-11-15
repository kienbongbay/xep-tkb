$("#btn-json-copy").addEventListener("click", () => copyFrom($("#json-box"), $("#json-status")));

// ------------------------------------------------------- JSON vào / ra (cùng định dạng data.json của bản Python)
$("#btn-json-out").addEventListener("click", () => {
  const busy = {};
  for (const t of teachers()) {
    let set; try { set = parseBusy(state.busy[t]); } catch (e) { continue; }
    if (!set.size) continue;
    busy[t] = [...set].map(k => { const [d, p] = k.split(","); return [Number(d), p === "*" ? null : Number(p)]; }).sort((a, b) => a[0] - b[0] || (a[1] || 0) - (b[1] || 0));
  }
  const data = {
    rooms: state.rooms,
    sections: state.sections.map(s => ({ id: s.id, name: s.name, teacher: s.teacher, group: s.group, students: s.students, sessions: s.sessions, length: s.length, room_kind: s.roomKind })),
    teacher_busy: busy
  };
  $("#json-box").value = JSON.stringify(data, null, 2);
  $("#json-status").textContent = "";
});
$("#btn-json-in").addEventListener("click", () => {
  const st = $("#json-status");
  try {
    const d = JSON.parse($("#json-box").value);
    const rooms = (d.rooms || []).map(r => ({ id: String(r.id), capacity: Number(r.capacity), kind: r.kind || "ly_thuyet" }));
    const sections = (d.sections || []).map(s => ({
      id: String(s.id), name: s.name || String(s.id), teacher: s.teacher, group: s.group, students: Number(s.students),
      sessions: Number(s.sessions || 2), length: Number(s.length || 3), roomKind: s.room_kind || s.roomKind || "ly_thuyet"
    }));
    const busy = {};
    for (const [t, v] of Object.entries(d.teacher_busy || {})) {
      if (typeof v === "string") busy[t] = v;
      else busy[t] = v.map(x => (x[0] + 2) + ":" + (x[1] == null ? "all" : x[1])).join(", ");
    }
    if (!rooms.length && !sections.length) throw new Error("Không thấy rooms hoặc sections");
    state = { rooms, sections, busy, sample: false };
    renderAll(); save(); st.textContent = "Đã nạp " + rooms.length + " phòng, " + sections.length + " lớp học phần";
  } catch (e) { st.textContent = "JSON không hợp lệ: " + e.message; }
});
