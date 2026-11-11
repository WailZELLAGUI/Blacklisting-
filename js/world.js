/* The whole world as one network: every fraud's blacklisted address is a hub, every receiving account a dot.
   An account paid by two frauds or more is pulled between their hubs and ringed, so it ties the frauds together.
   Canvas, with a small force layout written for this page (no library); the layout is seeded, so it repeats. */
const WORLD = (() => {
  const css = (n, fb) => NET.css(n, fb);
  const cache = new Map();

  function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

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
    // force layout: pairwise repulsion with a cutoff, springs on links, a light pull to the centre
    const N = nodes.length;
    for (let it = 0, alpha = 1; it < 320; it++, alpha *= 0.988) {
      for (let i = 0; i < N; i++) {
        const p = nodes[i];
        for (let j = i + 1; j < N; j++) {
          const q = nodes[j]; let dx = p.x - q.x, dy = p.y - q.y; let d2 = dx * dx + dy * dy;
          const hubs2 = p.kind === 'hub' && q.kind === 'hub';
          if (!hubs2 && d2 > 2500) continue; if (d2 < 0.01) { dx = rand() - 0.5; dy = rand() - 0.5; d2 = 0.25; }
          const f = (hubs2 ? 700 : 70) / d2 * alpha;   // hubs push each other far apart, so every fraud reads as its own star
          p.vx += dx * f; p.vy += dy * f; q.vx -= dx * f; q.vy -= dy * f;
        }
      }
      for (const [h, a] of links) {
        const dx = a.x - h.x, dy = a.y - h.y, d = Math.sqrt(dx * dx + dy * dy) || 1;
        const rest = 20 + 4.5 * Math.sqrt(h.deg), f = (d - rest) * 0.08 * alpha;
        a.vx -= dx / d * f; a.vy -= dy / d * f; h.vx += dx / d * f * 0.25; h.vy += dy / d * f * 0.25;
      }
      for (const p of nodes) { p.vx -= p.x * 0.006 * alpha; p.vy -= p.y * 0.006 * alpha; p.x += p.vx; p.y += p.vy; p.vx *= 0.55; p.vy *= 0.55; }
    }
    const q = (arr, f) => { const v = arr.slice().sort((a, b) => a - b); return v[Math.min(v.length - 1, Math.max(0, Math.round(f * (v.length - 1))))]; };
    const xs = nodes.map(p => p.x), ys = nodes.map(p => p.y);
    const minX = q(xs, 0.02), maxX = q(xs, 0.98), minY = q(ys, 0.02), maxY = q(ys, 0.98);
    for (const p of nodes) { p.x = Math.min(maxX, Math.max(minX, p.x)); p.y = Math.min(maxY, Math.max(minY, p.y)); }
    const maxAcc = Math.max(1, ...[...accs.values()].map(a => a.X));
    const model = { hubs, accs: [...accs.values()], links, nodes, box: { minX, minY, maxX, maxY }, maxAcc,
      shared: [...accs.values()].filter(a => a.by.length > 1) };
    cache.set(key, model);
    return model;
  }

  function level(acc, preset) {
    let lv = 0;
    for (const b of acc.by) lv = Math.max(lv, preset === '10k' ? (b.node.ten_k ? 3 : 0) : b.node.grade);
    return lv;
  }

  // draw into a canvas; o: { preset, t, hover, interactive }
  function draw(cv, m, o) {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const W = cv.clientWidth || cv.width, H = cv.clientHeight || cv.height;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const pad = 18, bw = m.box.maxX - m.box.minX || 1, bh = m.box.maxY - m.box.minY || 1;
    const s = Math.min((W - 2 * pad) / bw, (H - 2 * pad) / bh);
    const ox = (W - bw * s) / 2 - m.box.minX * s, oy = (H - bh * s) / 2 - m.box.minY * s;
    for (const p of m.nodes) { p.sx = p.x * s + ox; p.sy = p.y * s + oy; }
    const ink = css('--ink-hex', '#121a26'), paper = css('--paper-hi-hex', '#fbfcfd'), ring = css('--g2', '#ec8b3f');
    const g = [0, 1, 2, 3].map(i => css('--g' + i, '#ccc'));
    const hov = o.hover || null;
    const near = new Set();
    if (hov) { near.add(hov); for (const [h, a] of m.links) { if (h === hov) near.add(a); if (a === hov) near.add(h); } }
    c.fillStyle = paper; c.fillRect(0, 0, W, H);
    // links
    c.lineWidth = 0.6;
    for (const [h, a] of m.links) {
      const on = hov && (h === hov || a === hov);
      c.strokeStyle = on ? ring : ink; c.globalAlpha = on ? 0.95 : (hov ? 0.05 : 0.16); c.lineWidth = on ? 1.6 : 0.6;
      c.beginPath(); c.moveTo(h.sx, h.sy); c.lineTo(a.sx, a.sy); c.stroke();
    }
    // accounts
    const unit = Math.max(1, s * 0.9);
    for (const a of m.accs) {
      const lv = level(a, o.preset), r = Math.min(7, (1.6 + 2.6 * Math.sqrt(a.X / m.maxAcc)) * unit) + (a.by.length > 1 ? 1.2 : 0);
      c.globalAlpha = hov && !near.has(a) ? 0.25 : 1;
      c.fillStyle = g[lv]; c.beginPath(); c.arc(a.sx, a.sy, r, 0, 2 * Math.PI); c.fill();
      c.strokeStyle = ink; c.lineWidth = lv === 3 ? 1.2 : 0.6; if (lv >= 1) c.stroke();
      if (a.by.length > 1) { c.strokeStyle = ring; c.lineWidth = 1.6; c.beginPath(); c.arc(a.sx, a.sy, r + 2.6, 0, 2 * Math.PI); c.stroke(); }
    }
    // hubs: the blacklisted addresses
    for (const h of m.hubs) {
      c.globalAlpha = hov && !near.has(h) ? 0.3 : 1;
      const r = Math.max(3.2, 3.6 * unit);
      c.fillStyle = ink; c.beginPath(); c.arc(h.sx, h.sy, r, 0, 2 * Math.PI); c.fill();
      c.strokeStyle = paper; c.lineWidth = 1.1; c.beginPath(); c.moveTo(h.sx - r * 0.5, h.sy - r * 0.5); c.lineTo(h.sx + r * 0.5, h.sy + r * 0.5); c.moveTo(h.sx + r * 0.5, h.sy - r * 0.5); c.lineTo(h.sx - r * 0.5, h.sy + r * 0.5); c.stroke();
    }
    c.globalAlpha = 1;
    if (hov) { c.strokeStyle = ink; c.lineWidth = 2; c.beginPath(); c.arc(hov.sx, hov.sy, hov.kind === 'hub' ? 9 : 8, 0, 2 * Math.PI); c.stroke(); }
  }

  function pick(m, x, y) {
    let best = null, bd = 144;
    for (const p of m.nodes) { const d = (p.sx - x) ** 2 + (p.sy - y) ** 2; if (d < bd) { bd = d; best = p; } }
    return best;
  }

  // interactive canvas: hover tooltip, click opens a fraud (and its account)
  function attach(cv, getModel, o) {
    if (cv._world) { cv._world.o = o; return; }
    const st = cv._world = { o };
    const at = (e) => { const r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    cv.addEventListener('mousemove', (e) => {
      const m = getModel(); if (!m) return;
      const p = pick(m, ...at(e));
      if (p === st.hover) return; st.hover = p;
      draw(cv, m, { ...st.o, hover: p });
      const tip = st.o.tip; if (!tip) return;
      if (!p) { tip.hidden = true; return; }
      const t = st.o.t;
      tip.innerHTML = p.kind === 'hub' ? `<b>${t('world_seed', { id: p.fid })}</b>`
        : `<b>${t('world_acc', { aid: p.aid, ex: p.exchange })}</b><br>${t('world_paid_by', { ids: p.by.map(b => b.fid).join(', ') })}<br>` +
          (st.o.preset === '10k' ? (level(p, '10k') ? t('flag_10k') : t('not_flagged')) : 'G' + level(p, st.o.preset));
      const wrap = cv.parentNode.getBoundingClientRect(), r = cv.getBoundingClientRect();
      tip.style.left = `${r.left - wrap.left + p.sx + 14}px`; tip.style.top = `${r.top - wrap.top + p.sy - 10}px`; tip.hidden = false;
    });
    cv.addEventListener('mouseleave', () => { st.hover = null; const m = getModel(); if (m) draw(cv, m, st.o); if (st.o.tip) st.o.tip.hidden = true; });
    cv.addEventListener('click', (e) => {
      const m = getModel(); if (!m) return;
      const p = pick(m, ...at(e)); if (!p || !st.o.onPick) return;
      if (p.kind === 'hub') st.o.onPick(p.fid, null); else st.o.onPick(p.by[0].fid, p.id);
    });
  }

  return { build, draw, attach, level, cache };
})();
