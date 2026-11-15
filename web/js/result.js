// ----------------------------------------------------------------- Kết quả
function hueOf(id) { let h = 0; for (const c of id) h = (h * 31 + c.charCodeAt(0)) % 360; return h; }
function renderResult() {
  const stats = $("#stats"), issues = $("#issues");
  if (!result) {
    stats.innerHTML = ""; issues.innerHTML = "";
    $("#grid-wrap").innerHTML = `<p class="empty-note">Chưa có thời khóa biểu. Nhập dữ liệu ở tab Dữ liệu rồi bấm “Xếp thời khóa biểu”.</p>`;
    $("#view-item").innerHTML = ""; $("#csv-box").value = "";
    return;
  }
  const placed = result.total - result.unplaced.length;
  const bad = result.unplaced.length || result.errors.length;
  stats.innerHTML = `
    <div class="stat ${result.unplaced.length ? "bad" : "good"}"><b>${placed}/${result.total}</b><span>buổi học đã xếp</span></div>
    <div class="stat ${result.errors.length ? "bad" : "good"}"><b>${result.errors.length}</b><span>xung đột</span></div>
    <div class="stat"><b>${result.ms} ms</b><span>thời gian tính</span></div>`;
  issues.innerHTML = result.unplaced.map(u => `<li class="err">Chưa xếp được ${esc(u.sec.id)} (buổi ${u.idx + 1}): ${esc(u.why)}.</li>`).join("")
    + result.errors.slice(0, 20).map(x => `<li class="err">${esc(x)}</li>`).join("");
  fillItems();
  renderGrid();
  $("#csv-box").value = toCSV();
}
function itemKey(s, kind) { return kind === "group" ? s.sec.group : kind === "teacher" ? s.sec.teacher : s.room.id; }
function fillItems() {
  const kind = $("#view-kind").value, sel = $("#view-item"), prev = sel.value;
  const items = [...new Set(result.sessions.map(s => itemKey(s, kind)))].sort((a, b) => a.localeCompare(b, "vi", { numeric: true }));
  sel.innerHTML = items.map(x => `<option value="${esc(x)}">${esc(x)}</option>`).join("");
  if (items.includes(prev)) sel.value = prev;
}
function renderGrid() {
  const wrap = $("#grid-wrap");
  if (!result || !result.sessions.length) { wrap.innerHTML = `<p class="empty-note">Không có buổi học nào để hiển thị.</p>`; return; }
  const kind = $("#view-kind").value, item = $("#view-item").value;
  const list = result.sessions.filter(s => itemKey(s, kind) === item);
  const g = DAYS.map(() => ({}));
  for (const s of list) { g[s.day][s.start] = s; for (let t = s.start + 1; t <= s.end; t++) g[s.day][t] = "skip"; }
  let html = `<table class="grid" aria-label="Thời khóa biểu ${esc(item)}"><thead><tr><th class="p"></th>${DAYS.map(d => `<th>${d}</th>`).join("")}</tr></thead><tbody>`;
  for (let p = 1; p <= PERIODS; p++) {
    html += `<tr class="${p === 6 ? "noon" : ""}"><th class="p">${p === 1 ? '<span class="session-label">Sáng</span>' : p === 6 ? '<span class="session-label">Chiều</span>' : ""}Tiết ${p}</th>`;
    for (let d = 0; d < DAYS.length; d++) {
      const c = g[d][p];
      if (c === "skip") continue;
      if (!c) { html += "<td></td>"; continue; }
      const second = kind === "teacher" ? c.sec.group : c.sec.teacher;
      const third = kind === "room" ? c.sec.group : "Phòng " + c.room.id;
      html += `<td class="blk" rowspan="${c.end - c.start + 1}" style="--h:${hueOf(c.sec.id)}"><b>${esc(c.sec.id)}</b><small>${esc(c.sec.name)}</small><small>${esc(second)} · ${esc(third)}</small></td>`;
    }
    html += "</tr>";
  }
  wrap.innerHTML = html + "</tbody></table>";
}
$("#view-kind").addEventListener("change", () => { if (result) { fillItems(); renderGrid(); } });
$("#view-item").addEventListener("change", renderGrid);

function toCSV() {
  const q = v => { v = String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
  const rows = [["Thứ", "Tiết bắt đầu", "Tiết kết thúc", "Mã LHP", "Môn học", "Giảng viên", "Lớp", "Phòng"]];
  for (const s of result.sessions) rows.push([DAYS[s.day], s.start, s.end, s.sec.id, s.sec.name, s.sec.teacher, s.sec.group, s.room.id]);
  return rows.map(r => r.map(q).join(",")).join("\n");
}

function copyFrom(box, statusEl) {
  const done = ok => { statusEl.textContent = ok ? "Đã sao chép" : "Hãy bôi đen và nhấn Ctrl+C"; setTimeout(() => statusEl.textContent = "", 2500); };
  const fallback = () => { box.focus(); box.select(); let ok = false; try { ok = document.execCommand("copy"); } catch (e) { /* bỏ qua */ } done(ok); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(box.value).then(() => done(true), fallback);
  else fallback();
}
$("#btn-csv-copy").addEventListener("click", () => copyFrom($("#csv-box"), $("#csv-status")));
