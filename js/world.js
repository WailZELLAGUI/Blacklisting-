/* The whole world as one network: every fraud's blacklisted address is a hub, every receiving account a dot.
   An account paid by two frauds or more is pulled between their hubs and ringed, so it ties the frauds together.
   Canvas, with a small force layout written for this page (no library). build() settles a layout once (the
   report's preview); live() runs it on a canvas you can drag, zoom and pan, and keeps the physics running
   until it settles. The layout is seeded, so it repeats. */
const WORLD = (() => {
  const css = (n, fb) => NET.css(n, fb);
  const cache = new Map();

  function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

  // one step of the physics: pairwise repulsion with a cutoff (hubs push each other far apart), springs on
  // links, a light pull to the centre; a node being dragged is pinned
  function step(m, alpha, rand) {
    const nodes = m.nodes, N = nodes.length;
    for (let i = 0; i < N; i++) {
      const p = nodes[i];
      for (let j = i + 1; j < N; j++) {
        const q = nodes[j]; let dx = p.x - q.x, dy = p.y - q.y; let d2 = dx * dx + dy * dy;
        const hubs2 = p.kind === 'hub' && q.kind === 'hub';
        if (!hubs2 && d2 > 2500) continue; if (d2 < 0.01) { dx = rand() - 0.5; dy = rand() - 0.5; d2 = 0.25; }
        const f = (hubs2 ? 700 : 70) / d2 * alpha;
        p.vx += dx * f; p.vy += dy * f; q.vx -= dx * f; q.vy -= dy * f;
      }
    }
    for (const [h, a] of m.links) {
      const dx = a.x - h.x, dy = a.y - h.y, d = Math.sqrt(dx * dx + dy * dy) || 1;
      const rest = 20 + 4.5 * Math.sqrt(h.deg), f = (d - rest) * 0.08 * alpha;
      a.vx -= dx / d * f; a.vy -= dy / d * f; h.vx += dx / d * f * 0.25; h.vy += dy / d * f * 0.25;
    }
    for (const p of nodes) {
      if (p.pinned) { p.vx = 0; p.vy = 0; continue; }
      p.vx -= p.x * 0.006 * alpha; p.vy -= p.y * 0.006 * alpha; p.x += p.vx; p.y += p.vy; p.vx *= 0.55; p.vy *= 0.55;
    }
  }

  function bounds(m) {
    const q = (arr, f) => { const v = arr.slice().sort((a, b) => a - b); return v[Math.min(v.length - 1, Math.max(0, Math.round(f * (v.length - 1))))]; };
    const xs = m.nodes.map(p => p.x), ys = m.nodes.map(p => p.y);
    return { minX: q(xs, 0.02), maxX: q(xs, 0.98), minY: q(ys, 0.02), maxY: q(ys, 0.98) };
  }

  // graphs: { fraudId: {nodes, links} } for every fraud of the world
  function build(key, graphs, seed) {
    if (cache.has(key)) return cache.get(key);
    const rand = rng(seed || 7);
    const hubs = [], accs = new Map(), links = [];
    const ids = Object.keys(graphs).map(Number).sort((a, b) => a - b);
    const golden = Math.PI * (3 - Math.sqrt(5));
    ids.forEach((fid, i) => {
      const r = 260 * Math.sqrt((i + 0.5) / ids.length), a = i * golden;
      const hub = { kind: 'hub', fid, x: r * Math.cos(a), y: r * Math.sin(a), vx: 0, vy: 0, deg: 0 };
      hubs.push(hub);
      for (const n of graphs[fid].nodes) {
        if (n.kind !== 'account') continue;
        let acc = accs.get(n.id);
        if (!acc) { acc = { kind: 'acc', id: n.id, aid: n.aid, exchange: n.exchange, X: 0, by: [], x: hub.x + (rand() - 0.5) * 60, y: hub.y + (rand() - 0.5) * 60, vx: 0, vy: 0 }; accs.set(n.id, acc); }
        acc.by.push({ fid, node: n }); acc.X += n.X;
        links.push([hub, acc]); hub.deg++;
      }
    });
    const nodes = hubs.concat([...accs.values()]);
    const m = { hubs, accs: [...accs.values()], links, nodes, rand, maxAcc: Math.max(1, ...[...accs.values()].map(a => a.X)),
      shared: [...accs.values()].filter(a => a.by.length > 1) };
    for (let it = 0, alpha = 1; it < 320; it++, alpha *= 0.988) step(m, alpha, rand);
    m.box = bounds(m);
    cache.set(key, m);
    return m;
  }

  function level(acc, preset) {
    let lv = 0;
    for (const b of acc.by) lv = Math.max(lv, preset === '10k' ? (b.node.ten_k ? 3 : 0) : b.node.grade);
    return lv;
  }

  // the fit of the model into a W x H canvas: scale and offset
  function fit(m, W, H) {
    const pad = 18, b = m.box || bounds(m), bw = b.maxX - b.minX || 1, bh = b.maxY - b.minY || 1;
    const s = Math.min((W - 2 * pad) / bw, (H - 2 * pad) / bh);
    return { s, ox: (W - bw * s) / 2 - b.minX * s, oy: (H - bh * s) / 2 - b.minY * s };
  }

  // paints the model; view = { s, ox, oy } maps model space to CSS pixels, k is the zoom relative to the fit
  function render(cv, m, o, view, k = 1) {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const W = cv.clientWidth || cv.width, H = cv.clientHeight || cv.height;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const { s, ox, oy } = view;
    for (const p of m.nodes) { p.sx = p.x * s + ox; p.sy = p.y * s + oy; }
    const ink = css('--ink-hex', '#121a26'), paper = css('--paper-hi-hex', '#fbfcfd'), ring = css('--g2', '#ec8b3f'), muted = css('--muted-hex', '#5f6b78');
    const g = [0, 1, 2, 3].map(i => css('--g' + i, '#ccc'));
    const hov = o.hover || null;
    const near = new Set();
    if (hov) { near.add(hov); for (const [h, a] of m.links) { if (h === hov) near.add(a); if (a === hov) near.add(h); } }
    c.fillStyle = paper; c.fillRect(0, 0, W, H);
    const zs = Math.sqrt(k);                         // sizes grow slower than the zoom
    for (const [h, a] of m.links) {
      const on = hov && (h === hov || a === hov);
      c.strokeStyle = on ? ring : ink; c.globalAlpha = on ? 0.95 : (hov ? 0.05 : 0.16); c.lineWidth = (on ? 1.6 : 0.6) * zs;
      c.beginPath(); c.moveTo(h.sx, h.sy); c.lineTo(a.sx, a.sy); c.stroke();
    }
    const unit = Math.max(1, s * 0.9 / zs);
    for (const a of m.accs) {
      const lv = level(a, o.preset);
      const r = (Math.min(7, (1.6 + 2.6 * Math.sqrt(a.X / m.maxAcc)) * unit) + (a.by.length > 1 ? 1.2 : 0)) * zs;
      a.sr = r;
      c.globalAlpha = hov && !near.has(a) ? 0.25 : 1;
      c.fillStyle = g[lv]; c.beginPath(); c.arc(a.sx, a.sy, r, 0, 2 * Math.PI); c.fill();
      c.strokeStyle = ink; c.lineWidth = (lv === 3 ? 1.2 : 0.6) * zs; if (lv >= 1) c.stroke();
      if (a.by.length > 1) { c.strokeStyle = ring; c.lineWidth = 1.6 * zs; c.beginPath(); c.arc(a.sx, a.sy, r + 2.6 * zs, 0, 2 * Math.PI); c.stroke(); }
    }
    for (const h of m.hubs) {
      c.globalAlpha = hov && !near.has(h) ? 0.3 : 1;
      const r = Math.max(3.2, 3.6 * unit) * zs; h.sr = r;
      c.fillStyle = ink; c.beginPath(); c.arc(h.sx, h.sy, r, 0, 2 * Math.PI); c.fill();
      c.strokeStyle = paper; c.lineWidth = 1.1 * zs; c.beginPath(); c.moveTo(h.sx - r * 0.5, h.sy - r * 0.5); c.lineTo(h.sx + r * 0.5, h.sy + r * 0.5); c.moveTo(h.sx + r * 0.5, h.sy - r * 0.5); c.lineTo(h.sx - r * 0.5, h.sy + r * 0.5); c.stroke();
    }
    c.globalAlpha = 1;
    // labels come in as you zoom: fraud numbers first, then account numbers
    const font = css('--font-body', 'system-ui');
    if (k >= 2.2) {
      c.font = `500 12px ${font}`; c.fillStyle = ink; c.textBaseline = 'middle';
      for (const h of m.hubs) { if (hov && !near.has(h)) continue; c.fillText(`${o.t('fraud_pick')} ${h.fid}`, h.sx + h.sr + 4, h.sy); }
    }
    if (k >= 4.5) {
      c.font = `400 11px ${font}`; c.fillStyle = muted; c.textBaseline = 'middle';
      for (const a of m.accs) { if (hov && !near.has(a)) continue; c.fillText(String(a.aid), a.sx + a.sr + 3, a.sy); }
    }
    if (hov) { c.strokeStyle = ink; c.lineWidth = 2; c.beginPath(); c.arc(hov.sx, hov.sy, (hov.sr || 6) + 3, 0, 2 * Math.PI); c.stroke(); }
  }

  // the report's static preview
  function draw(cv, m, o) { render(cv, m, o, fit(m, cv.clientWidth || cv.width, cv.clientHeight || cv.height)); }

  function pick(m, x, y) {
    let best = null, bd = 144;
    for (const p of m.nodes) { const d = (p.sx - x) ** 2 + (p.sy - y) ** 2; if (d < bd) { bd = d; best = p; } }
    return best;
  }

  // the live network: physics on a frame loop, drag, zoom, pan, hover, click
  function live(cv, m, o) {
    const st = cv._world || (cv._world = { pointers: new Map() });
    if (st.raf) cancelAnimationFrame(st.raf);
    if (st.cleanup) st.cleanup();
    const W = () => cv.clientWidth || cv.width, H = () => cv.clientHeight || cv.height;
    const base = fit(m, W(), H());
    st.m = m; st.o = o; st.k = 1; st.px = 0; st.py = 0; st.hover = null; st.drag = null; st.alpha = o.reduce ? 0 : 0.35; st.raf = 0;
    const view = () => ({ s: base.s * st.k, ox: base.ox * st.k + st.px + (W() / 2) * (1 - st.k), oy: base.oy * st.k + st.py + (H() / 2) * (1 - st.k) });
    const paint = () => render(cv, m, { ...o, hover: st.hover }, view(), st.k);
    const frame = () => {
      st.raf = 0;
      if (st.alpha > 0.003) { step(m, st.alpha, m.rand); st.alpha *= 0.985; paint(); st.raf = requestAnimationFrame(frame); }
      else { st.alpha = 0; paint(); }
    };
    const heat = (a) => { if (o.reduce) { for (let i = 0; i < 120; i++) step(m, a * (1 - i / 120), m.rand); paint(); return; } st.alpha = Math.max(st.alpha, a); if (!st.raf) st.raf = requestAnimationFrame(frame); };
    const at = (e) => { const r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    const zoomAt = (f, x, y) => {
      const k2 = Math.min(12, Math.max(0.5, st.k * f)), r = k2 / st.k;
      // keep the point under the cursor where it is
      st.px = x - (x - st.px - (W() / 2) * (1 - st.k)) * r - (W() / 2) * (1 - k2);
      st.py = y - (y - st.py - (H() / 2) * (1 - st.k)) * r - (H() / 2) * (1 - k2);
      st.k = k2; paint();
    };
    const tipFor = (p) => {
      const t = o.t;
      return p.kind === 'hub' ? `<b>${t('world_seed', { id: p.fid })}</b><br>${t('world_hub_tip', { n: p.deg })}`
        : `<b>${t('world_acc', { aid: p.aid, ex: p.exchange })}</b><br>${t('world_paid_by', { ids: p.by.map(b => b.fid).join(', ') })}<br>` +
          (o.preset === '10k' ? (level(p, '10k') ? t('flag_10k') : t('not_flagged')) : 'G' + level(p, o.preset));
    };
    const showTip = (p) => {
      const tip = o.tip; if (!tip) return;
      if (!p) { tip.hidden = true; return; }
      tip.innerHTML = tipFor(p);
      const wrap = cv.parentNode.getBoundingClientRect(), r = cv.getBoundingClientRect();
      tip.style.left = `${Math.min(r.width - 200, r.left - wrap.left + p.sx + 14)}px`; tip.style.top = `${r.top - wrap.top + p.sy - 10}px`; tip.hidden = false;
    };
    const onMove = (e) => {
      st.pointers.set(e.pointerId, e);
      if (st.pointers.size === 2) {                       // pinch
        const [a, b] = [...st.pointers.values()];
        const d = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
        if (st.pinch) { const r = cv.getBoundingClientRect(); zoomAt(d / st.pinch, (a.clientX + b.clientX) / 2 - r.left, (a.clientY + b.clientY) / 2 - r.top); }
        st.pinch = d; return;
      }
      const [x, y] = at(e);
      if (st.drag) {
        st.moved = true;
        if (st.drag.kind === 'pan') { st.px = st.drag.px + x - st.drag.x; st.py = st.drag.py + y - st.drag.y; paint(); }
        else { const v = view(); st.drag.node.x = (x - v.ox) / v.s; st.drag.node.y = (y - v.oy) / v.s; if (o.reduce) paint(); else heat(0.12); }
        return;
      }
      const p = pick(m, x, y);
      if (p !== st.hover) { st.hover = p; cv.style.cursor = p ? 'pointer' : 'grab'; paint(); showTip(p); }
    };
    const onDown = (e) => {
      try { cv.setPointerCapture(e.pointerId); } catch (err) { /* a synthetic pointer cannot be captured */ }
      st.pointers.set(e.pointerId, e); st.moved = false;
      if (st.pointers.size > 1) { st.drag = null; return; }
      const [x, y] = at(e); const p = pick(m, x, y);
      if (p) { p.pinned = true; st.drag = { kind: 'node', node: p }; cv.style.cursor = 'grabbing'; }
      else { st.drag = { kind: 'pan', x, y, px: st.px, py: st.py }; cv.style.cursor = 'grabbing'; }
      if (o.tip) o.tip.hidden = true;
    };
    const onUp = (e) => {
      st.pointers.delete(e.pointerId); st.pinch = null;
      if (!st.drag) return;
      if (st.drag.kind === 'node') { st.drag.node.pinned = false; heat(0.08); if (!st.moved && o.onPick) { const p = st.drag.node; if (p.kind === 'hub') o.onPick(p.fid, null); else o.onPick(p.by[0].fid, p.id); } }
      st.drag = null; cv.style.cursor = st.hover ? 'pointer' : 'grab';
    };
    const onLeave = () => { st.hover = null; if (o.tip) o.tip.hidden = true; paint(); };
    const onWheel = (e) => { if (!(e.ctrlKey || e.metaKey || document.activeElement === cv)) return; e.preventDefault(); const [x, y] = at(e); zoomAt(Math.exp(-e.deltaY * 0.0015), x, y); };
    const onDbl = (e) => { const [x, y] = at(e); zoomAt(1.8, x, y); };
    const reset = () => { st.k = 1; st.px = 0; st.py = 0; paint(); };
    const onKey = (e) => {
      if (e.key === '+' || e.key === '=') { zoomAt(1.4, W() / 2, H() / 2); e.preventDefault(); }
      else if (e.key === '-') { zoomAt(1 / 1.4, W() / 2, H() / 2); e.preventDefault(); }
      else if (e.key === '0') { reset(); e.preventDefault(); }
      else if (e.key.startsWith('Arrow')) { const d = 40; st.px += e.key === 'ArrowLeft' ? d : e.key === 'ArrowRight' ? -d : 0; st.py += e.key === 'ArrowUp' ? d : e.key === 'ArrowDown' ? -d : 0; paint(); e.preventDefault(); }
    };
    const zi = () => zoomAt(1.4, W() / 2, H() / 2), zo = () => zoomAt(1 / 1.4, W() / 2, H() / 2);
    cv.addEventListener('pointermove', onMove); cv.addEventListener('pointerdown', onDown); cv.addEventListener('pointerup', onUp);
    cv.addEventListener('pointercancel', onUp); cv.addEventListener('pointerleave', onLeave); cv.addEventListener('wheel', onWheel, { passive: false });
    cv.addEventListener('dblclick', onDbl); cv.addEventListener('keydown', onKey);
    if (o.zoomIn) o.zoomIn.addEventListener('click', zi); if (o.zoomOut) o.zoomOut.addEventListener('click', zo); if (o.reset) o.reset.addEventListener('click', reset);
    st.cleanup = () => {
      cv.removeEventListener('pointermove', onMove); cv.removeEventListener('pointerdown', onDown); cv.removeEventListener('pointerup', onUp);
      cv.removeEventListener('pointercancel', onUp); cv.removeEventListener('pointerleave', onLeave); cv.removeEventListener('wheel', onWheel);
      cv.removeEventListener('dblclick', onDbl); cv.removeEventListener('keydown', onKey);
      if (o.zoomIn) o.zoomIn.removeEventListener('click', zi); if (o.zoomOut) o.zoomOut.removeEventListener('click', zo); if (o.reset) o.reset.removeEventListener('click', reset);
      if (st.raf) cancelAnimationFrame(st.raf); st.raf = 0;
    };
    cv.style.cursor = 'grab'; cv.tabIndex = 0;
    paint();
    if (!o.reduce) heat(0.35);
  }

  return { build, draw, live, level, cache };
})();
