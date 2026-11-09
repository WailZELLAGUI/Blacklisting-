/* Draws one fraud: blacklisted address -> (collector) -> accounts grouped by exchange. Plain SVG, no library. */
const NET = (() => {
  const NS = 'http://www.w3.org/2000/svg';
  const ROLE_COLORS = { SELF: '#b03a2e', MULE: '#e67e22', FACILITATOR: '#7d3c98', ACCOMPLICE: '#c9a227',
    P2P: '#5dade2', VICTIM: '#45b39d', SERVICE: '#85929e', DUST: '#d5d8dc', FRAMED: '#2e86c1', BAIT: '#aab7b8', LANDLORD: '#82c09a' };
  const GRADE_COLORS = ['#d9dde3', '#f2c94c', '#f2994a', '#c0392b'];
  const INVOLVED = new Set(['SELF', 'MULE', 'FACILITATOR']);
  const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
  let last = null;

  function flagged(n, preset) { return preset === '10k' ? n.ten_k : n.grade >= 2; }
  function fill(n, o) {
    if (o.colorBy === 'truth') return ROLE_COLORS[n.role] || '#999';
    if (o.preset === '10k') return n.ten_k ? GRADE_COLORS[3] : GRADE_COLORS[0];
    return GRADE_COLORS[n.grade];
  }

  function draw(svg, g, o) {
    last = { svg, g, o };
    svg.innerHTML = '';
    const W = 900, H = 470;
    const nodes = g.nodes, byId = Object.fromEntries(nodes.map(n => [n.id, n]));
    const accts = nodes.filter(n => n.kind === 'account');
    const seed = byId.seed; seed.x = 62; seed.y = 215;
    const coll = byId.collector; if (coll) { coll.x = 168; coll.y = 215; }
    const small = byId.small; if (small) { small.x = 62; small.y = 400; }
    // exchanges present, in alphabetical order
    const exs = [...new Set(accts.map(a => a.exchange))].sort();
    const x0 = 250, x1 = W - 14, colW = exs.length ? (x1 - x0) / exs.length : 0;
    const maxX = Math.max(1, ...accts.map(a => a.X));
    const gEx = el('g', {}, svg);
    exs.forEach((ex, i) => {
      const bx = x0 + i * colW + 6, bw = colW - 12;
      el('rect', { x: bx, y: 24, width: bw, height: H - 40, rx: 10, class: 'exbox' }, gEx);
      const t = el('text', { x: bx + bw / 2, y: 17, class: 'exlab' }, gEx); t.textContent = `${o.t('exch')} ${ex}`;
      const list = accts.filter(a => a.exchange === ex).sort((a, b) => b.X - a.X);
      const perCol = Math.min(list.length, 9), sub = Math.ceil(list.length / 9);
      const cw = bw / sub, ch = (H - 64) / Math.max(perCol, 1);
      list.forEach((a, j) => {
        const c = Math.floor(j / 9), r = j % 9;
        a.x = bx + cw * (c + 0.5); a.y = 40 + ch * (r + 0.5);
        a.r = Math.max(5, Math.min(Math.min(cw, ch) / 2 - 3, 5 + 13 * Math.sqrt(a.X / maxX)));
      });
    });
    // links
    const gL = el('g', {}, svg);
    const order = [...accts].sort((a, b) => a.t_first_h - b.t_first_h);
    const rank = new Map(order.map((a, i) => [a.id, i]));
    const linkEls = [];
    for (const l of g.links) {
      const s = byId[l.source], t = byId[l.target];
      if (!s || !t) continue;
      const mx = (s.x + t.x) / 2;
      const w = t.kind === 'account' ? 0.8 + 3.2 * Math.sqrt(t.X / maxX) : 1.2;
      const p = el('path', { d: `M${s.x},${s.y} C${mx},${s.y} ${mx},${t.y} ${t.x},${t.y}`, class: 'lk', 'stroke-width': w }, gL);
      linkEls.push([p, t.kind === 'account' ? rank.get(t.id) : -1]);
    }
    // same person across exchanges
    for (const ids of g.same_person || []) {
      for (let i = 1; i < ids.length; i++) {
        const a = byId[ids[i - 1]], b = byId[ids[i]];
        if (!a || !b) continue;
        const my = Math.min(a.y, b.y) - 40;
        el('path', { d: `M${a.x},${a.y} Q${(a.x + b.x) / 2},${my} ${b.x},${b.y}`, class: 'sp-l' }, gL);
      }
    }
    // seed, collector, small
    const gN = el('g', {}, svg);
    el('circle', { cx: seed.x, cy: seed.y, r: 22, fill: '#c0392b' }, gN);
    el('path', { d: `M${seed.x - 9},${seed.y - 9} L${seed.x + 9},${seed.y + 9} M${seed.x + 9},${seed.y - 9} L${seed.x - 9},${seed.y + 9}`, stroke: '#fff', 'stroke-width': 3.5 }, gN);
    const ts = el('text', { x: seed.x, y: seed.y + 38, class: 'lbl', 'text-anchor': 'middle' }, gN); ts.textContent = o.t('legend_seed');
    if (coll) {
      el('rect', { x: coll.x - 16, y: coll.y - 16, width: 32, height: 32, rx: 6, fill: '#566573' }, gN);
      const tc = el('text', { x: coll.x, y: coll.y + 32, class: 'lbl', 'text-anchor': 'middle' }, gN); tc.textContent = o.t('legend_coll');
    }
    if (small) {
      el('rect', { x: small.x - 44, y: small.y - 18, width: 88, height: 36, rx: 8, fill: '#eef1f5', stroke: '#d9dee6' }, gN);
      const t1 = el('text', { x: small.x, y: small.y - 2, class: 'lbl', 'text-anchor': 'middle' }, gN); t1.textContent = `${small.n} ×`;
      const t2 = el('text', { x: small.x, y: small.y + 12, class: 'lbl', 'text-anchor': 'middle' }, gN); t2.textContent = '< €100';
    }
    // accounts
    const accEls = [];
    for (const a of accts) {
      const grp = el('g', {}, gN);
      const c = el('circle', { cx: a.x, cy: a.y, r: a.r, fill: fill(a, o), class: 'acc' + (o.selected === a.id ? ' sel' : '') }, grp);
      const tt = el('title', {}, c);
      tt.textContent = `${o.t('roles')[a.role] || a.role} · ${o.preset === '10k' ? (a.ten_k ? '€10k ✓' : '€10k ✗') : 'G' + a.grade} · €${Math.round(a.X).toLocaleString()}`;
      if (o.mistakes && o.colorBy === 'grade') {
        const inv = INVOLVED.has(a.role), fl = flagged(a, o.preset);
        if (fl && !inv) el('circle', { cx: a.x, cy: a.y, r: a.r + 4, class: 'mist', stroke: '#c0392b', 'stroke-dasharray': '3 2' }, grp);
        if (!fl && inv) el('circle', { cx: a.x, cy: a.y, r: a.r + 4, class: 'mist', stroke: '#1b2230' }, grp);
      }
      c.addEventListener('click', () => { o.onSelect && o.onSelect(a); });
      accEls.push([grp, rank.get(a.id)]);
    }
    return { linkEls, accEls };
  }

  function play() {
    if (!last) return;
    const { linkEls, accEls } = draw(last.svg, last.g, last.o);
    const n = Math.max(1, accEls.length);
    linkEls.forEach(([p, r]) => {
      const len = p.getTotalLength();
      p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
      p.style.transition = 'none';
      const delay = r < 0 ? 0 : 300 + (r / n) * 2600;
      setTimeout(() => { p.style.transition = 'stroke-dashoffset 0.7s ease'; p.style.strokeDashoffset = 0; }, delay);
    });
    accEls.forEach(([gr, r]) => {
      gr.style.opacity = 0; gr.style.transition = 'opacity .4s';
      setTimeout(() => { gr.style.opacity = 1; }, 900 + (r / n) * 2600);
    });
  }

  function legend(box, o, g) {
    const items = [];
    if (o.colorBy === 'truth') {
      const present = [...new Set(g.nodes.filter(n => n.kind === 'account').map(n => n.role))];
      for (const r of present) items.push([ROLE_COLORS[r], o.t('roles')[r] + (INVOLVED.has(r) ? ` (${o.t('involved')})` : '')]);
    } else if (o.preset === '10k') {
      items.push([GRADE_COLORS[3], o.t('card_10k')], [GRADE_COLORS[0], '—']);
    } else {
      ['G0', 'G1', 'G2', 'G3'].forEach((gname, i) => items.push([GRADE_COLORS[i], gname]));
    }
    let h = items.map(([c, l]) => `<span><i style="background:${c}"></i>${l}</span>`).join('');
    if (o.mistakes && o.colorBy === 'grade') {
      h += `<span><i style="border:2px dashed #c0392b;background:none"></i>${o.lang === 'fr' ? 'innocent signalé' : 'innocent flagged'}</span>`;
      h += `<span><i style="border:2px solid #1b2230;background:none"></i>${o.lang === 'fr' ? 'impliqué manqué' : 'involved missed'}</span>`;
    }
    h += `<span><i style="border:2px dashed #1f5f99;background:none;border-radius:0;height:0;width:16px"></i>${o.t('same_person')}</span>`;
    box.innerHTML = h;
  }

  return { draw, play, legend, ROLE_COLORS, GRADE_COLORS, INVOLVED };
})();
