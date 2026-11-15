// "2:1-5, 7:all" -> Set của "ngày,tiết" hoặc "ngày,*" (ngày 0..5 ứng với Thứ 2..7)
function parseBusy(text) {
  const res = new Set();
  for (let tok of String(text || "").split(",")) {
    tok = tok.trim();
    if (!tok) continue;
    const i = tok.indexOf(":");
    const dStr = (i < 0 ? tok : tok.slice(0, i)).trim();
    const pStr = (i < 0 ? "" : tok.slice(i + 1)).trim().toLowerCase();
    const day = parseInt(dStr, 10) - 2;
    if (!/^\d+$/.test(dStr) || day < 0 || day > 5) throw new Error("Thứ phải từ 2 đến 7 (gặp “" + tok + "”)");
    if (pStr === "" || pStr === "all") res.add(day + ",*");
    else if (pStr.includes("-")) {
      const [a, b] = pStr.split("-").map(x => parseInt(x, 10));
      if (!(a >= 1 && a <= b && b <= PERIODS)) throw new Error("Tiết phải từ 1 đến 10 (gặp “" + tok + "”)");
      for (let x = a; x <= b; x++) res.add(day + "," + x);
    } else {
      const x = parseInt(pStr, 10);
      if (!(x >= 1 && x <= PERIODS)) throw new Error("Tiết phải từ 1 đến 10 (gặp “" + tok + "”)");
      res.add(day + "," + x);
    }
  }
  return res;
}
