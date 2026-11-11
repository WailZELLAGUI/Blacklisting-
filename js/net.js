/* Draws one fraud: blacklisted address -> (collector) -> accounts grouped by exchange. Plain SVG, no library.
   Grades are drawn as rings as well as colour (G1 single, G2 double, G3 heavy double), so they read in grayscale.
   Hovering or focusing an account lights its money path from the blacklisted address and dims the rest. */
const NET = (() => {
  const NS = 'http://www.w3.org/2000/svg';
  const css = (name, fb) => (getComputedStyle(document.documentElement).getPropertyValue(name) || '').trim() || fb;
  const ROLE_VAR = { SELF: '--role-self', MULE: '--role-mule', FACILITATOR: '--role-fac', ACCOMPLICE: '--role-acc', P2P: '--role-p2p', VICTIM: '--role-victim',
    SERVICE: '--role-service', DUST: '--role-dust', FRAMED: '--role-framed', BAIT: '--role-bait', LANDLORD: '--role-landlord' };
  const ROLE_COLORS = new Proxy({}, { get: (_, k) => css(ROLE_VAR[k] || '--color-muted', '#999') });
  const GRADE_COLORS = new Proxy([], { get: (_, i) => i === 'length' ? 4 : css('--g' + i, '#ccc') });
  const INVOLVED = new Set(['SELF', 'MULE', 'FACILITATOR']);
  const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
  let last = null;

  function flagged(n, preset) { return preset === '10k' ? n.ten_k : n.grade >= 2; }
  function level(n, o) { return o.preset === '10k' ? (n.ten_k ? 3 : 0) : n.grade; }
  function fill(n, o) { return o.colorBy === 'truth' ? ROLE_COLORS[n.role] : GRADE_COLORS[level(n, o)]; }
  // rings around a node: the line form of its grade
  function rings(grp, a, lv) {
    if (lv >= 1) el('circle', { cx: a.x, cy: a.y, r: a.r + 1.5, class: 'gr', 'stroke-width': lv === 3 ? 2.5 : 1.5 }, grp);
    if (lv >= 2) el('circle', { cx: a.x, cy: a.y, r: a.r + 4.5, class: 'gr', 'stroke-width': lv === 3 ? 2.5 : 1.5 }, grp);
  }

  function draw(svg, g, o) {
    if (!o.noPlay) last = { svg, g, o };
    svg.innerHTML = '';
    svg.classList.remove('focusing');
    const W = 900, H = 470;
    const k = Math.max(1, W / (svg.getBoundingClientRect().width || W));
    const exFont = `font-size:${(14 * k).toFixed(1)}px`, lblFont = `font-size:${(13 * k).toFixed(1)}px`;
    const ink = css('--color-ink', '#111'), muted = css('--color-muted', '#666'), paper2 = css('--color-paper-2', '#eee'), rule = css('--color-rule', '#ccc'), err = css('--color-error', '#b3261e');
    const nodes = g.nodes, byId = Object.fromEntries(nodes.map(n => [n.id, n]));
    const accts = nodes.filter(n => n.kind === 'account');
    const seed = byId.seed; seed.x = 62; seed.y = 215;
    // an untraced collector sits below, off the links: the accounts shown got their money from the address itself
    const coll = byId.collector; if (coll) { coll.x = 168; coll.y = coll.found === false ? 300 : 215; }
    const small = byId.small; if (small) { small.x = 62; small.y = 400; }
    const exs = [...new Set(accts.map(a => a.exchange))].sort();
    const x0 = 250, x1 = W - 14, colW = exs.length ? (x1 - x0) / exs.length : 0;
    const maxX = Math.max(1, ...accts.map(a => a.X));
    const gEx = el('g', { 'aria-hidden': 'true' }, svg);
    exs.forEach((ex, i) => {
      const bx = x0 + i * colW + 6, bw = colW - 12;
      el('rect', { x: bx, y: 28, width: bw, height: H - 44, class: 'exbox' }, gEx);
      const full = `${o.t('exch')} ${ex}`, fits = full.length * 0.56 * 14 * k <= bw;   // too narrow: the letter alone
      const t = el('text', { x: bx + bw / 2, y: 20, class: 'exlab', style: exFont }, gEx); t.textContent = fits ? full : ex;
      const list = accts.filter(a => a.exchange === ex).sort((a, b) => b.X - a.X);
      const perCol = Math.min(list.length, 9), sub = Math.ceil(list.length / 9);
      const cw = bw / sub, ch = (H - 70) / Math.max(perCol, 1);
      list.forEach((a, j) => {
        const c = Math.floor(j / 9), r = j % 9;
        a.x = bx + cw * (c + 0.5); a.y = 46 + ch * (r + 0.5);
        a.r = Math.max(6, Math.min(Math.min(cw, ch) / 2 - 6, 6 + 12 * Math.sqrt(a.X / maxX)));
      });
    });
    // links, each one remembers the account it pays
    const gL = el('g', { 'aria-hidden': 'true' }, svg);
    const order = [...accts].sort((a, b) => a.t_first_h - b.t_first_h);
    const rank = new Map(order.map((a, i) => [a.id, i]));
    const linkEls = [];
    for (const l of g.links) {
      const s = byId[l.source], t = byId[l.target];
      if (!s || !t) continue;
      const mx = (s.x + t.x) / 2;
      const w = t.kind === 'account' ? 0.8 + 3.2 * Math.sqrt(t.X / maxX) : 1.2;
      const p = el('path', { d: `M${s.x},${s.y} C${mx},${s.y} ${mx},${t.y} ${t.x},${t.y}`, class: 'lk', 'stroke-width': w, 'data-to': t.id }, gL);
      linkEls.push([p, t.kind === 'account' ? rank.get(t.id) : -1]);
    }
    for (const ids of g.same_person || []) {
      for (let i = 1; i < ids.length; i++) {
        const a = byId[ids[i - 1]], b = byId[ids[i]];
        if (!a || !b) continue;
        const my = Math.min(a.y, b.y) - 40;
        el('path', { d: `M${a.x},${a.y} Q${(a.x + b.x) / 2},${my} ${b.x},${b.y}`, class: 'sp-l' }, gL);
      }
    }
    // seed, collector, small receivers
    const gN = el('g', {}, svg);
    const gS = el('g', { 'aria-hidden': 'true' }, gN);
    el('circle', { cx: seed.x, cy: seed.y, r: 22, fill: ink }, gS);
    el('path', { d: `M${seed.x - 9},${seed.y - 9} L${seed.x + 9},${seed.y + 9} M${seed.x + 9},${seed.y - 9} L${seed.x - 9},${seed.y + 9}`, stroke: css('--color-paper-hi', '#fff'), 'stroke-width': 3.5 }, gS);
    if (!o.static) { const ts = el('text', { x: 10, y: seed.y - 32, class: 'lbl', style: lblFont, 'text-anchor': 'start' }, gS); ts.textContent = o.t('legend_seed'); }
    if (coll) {
      const traced = coll.found !== false;
      el('rect', traced ? { x: coll.x - 16, y: coll.y - 16, width: 32, height: 32, fill: muted }
        : { x: coll.x - 16, y: coll.y - 16, width: 32, height: 32, fill: css('--color-paper-hi', '#fff'), stroke: ink, 'stroke-width': 2.5, 'stroke-dasharray': '5 4' }, gS);
      if (!o.static) { const tc = el('text', { x: coll.x, y: coll.y + 36, class: 'lbl', style: lblFont, 'text-anchor': 'middle' }, gS); tc.textContent = o.t('legend_coll'); }
      if (!traced) { const tn = el('text', { x: coll.x, y: coll.y + 36 + 15 * k, class: 'lbl', style: lblFont + `;fill:${err}`, 'text-anchor': 'middle' }, gS); tn.textContent = o.t('coll_not_traced'); }
    }
    if (small) {
      el('rect', { x: small.x - 46, y: small.y - 20, width: 92, height: 40, fill: paper2, stroke: rule }, gS);
      const t1 = el('text', { x: small.x, y: small.y - 3, class: 'lbl', style: lblFont, 'text-anchor': 'middle' }, gS); t1.textContent = `${small.n} ×`;
      const t2 = el('text', { x: small.x, y: small.y + 14, class: 'lbl', style: lblFont, 'text-anchor': 'middle' }, gS); t2.textContent = o.lang === 'fr' ? '< 100 €' : '< €100';
    }
    // accounts: each one is a focusable button
    const accEls = [];
    const describe = (a) => {
      const gradeTxt = o.preset === '10k' ? (a.ten_k ? o.t('flag_10k') : o.t('not_flagged')) : 'G' + a.grade;
      return `${o.t('card_h')} ${a.aid}, ${o.t('exch')} ${a.exchange}, ${gradeTxt}, ${o.eur ? o.eur(a.X) : Math.round(a.X)}` + (o.colorBy === 'truth' ? `, ${o.t('roles')[a.role] || a.role}` : '');
    };
    const focusOn = (a, grp) => {
      svg.classList.add('focusing');
      grp.classList.add('hot');
      svg.querySelectorAll(`.lk[data-to="${a.id}"]`).forEach(p => p.classList.add('on'));
      if (coll && coll.found !== false) svg.querySelectorAll('.lk[data-to="collector"]').forEach(p => p.classList.add('on'));
      if (o.tip) {
        const pct = (x) => x === null || x === undefined ? '–' : Math.round(100 * x) + ' %';
        o.tip.innerHTML = `<b>${o.t('card_h')} ${a.aid}</b>, ${o.t('exch')} ${a.exchange}<br>${o.eur ? o.eur(a.X) : ''}, ${o.t('card_pi')}: ${pct(a.pass_24h)}<br>` +
          (o.preset === '10k' ? (a.ten_k ? o.t('flag_10k') : o.t('not_flagged')) : 'G' + a.grade) + (o.colorBy === 'truth' ? `, ${o.t('roles')[a.role] || a.role}` : '');
        const box = svg.getBoundingClientRect(), wrap = o.tip.parentNode.getBoundingClientRect(), sc = box.width / W;
        o.tip.style.left = `${box.left - wrap.left + o.tip.parentNode.scrollLeft + a.x * sc + 16}px`;
        o.tip.style.top = `${box.top - wrap.top + a.y * sc - 8}px`;
        o.tip.hidden = false;
      }
    };
    const focusOff = (grp) => {
      svg.classList.remove('focusing'); grp.classList.remove('hot');
      svg.querySelectorAll('.lk.on').forEach(p => p.classList.remove('on'));
      if (o.tip) o.tip.hidden = true;
    };
    for (const a of accts) {
      const lv = level(a, o);
      const inv = INVOLVED.has(a.role), fl = flagged(a, o.preset);
      const label = describe(a);
      const attrs = { class: 'acc' + (o.selected === a.id ? ' sel' : ''), 'data-id': a.id };
      if (!o.static) Object.assign(attrs, { tabindex: 0, role: 'button', 'aria-label': label, 'aria-pressed': String(o.selected === a.id) });
      const grp = el('g', attrs, gN);
      el('circle', { cx: a.x, cy: a.y, r: Math.max(a.r + 6, 14), class: 'hit' }, grp);
      if (o.colorBy === 'grade') rings(grp, a, lv);
      el('circle', { cx: a.x, cy: a.y, r: a.r, fill: fill(a, o), class: 'dot' }, grp);
      el('circle', { cx: a.x, cy: a.y, r: a.r + 9, class: 'focus', fill: 'none', stroke: 'none' }, grp);
      if (!o.tip) { const tt = el('title', {}, grp); tt.textContent = label; }
      if (o.mistakes && o.colorBy === 'grade') {
        if (fl && !inv) el('circle', { cx: a.x, cy: a.y, r: a.r + 8, class: 'mist', stroke: err, 'stroke-dasharray': '3 3' }, grp);
        if (!fl && inv) el('circle', { cx: a.x, cy: a.y, r: a.r + 8, class: 'mist', stroke: ink }, grp);
      }
      if (!o.static) {
        grp.addEventListener('mouseenter', () => focusOn(a, grp));
        grp.addEventListener('mouseleave', () => focusOff(grp));
        grp.addEventListener('focus', () => focusOn(a, grp));
        grp.addEventListener('blur', () => focusOff(grp));
        grp.addEventListener('click', () => { o.onSelect && o.onSelect(a); });
      }
      accEls.push([grp, rank.get(a.id)]);
    }
    return { linkEls, accEls };
  }

  function animate({ linkEls, accEls }) {
    const n = Math.max(1, accEls.length);
    linkEls.forEach(([p, r]) => {
      const len = p.getTotalLength();
      p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
      p.style.transition = 'none';
      const delay = r < 0 ? 0 : 300 + (r / n) * 2600;
      setTimeout(() => { p.style.transition = 'stroke-dashoffset 0.7s cubic-bezier(.16,1,.3,1)'; p.style.strokeDashoffset = 0; }, delay);
    });
    accEls.forEach(([gr, r]) => {
      gr.style.opacity = 0; gr.style.transition = 'opacity .4s';
      setTimeout(() => { gr.style.opacity = ''; gr.style.transition = ''; }, 900 + (r / n) * 2600);
    });
  }
  function play(reduce) {
    if (!last) return;
    const els = draw(last.svg, last.g, last.o);
    if (!reduce) animate(els);
  }

  function ringSwatch(lv, color) {
    const s = 18, c = s / 2, ink = css('--color-ink', '#111');
    let h = `<svg width="${s + 8}" height="${s + 8}" viewBox="-4 -4 ${s + 8} ${s + 8}" aria-hidden="true"><circle cx="${c}" cy="${c}" r="5" fill="${color}"/>`;
    if (lv >= 1) h += `<circle cx="${c}" cy="${c}" r="6.5" fill="none" stroke="${ink}" stroke-width="${lv === 3 ? 2 : 1.2}"/>`;
    if (lv >= 2) h += `<circle cx="${c}" cy="${c}" r="9.5" fill="none" stroke="${ink}" stroke-width="${lv === 3 ? 2 : 1.2}"/>`;
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
      h += `<span><i style="border:2px dashed ${css('--color-error', '#b3261e')};background:none"></i>${o.t('innocent_flagged')}</span>`;
      h += `<span><i style="border:2px solid ${css('--color-ink', '#111')};background:none"></i>${o.t('involved_missed')}</span>`;
    }
    h += `<span><i style="border-top:2px dashed ${css('--color-ink', '#111')};background:none;border-radius:0;height:0;width:18px"></i>${o.t('same_person')}</span>`;
    if (g.nodes.some(n => n.id === 'collector' && n.found === false)) h += `<span><i style="border:2px dashed ${css('--color-ink', '#111')};background:none;border-radius:0"></i>${o.t('coll_untraced_legend')}</span>`;
    box.innerHTML = h;
  }

  return { draw, play, animate, legend, flagged, level, ringSwatch, ROLE_COLORS, GRADE_COLORS, INVOLVED, css };
})();
