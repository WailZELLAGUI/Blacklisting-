/* Draws one fraud: blacklisted address -> (collector) -> accounts grouped by exchange. Plain SVG, no library.
   Grades are drawn as rings as well as colour (G1 single, G2 double, G3 heavy double), so they read in grayscale. */
const NET = (() => {
  const NS = 'http://www.w3.org/2000/svg';
  const ROLE_COLORS = { SELF: '#b03a2e', MULE: '#e67e22', FACILITATOR: '#7d3c98', ACCOMPLICE: '#c9a227',
    P2P: '#5dade2', VICTIM: '#45b39d', SERVICE: '#85929e', DUST: '#d5d8dc', FRAMED: '#2e86c1', BAIT: '#aab7b8', LANDLORD: '#82c09a' };
  const GRADE_COLORS = ['#d8d8d4', '#f2c230', '#e07b1f', '#b3261e'];
  const INVOLVED = new Set(['SELF', 'MULE', 'FACILITATOR']);
  const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
  let last = null;

  function flagged(n, preset) { return preset === '10k' ? n.ten_k : n.grade >= 2; }
  function level(n, o) { return o.preset === '10k' ? (n.ten_k ? 3 : 0) : n.grade; }
  function fill(n, o) {
    if (o.colorBy === 'truth') return ROLE_COLORS[n.role] || '#999';
    return GRADE_COLORS[level(n, o)];
  }
  // rings around a node: the line form of its grade
  function rings(grp, a, lv) {
    if (lv >= 1) el('circle', { cx: a.x, cy: a.y, r: a.r + 1.5, class: 'gr', 'stroke-width': lv === 3 ? 2.5 : 1.5 }, grp);
    if (lv >= 2) el('circle', { cx: a.x, cy: a.y, r: a.r + 4.5, class: 'gr', 'stroke-width': lv === 3 ? 2.5 : 1.5 }, grp);
  }

  function draw(svg, g, o) {
    last = { svg, g, o };
    svg.innerHTML = '';
    const W = 900, H = 470;
    // labels keep a readable size on screen: scale them up when the drawing is shown smaller than its viewBox
    const k = Math.max(1, W / (svg.getBoundingClientRect().width || W));
    const exFont = `font-size:${(14 * k).toFixed(1)}px`, lblFont = `font-size:${(13 * k).toFixed(1)}px`;
    const nodes = g.nodes, byId = Object.fromEntries(nodes.map(n => [n.id, n]));
    const accts = nodes.filter(n => n.kind === 'account');
    const seed = byId.seed; seed.x = 62; seed.y = 215;
    const coll = byId.collector; if (coll) { coll.x = 168; coll.y = 215; }
    const small = byId.small; if (small) { small.x = 62; small.y = 400; }
    // exchanges present, in alphabetical order
    const exs = [...new Set(accts.map(a => a.exchange))].sort();
    const x0 = 250, x1 = W - 14, colW = exs.length ? (x1 - x0) / exs.length : 0;
    const maxX = Math.max(1, ...accts.map(a => a.X));
    const gEx = el('g', { 'aria-hidden': 'true' }, svg);
    exs.forEach((ex, i) => {
      const bx = x0 + i * colW + 6, bw = colW - 12;
      el('rect', { x: bx, y: 28, width: bw, height: H - 44, class: 'exbox' }, gEx);
      const t = el('text', { x: bx + bw / 2, y: 20, class: 'exlab', style: exFont }, gEx); t.textContent = `${o.t('exch')} ${ex}`;
      const list = accts.filter(a => a.exchange === ex).sort((a, b) => b.X - a.X);
      const perCol = Math.min(list.length, 9), sub = Math.ceil(list.length / 9);
      const cw = bw / sub, ch = (H - 70) / Math.max(perCol, 1);
      list.forEach((a, j) => {
        const c = Math.floor(j / 9), r = j % 9;
        a.x = bx + cw * (c + 0.5); a.y = 46 + ch * (r + 0.5);
        a.r = Math.max(6, Math.min(Math.min(cw, ch) / 2 - 6, 6 + 12 * Math.sqrt(a.X / maxX)));
      });
    });
    // links
    const gL = el('g', { 'aria-hidden': 'true' }, svg);
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
    const gS = el('g', { 'aria-hidden': 'true' }, gN);
    el('circle', { cx: seed.x, cy: seed.y, r: 22, fill: '#111' }, gS);
    el('path', { d: `M${seed.x - 9},${seed.y - 9} L${seed.x + 9},${seed.y + 9} M${seed.x + 9},${seed.y - 9} L${seed.x - 9},${seed.y + 9}`, stroke: '#fff', 'stroke-width': 3.5 }, gS);
    const ts = el('text', { x: 10, y: seed.y - 32, class: 'lbl', style: lblFont, 'text-anchor': 'start' }, gS); ts.textContent = o.t('legend_seed');
    if (coll) {
      el('rect', { x: coll.x - 16, y: coll.y - 16, width: 32, height: 32, fill: '#5c5c5c' }, gS);
      const tc = el('text', { x: coll.x, y: coll.y + 36, class: 'lbl', style: lblFont, 'text-anchor': 'middle' }, gS); tc.textContent = o.t('legend_coll');
    }
    if (small) {
      el('rect', { x: small.x - 46, y: small.y - 20, width: 92, height: 40, fill: '#f6f6f3', stroke: '#d4d4cf' }, gS);
      const t1 = el('text', { x: small.x, y: small.y - 3, class: 'lbl', style: lblFont, 'text-anchor': 'middle' }, gS); t1.textContent = `${small.n} ×`;
      const t2 = el('text', { x: small.x, y: small.y + 14, class: 'lbl', style: lblFont, 'text-anchor': 'middle' }, gS); t2.textContent = o.lang === 'fr' ? '< 100 €' : '< €100';
    }
    // accounts: each one is a focusable button
    const accEls = [];
    for (const a of accts) {
      const lv = level(a, o);
      const inv = INVOLVED.has(a.role), fl = flagged(a, o.preset);
      const gradeTxt = o.preset === '10k' ? (a.ten_k ? o.t('flag_10k') : o.t('not_flagged')) : 'G' + a.grade;
      const label = `${o.t('card_h')} ${a.aid}, ${o.t('exch')} ${a.exchange}, ${gradeTxt}, ${o.eur ? o.eur(a.X) : Math.round(a.X)}` +
        (o.colorBy === 'truth' ? `, ${o.t('roles')[a.role] || a.role}` : '');
      const grp = el('g', { class: 'acc' + (o.selected === a.id ? ' sel' : ''), tabindex: 0, role: 'button', 'aria-label': label, 'aria-pressed': String(o.selected === a.id), 'data-id': a.id }, gN);
      el('circle', { cx: a.x, cy: a.y, r: Math.max(a.r + 6, 14), class: 'hit' }, grp);
      if (o.colorBy === 'grade') rings(grp, a, lv);
      el('circle', { cx: a.x, cy: a.y, r: a.r, fill: fill(a, o), class: 'dot' }, grp);
      el('circle', { cx: a.x, cy: a.y, r: a.r + 9, class: 'focus', fill: 'none', stroke: 'none' }, grp);
      const tt = el('title', {}, grp); tt.textContent = label;
      if (o.mistakes && o.colorBy === 'grade') {
        if (fl && !inv) el('circle', { cx: a.x, cy: a.y, r: a.r + 8, class: 'mist', stroke: '#b3261e', 'stroke-dasharray': '3 3' }, grp);
        if (!fl && inv) el('circle', { cx: a.x, cy: a.y, r: a.r + 8, class: 'mist', stroke: '#111', 'stroke-dasharray': '1 0' }, grp);
      }
      grp.addEventListener('click', () => { o.onSelect && o.onSelect(a); });
      accEls.push([grp, rank.get(a.id)]);
    }
    return { linkEls, accEls };
  }

  function play(reduce) {
    if (!last) return;
    const { linkEls, accEls } = draw(last.svg, last.g, last.o);
    if (reduce) return;
    const n = Math.max(1, accEls.length);
    linkEls.forEach(([p, r]) => {
      const len = p.getTotalLength();
      p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
      p.style.transition = 'none';
      const delay = r < 0 ? 0 : 300 + (r / n) * 2600;
      setTimeout(() => { p.style.transition = 'stroke-dashoffset 0.7s cubic-bezier(.2,.8,.2,1)'; p.style.strokeDashoffset = 0; }, delay);
    });
    accEls.forEach(([gr, r]) => {
      gr.style.opacity = 0; gr.style.transition = 'opacity .4s';
      setTimeout(() => { gr.style.opacity = 1; }, 900 + (r / n) * 2600);
    });
  }

  function ringSwatch(lv, color) {
    const s = 18, c = s / 2;
    let h = `<svg width="${s + 8}" height="${s + 8}" viewBox="-4 -4 ${s + 8} ${s + 8}" aria-hidden="true"><circle cx="${c}" cy="${c}" r="5" fill="${color}"/>`;
    if (lv >= 1) h += `<circle cx="${c}" cy="${c}" r="6.5" fill="none" stroke="#111" stroke-width="${lv === 3 ? 2 : 1.2}"/>`;
    if (lv >= 2) h += `<circle cx="${c}" cy="${c}" r="9.5" fill="none" stroke="#111" stroke-width="${lv === 3 ? 2 : 1.2}"/>`;
    return h + '</svg>';
  }
  function legend(box, o, g) {
    const items = [];
    if (o.colorBy === 'truth') {
      const present = [...new Set(g.nodes.filter(n => n.kind === 'account').map(n => n.role))];
      for (const r of present) items.push(`<span><i style="background:${ROLE_COLORS[r]}"></i>${o.t('roles')[r] + (INVOLVED.has(r) ? ` (${o.t('involved')})` : '')}</span>`);
    } else if (o.preset === '10k') {
      items.push(`<span>${ringSwatch(3, GRADE_COLORS[3])}${o.t('card_10k')}</span>`, `<span>${ringSwatch(0, GRADE_COLORS[0])}${o.t('not_flagged')}</span>`);
    } else {
      ['G0', 'G1', 'G2', 'G3'].forEach((gname, i) => items.push(`<span>${ringSwatch(i, GRADE_COLORS[i])}${gname}</span>`));
    }
    let h = items.join('');
    if (o.mistakes && o.colorBy === 'grade') {
      h += `<span><i style="border:2px dashed #b3261e;background:none"></i>${o.t('innocent_flagged')}</span>`;
      h += `<span><i style="border:2px solid #111;background:none"></i>${o.t('involved_missed')}</span>`;
    }
    h += `<span><i style="border-top:2px dashed #2a5db0;background:none;border-radius:0;height:0;width:18px"></i>${o.t('same_person')}</span>`;
    box.innerHTML = h;
  }

  return { draw, play, legend, ROLE_COLORS, GRADE_COLORS, INVOLVED };
})();
