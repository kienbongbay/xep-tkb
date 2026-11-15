// ---------------------------------------------------------------- Thuật toán xếp lịch ngay trong trình duyệt
// (dùng khi không có máy chủ Flask, ví dụ mở bằng Go Live)
function startPeriods(len) {
  const res = [];
  for (const [a, b] of [[1, 5], [6, 10]]) for (let s = a; s <= b - len + 1; s++) res.push(s);
  return res;
}
function fits(room, sec) { return room.kind === sec.roomKind && room.capacity >= sec.students; }
function mulberry32(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
function schedule(p) {
  const verts = [];
  for (const s of p.sections) for (let k = 0; k < s.sessions; k++) verts.push({ vid: verts.length, sec: s, idx: k });
  const adj = verts.map(() => new Set());
  const link = key => {
    const m = new Map();
    for (const v of verts) { const k = key(v); if (!m.has(k)) m.set(k, []); m.get(k).push(v.vid); }
    for (const ids of m.values()) for (const i of ids) for (const j of ids) if (i !== j) adj[i].add(j);
  };
  link(v => "t|" + v.sec.teacher); link(v => "g|" + v.sec.group); link(v => "s|" + v.sec.id);

  const color = new Map(), roomOf = new Map(), roomUsed = new Map();
  const loadG = new Map(), loadT = new Map();
  const fitting = new Map();
  for (const s of p.sections) fitting.set(s.id, p.rooms.filter(r => fits(r, s)).sort((a, b) => a.capacity - b.capacity));
  const cellsOf = (v, slot) => { const r = []; for (let i = 0; i < v.sec.length; i++) r.push(slot[0] + "," + (slot[1] + i)); return r; };

  const teacherFree = (v, slot) => {
    const busy = p.busy[v.sec.teacher];
    if (!busy) return true;
    for (let i = 0; i < v.sec.length; i++) {
      if (busy.has(slot[0] + ",*") || busy.has(slot[0] + "," + (slot[1] + i))) return false;
    }
    return true;
  };
  const neighborFree = (v, slot) => {
    for (const u of adj[v.vid]) {
      const c = color.get(u);
      if (c && c[0] === slot[0] && slot[1] < c[1] + verts[u].sec.length && c[1] < slot[1] + v.sec.length) return false;
    }
    return true;
  };
  const pickRoom = (v, slot) => {
    const cells = cellsOf(v, slot);
    return fitting.get(v.sec.id).find(r => cells.every(c => !(roomUsed.get(c) && roomUsed.get(c).has(r.id)))) || null;
  };
  const softCost = (v, slot) => {
    const [d, s] = slot;
    let cost = 0;
    for (const u of adj[v.vid]) {
      if (color.has(u) && verts[u].sec.id === v.sec.id) {
        const ud = color.get(u)[0];
        if (ud === d) cost += 50; else if (Math.abs(ud - d) === 1) cost += 5;
      }
    }
    cost += (loadG.get(v.sec.group + "|" + d) || 0) * 2;
    cost += (loadT.get(v.sec.teacher + "|" + d) || 0);
    if (s === 1) cost += 3;
    if (s + v.sec.length - 1 >= 9) cost += 4;
    if (d === 5) cost += 15;
    return cost;
  };
  const bump = (m, k, n) => m.set(k, (m.get(k) || 0) + n);
  const place = (v, slot, room) => {
    color.set(v.vid, slot); roomOf.set(v.vid, room);
    for (const c of cellsOf(v, slot)) { if (!roomUsed.has(c)) roomUsed.set(c, new Set()); roomUsed.get(c).add(room.id); }
    bump(loadG, v.sec.group + "|" + slot[0], v.sec.length);
    bump(loadT, v.sec.teacher + "|" + slot[0], v.sec.length);
  };
  const unplace = v => {
    const slot = color.get(v.vid), room = roomOf.get(v.vid);
    for (const c of cellsOf(v, slot)) roomUsed.get(c).delete(room.id);
    bump(loadG, v.sec.group + "|" + slot[0], -v.sec.length);
    bump(loadT, v.sec.teacher + "|" + slot[0], -v.sec.length);
    color.delete(v.vid); roomOf.delete(v.vid);
  };
  const tryVertex = v => {
    let best = null;
    for (let d = 0; d < DAYS.length; d++) {
      for (const s of startPeriods(v.sec.length)) {
        const slot = [d, s];
        if (!teacherFree(v, slot) || !neighborFree(v, slot)) continue;
        const room = pickRoom(v, slot);
        if (!room) continue;
        const cost = softCost(v, slot);
        if (!best || cost < best.cost) best = { cost, slot, room };
      }
    }
    if (!best) return false;
    place(v, best.slot, best.room);
    return true;
  };
  const saturation = vid => { const set = new Set(); for (const u of adj[vid]) if (color.has(u)) set.add(color.get(u).join()); return set.size; };

  const remaining = new Set(verts.map(v => v.vid));
  let failed = [];
  while (remaining.size) {
    let bestId = -1, bestKey = null;
    for (const id of remaining) {
      const key = [saturation(id), adj[id].size, verts[id].sec.students];
      if (!bestKey || key[0] > bestKey[0] || (key[0] === bestKey[0] && (key[1] > bestKey[1] || (key[1] === bestKey[1] && key[2] > bestKey[2])))) { bestKey = key; bestId = id; }
    }
    remaining.delete(bestId);
    if (!tryVertex(verts[bestId])) failed.push(bestId);
  }

  // Cứu các buổi thất bại: gỡ tạm một buổi xung đột, xếp buổi thất bại, rồi xếp lại buổi vừa gỡ
  const rng = mulberry32(1);
  for (let round = 0; round < 300 && failed.length; round++) {
    const vid = failed.shift();
    const cand = [...adj[vid]].filter(u => color.has(u));
    if (!cand.length) { failed.push(vid); continue; }
    const u = verts[cand[Math.floor(rng() * cand.length)]];
    const oldSlot = color.get(u.vid), oldRoom = roomOf.get(u.vid);
    unplace(u);
    if (tryVertex(verts[vid])) { if (!tryVertex(u)) failed.push(u.vid); }
    else { place(u, oldSlot, oldRoom); failed.push(vid); }
  }

  const sessions = [];
  for (const [vid, slot] of color) {
    const v = verts[vid];
    sessions.push({ day: slot[0], start: slot[1], end: slot[1] + v.sec.length - 1, sec: v.sec, room: roomOf.get(vid), idx: v.idx });
  }
  sessions.sort((a, b) => a.day - b.day || a.start - b.start || a.sec.id.localeCompare(b.sec.id));
  const unplaced = failed.map(id => {
    const v = verts[id];
    let why = "không còn khung giờ trống phù hợp";
    if (!fitting.get(v.sec.id).length) why = "không có phòng đủ sức chứa và đúng loại";
    return { sec: v.sec, idx: v.idx, why };
  });
  return { sessions, unplaced, errors: validateLocal(p, sessions), total: verts.length };
}
function validateLocal(p, sessions) {
  const errors = [], cells = new Map();
  for (const s of sessions) {
    for (let t = s.start; t <= s.end; t++) {
      const k = s.day + "," + t;
      if (!cells.has(k)) cells.set(k, []);
      cells.get(k).push(s);
    }
    const busy = p.busy[s.sec.teacher];
    if (busy) for (let t = s.start; t <= s.end; t++) if (busy.has(s.day + ",*") || busy.has(s.day + "," + t)) errors.push(s.sec.teacher + " bị xếp vào giờ bận (" + DAYS[s.day] + ", tiết " + t + ")");
    if (!fits(s.room, s.sec)) errors.push(s.sec.id + ": phòng " + s.room.id + " không phù hợp");
  }
  for (const [k, list] of cells) {
    const [d, t] = k.split(",").map(Number);
    for (const [name, f] of [["Giảng viên", x => x.sec.teacher], ["Lớp", x => x.sec.group], ["Phòng", x => x.room.id]]) {
      const seen = new Set();
      for (const x of list) { const key = f(x); if (seen.has(key)) errors.push(name + " " + key + " trùng lịch (" + DAYS[d] + ", tiết " + t + ")"); seen.add(key); }
    }
  }
  return [...new Set(errors)];
}
