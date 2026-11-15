// Bảng nhập phòng, lớp học phần, lịch bận giảng viên
function renderRooms() {
  $("#rooms-body").innerHTML = state.rooms.map((r, i) => `<tr>
    <td><input type="text" id="room-${i}-id" data-l="rooms" data-i="${i}" data-f="id" value="${esc(r.id)}" aria-label="Mã phòng"></td>
    <td class="w-num"><input type="number" min="1" id="room-${i}-cap" data-l="rooms" data-i="${i}" data-f="capacity" value="${esc(r.capacity)}" aria-label="Sức chứa"></td>
    <td><input type="text" list="kinds" id="room-${i}-kind" data-l="rooms" data-i="${i}" data-f="kind" value="${esc(r.kind)}" aria-label="Loại phòng"></td>
    <td><button type="button" class="btn ghost" data-del="rooms" data-i="${i}" aria-label="Xóa phòng ${esc(r.id)}">Xóa</button></td></tr>`).join("");
}
function renderSections() {
  $("#secs-body").innerHTML = state.sections.map((s, i) => `<tr>
    <td><input type="text" id="sec-${i}-id" data-l="sections" data-i="${i}" data-f="id" value="${esc(s.id)}" aria-label="Mã lớp học phần"></td>
    <td class="w-name"><input type="text" id="sec-${i}-name" data-l="sections" data-i="${i}" data-f="name" value="${esc(s.name)}" aria-label="Môn học"></td>
    <td><input type="text" id="sec-${i}-teacher" data-l="sections" data-i="${i}" data-f="teacher" value="${esc(s.teacher)}" aria-label="Giảng viên"></td>
    <td><input type="text" id="sec-${i}-group" data-l="sections" data-i="${i}" data-f="group" value="${esc(s.group)}" aria-label="Lớp sinh viên"></td>
    <td class="w-num"><input type="number" min="1" id="sec-${i}-students" data-l="sections" data-i="${i}" data-f="students" value="${esc(s.students)}" aria-label="Sĩ số"></td>
    <td class="w-num"><input type="number" min="1" max="6" id="sec-${i}-sessions" data-l="sections" data-i="${i}" data-f="sessions" value="${esc(s.sessions)}" aria-label="Số buổi mỗi tuần"></td>
    <td class="w-num"><input type="number" min="1" max="5" id="sec-${i}-length" data-l="sections" data-i="${i}" data-f="length" value="${esc(s.length)}" aria-label="Số tiết mỗi buổi"></td>
    <td><input type="text" list="kinds" id="sec-${i}-kind" data-l="sections" data-i="${i}" data-f="roomKind" value="${esc(s.roomKind)}" aria-label="Loại phòng cần"></td>
    <td><span class="warn" data-warn="${i}"></span></td>
    <td><button type="button" class="btn ghost" data-del="sections" data-i="${i}" aria-label="Xóa lớp học phần ${esc(s.id)}">Xóa</button></td></tr>`).join("");
  updateWarns();
}
function updateWarns() {
  state.sections.forEach((s, i) => {
    const el = document.querySelector(`[data-warn="${i}"]`);
    if (!el) return;
    const ok = state.rooms.some(r => r.kind === s.roomKind && Number(r.capacity) >= Number(s.students));
    el.textContent = ok ? "" : "Không có phòng phù hợp";
  });
}
function teachers() { return [...new Set(state.sections.map(s => String(s.teacher).trim()).filter(Boolean))].sort(); }
function renderBusy() {
  const ts = teachers();
  $("#busy-grid").innerHTML = ts.length ? ts.map((t, i) => `<div>
    <label for="busy-${i}">${esc(t)}</label>
    <input type="text" id="busy-${i}" data-busy="${esc(t)}" value="${esc(state.busy[t] || "")}" placeholder="Ví dụ 2:1-5, 7:all">
    <div class="err" id="busy-err-${i}"></div></div>`).join("") : `<p class="hint">Thêm lớp học phần có giảng viên để nhập lịch bận.</p>`;
  ts.forEach((t, i) => checkBusy(i, state.busy[t]));
}
function checkBusy(i, text) {
  const el = $("#busy-err-" + i);
  if (!el) return true;
  try { parseBusy(text); el.textContent = ""; return true; } catch (e) { el.textContent = e.message; return false; }
}
function renderAll() {
  renderRooms(); renderSections(); renderBusy();
  $("#sample-banner").hidden = !state.sample;
}

document.addEventListener("input", e => {
  const t = e.target;
  if (t.dataset && t.dataset.l) {
    const f = t.dataset.f;
    state[t.dataset.l][+t.dataset.i][f] = NUM.has(f) ? (t.value === "" ? "" : Number(t.value)) : t.value;
    state.sample = false; $("#sample-banner").hidden = true;
    updateWarns(); save();
  } else if (t.dataset && t.dataset.busy) {
    state.busy[t.dataset.busy] = t.value;
    checkBusy(t.id.replace("busy-", ""), t.value); save();
  }
});
document.addEventListener("change", e => {
  const t = e.target;
  if (t.dataset && t.dataset.f === "teacher") renderBusy();
});
document.addEventListener("click", e => {
  const del = e.target.closest("[data-del]");
  if (!del) return;
  state[del.dataset.del].splice(+del.dataset.i, 1);
  state.sample = false;
  renderAll(); save();
});
$("#add-room").addEventListener("click", () => {
  state.rooms.push({ id: "P" + (state.rooms.length + 1), capacity: 50, kind: "ly_thuyet" });
  state.sample = false; renderAll(); save();
  const el = $("#room-" + (state.rooms.length - 1) + "-id"); if (el) { el.focus(); el.select(); }
});
$("#add-sec").addEventListener("click", () => {
  state.sections.push({ id: "", name: "", teacher: "", group: "", students: 40, sessions: 2, length: 3, roomKind: "ly_thuyet" });
  state.sample = false; renderAll(); save();
  const el = $("#sec-" + (state.sections.length - 1) + "-id"); if (el) el.focus();
});
$("#btn-clear").addEventListener("click", () => {
  state = { rooms: [], sections: [], busy: {}, sample: false };
  result = null; renderAll(); renderResult(); save(); setStatus("");
});
