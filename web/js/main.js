// ------------------------------------------------------------------ Khởi động
(function init() {
  const saved = loadSaved();
  if (saved) state = { rooms: saved.rooms, sections: saved.sections, busy: saved.busy || {}, sample: !!saved.sample };
  else useSample();
  renderAll();
  if (state.rooms.length && state.sections.length) run(true); else renderResult();
  const h = location.hash.slice(1);
  showTab(h === "ket-qua" ? "ket-qua" : "du-lieu");
})();
