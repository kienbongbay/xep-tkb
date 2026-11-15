// --------------------------------------------------------------------- Tab
function showTab(name) {
  for (const t of document.querySelectorAll(".tab")) t.setAttribute("aria-selected", String(t.dataset.tab === name));
  $("#tab-du-lieu").hidden = name !== "du-lieu";
  $("#tab-ket-qua").hidden = name !== "ket-qua";
  if (location.hash !== "#" + name) { try { history.replaceState(null, "", "#" + name); } catch (e) { location.hash = name; } }
}
for (const t of document.querySelectorAll(".tab")) t.addEventListener("click", () => showTab(t.dataset.tab));
window.addEventListener("hashchange", () => { const h = location.hash.slice(1); if (h === "du-lieu" || h === "ket-qua") showTab(h); });
