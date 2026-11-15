// Trạng thái của trang và lưu vào trình duyệt
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const NUM = new Set(["capacity", "students", "sessions", "length"]);
const STORE_KEY = "xep-tkb-v1";
let state = { rooms: [], sections: [], busy: {}, sample: false };
let result = null;

function save() {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* bỏ qua */ }
}
function loadSaved() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) { const d = JSON.parse(raw); if (d && Array.isArray(d.rooms) && Array.isArray(d.sections)) return d; }
  } catch (e) { /* bỏ qua */ }
  return null;
}
function useSample() {
  state = JSON.parse(JSON.stringify(SAMPLE)); state.sample = true;
}
