// Interactive explainers for RedTeam Quest. mountViz(root, [[id, config], ...])
const vEl = (tag, props = {}, ...kids) => { const e = Object.assign(document.createElement(tag), props); e.append(...kids); return e; };
const vSvg = (tag, attrs = {}, ...kids) => { const e = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const k in attrs) e.setAttribute(k, attrs[k]); e.append(...kids); return e; };
const vGet = u => fetch(u).then(r => r.json());
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const TITLES = { digit: 'Digit lab', curve: 'Accuracy vs. budget', landscape: 'Loss landscape' };
const MOUNT = { digit: mountDigit, curve: mountCurve, landscape: mountLandscape };

function mountViz(root, list, n) {
  const tabs = vEl('div', { className: 'vtabs' }), panel = vEl('div', { className: 'vpanel' });
  root.replaceChildren(tabs, panel);
  const show = i => { [...tabs.children].forEach((b, j) => b.classList.toggle('on', i === j)); panel.replaceChildren(); MOUNT[list[i][0]](panel, { ...list[i][1], n }); };
  list.forEach(([id], i) => tabs.append(vEl('button', { className: 'vtab', textContent: TITLES[id], onclick: () => show(i) })));
  show(0);
}

// ---- Digit lab: a real FGSM attack on the real model, driven by a slider ----
function paint(canvas, arr, diverging, eps) {
  const ctx = canvas.getContext('2d'), im = ctx.createImageData(28, 28);
  arr.forEach((v, k) => {
    let r, g, b;
    if (diverging) { const t = eps ? clamp(v / eps, -1, 1) : 0; r = 24 + 231 * Math.max(t, 0); g = 24; b = 24 + 231 * Math.max(-t, 0); }
    else r = g = b = v * 255;
    im.data.set([r, g, b, 255], k * 4);
  });
  ctx.putImageData(im, 0, 0);
}
const argmax = a => a.indexOf(Math.max(...a));

function mountDigit(p) {
  let i = Math.floor(Math.random() * 500), eps = 0.2, timer;
  const cs = [0, 1, 2].map(() => vEl('canvas', { width: 28, height: 28, className: 'vcanvas' }));
  const labels = ['Original', 'Change added (red = brighter, blue = darker)', 'Attacked image'];
  const figs = cs.map((c, k) => vEl('figure', { className: 'vfig' }, c, vEl('figcaption', { textContent: labels[k] })));
  const bars = vEl('div', { className: 'vbars' }), info = vEl('div', { className: 'vinfo', ariaLive: 'polite' });
  const readout = vEl('b', { textContent: eps.toFixed(2) });
  const slider = vEl('input', { type: 'range', min: 0, max: 0.4, step: 0.01, value: eps, ariaLabel: 'Attack budget eps' });
  const next = vEl('button', { className: 'ghost sm', textContent: 'Another digit', onclick: () => { i = Math.floor(Math.random() * 500); update(); } });
  p.append(vEl('p', { className: 'dim sm', textContent: 'This runs a real FGSM attack on the real model. Drag the budget (eps) and watch the model\'s confidence move.' }),
    vEl('div', { className: 'vrow' }, ...figs), vEl('div', { className: 'vrow ctl' }, vEl('label', {}, 'Budget eps: ', readout), slider, next), bars, info);
  async function update() {
    const d = await vGet(`/api/viz/digit?i=${i}&eps=${eps}`);
    paint(cs[0], d.x); paint(cs[1], d.delta, true, eps); paint(cs[2], d.adv);
    const pc = argmax(d.pc), pa = argmax(d.pa);
    bars.replaceChildren(...d.pc.map((c, k) => vEl('div', { className: 'vcol' + (k === d.label ? ' true' : '') },
      vEl('div', { className: 'vpair' }, vEl('i', { className: 'c', style: `height:${c * 70}px`, title: `clean: ${(c * 100).toFixed(0)}%` }), vEl('i', { className: 'a', style: `height:${d.pa[k] * 70}px`, title: `attacked: ${(d.pa[k] * 100).toFixed(0)}%` })), vEl('span', { textContent: k }))));
    const fooled = pa !== d.label;
    info.replaceChildren(vEl('div', { textContent: `Model on original: ${pc} (${(d.pc[pc] * 100).toFixed(0)}% sure).  On attacked image: ${pa} (${(d.pa[pa] * 100).toFixed(0)}% sure).  True digit: ${d.label}.` }),
      vEl('div', { className: 'vbadge ' + (fooled ? 'bad' : 'ok'), textContent: fooled ? 'Fooled: the model changed its answer.' : eps ? 'Still correct at this budget. Try a bigger eps.' : 'No attack yet. Drag the slider.' }),
      vEl('div', { className: 'dim sm', textContent: 'Grey bars = confidence before, orange = after. The outlined column is the true digit.' }));
  }
  slider.oninput = () => { eps = +slider.value; readout.textContent = eps.toFixed(2); clearTimeout(timer); timer = setTimeout(update, 100); };
  update();
}

// ---- Accuracy vs budget curve ----
function mountCurve(p, cfg) {
  p.append(vEl('div', { className: 'dim sm', textContent: 'Running the attacks on 500 test digits...' }));
  vGet('/api/viz/curve').then(d => {
    const W = 520, H = 270, m = { l: 46, r: 18, t: 16, b: 40 }, X = e => m.l + e / 0.4 * (W - m.l - m.r), Y = a => H - m.b - a / 100 * (H - m.t - m.b);
    const COL = { fgsm: 'var(--gold)', pgd: 'var(--hot)' }, NAME = { fgsm: 'FGSM (1 step)', pgd: 'PGD (20 steps)' };
    const s = vSvg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'vchart', role: 'img', 'aria-label': 'Model accuracy under attack as the budget grows' });
    for (const a of [0, 25, 50, 75, 100]) s.append(vSvg('line', { x1: m.l, x2: W - m.r, y1: Y(a), y2: Y(a), class: 'grid' }), vSvg('text', { x: m.l - 8, y: Y(a) + 4, 'text-anchor': 'end', class: 'tick' }, a + '%'));
    d.eps.forEach(e => s.append(vSvg('text', { x: X(e), y: H - m.b + 16, 'text-anchor': 'middle', class: 'tick' }, e.toFixed(2))));
    s.append(vSvg('text', { x: (m.l + W - m.r) / 2, y: H - 6, 'text-anchor': 'middle', class: 'tick' }, 'attack budget eps (how much each pixel may change)'));
    if (cfg.eps) s.append(vSvg('line', { x1: X(cfg.eps), x2: X(cfg.eps), y1: m.t, y2: H - m.b, class: 'mark' }), vSvg('text', { x: X(cfg.eps) + 5, y: m.t + 10, class: 'tick' }, `this level: eps ${cfg.eps}`));
    cfg.series.forEach((k, idx) => {
      s.append(vSvg('polyline', { points: d.eps.map((e, j) => `${X(e)},${Y(d[k][j])}`).join(' '), fill: 'none', stroke: COL[k], 'stroke-width': 2.5 }));
      d.eps.forEach((e, j) => s.append(vSvg('circle', { cx: X(e), cy: Y(d[k][j]), r: 4, fill: COL[k] }, vSvg('title', {}, `${NAME[k]}, eps ${e}: ${d[k][j]}% accuracy`))));
      s.append(vSvg('text', { x: W - m.r - 4, y: m.t + 28 + idx * 16, 'text-anchor': 'end', fill: COL[k], class: 'legend' }, NAME[k]));
    });
    p.replaceChildren(vEl('p', { className: 'dim sm', textContent: cfg.series.length > 1
      ? 'Same budget, two attacks. PGD takes many small steps and stays inside the budget, so it beats FGSM. Hover a dot for the exact number.'
      : 'The model is accurate on clean digits (eps 0). As the budget grows, accuracy collapses, long before a human would notice the change.' }), s);
  });
}

// ---- Loss landscape: why FGSM jumps and PGD walks ----
const HILLS = [[0.7, 0.6, 0.1, 1.0], [0.8, -0.5, 0.12, 0.8], [-0.7, 0.2, 0.2, 0.5]];  // [cx, cy, width, height]: places the model is MOST wrong
const loss = (x, y) => HILLS.reduce((s, [cx, cy, v, a]) => s + a * Math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / v), 0);
const grad = (x, y, h = 1e-4) => [(loss(x + h, y) - loss(x - h, y)) / 2 / h, (loss(x, y + h) - loss(x, y - h)) / 2 / h];
const START = [-0.15, -0.1], R = 1.2, SZ = 420;
const STOPS = [[0, [16, 22, 43]], [0.35, [59, 42, 107]], [0.7, [181, 68, 110]], [1, [255, 192, 99]]];
const ramp = t => { t = clamp(t, 0, 1); const j = STOPS.findIndex(s => s[0] >= t) || 1, [t0, c0] = STOPS[Math.max(0, j - 1)], [t1, c1] = STOPS[j];
  return c0.map((c, k) => c + (c1[k] - c) * (t1 === t0 ? 0 : (t - t0) / (t1 - t0))); };

function simulate(eps, steps) {
  const s = START, [gx, gy] = grad(...s), fg = [s[0] + eps * Math.sign(gx), s[1] + eps * Math.sign(gy)];
  const path = [[...s]], a = 2.5 * eps / steps; let q = [...s];
  for (let k = 0; k < steps; k++) { const [dx, dy] = grad(...q); q = [clamp(q[0] + a * Math.sign(dx), s[0] - eps, s[0] + eps), clamp(q[1] + a * Math.sign(dy), s[1] - eps, s[1] + eps)]; path.push([...q]); }
  return { fg, path, g: [gx, gy] };
}

function mountLandscape(p, cfg) {
  let eps = 0.6, steps = 10, mode = cfg.modes[0];
  const both = cfg.modes.length > 1, cv = vEl('canvas', { width: SZ, height: SZ, className: 'vland' });
  const heat = document.createElement('canvas'); heat.width = heat.height = 110;
  const hx = heat.getContext('2d'), im = hx.createImageData(110, 110);
  for (let r = 0; r < 110; r++) for (let c = 0; c < 110; c++) im.data.set([...ramp(loss((c / 110 * 2 - 1) * R, (1 - r / 110 * 2) * R) / 0.9), 255], (r * 110 + c) * 4);
  hx.putImageData(im, 0, 0);
  const P = ([x, y]) => [(x + R) / (2 * R) * SZ, (R - y) / (2 * R) * SZ];
  const readout = vEl('div', { className: 'vinfo', ariaLive: 'polite' }), cap = vEl('p', { className: 'dim sm' });
  const epsS = vEl('input', { type: 'range', min: 0.1, max: 0.9, step: 0.05, value: eps, ariaLabel: 'Budget eps' }), epsV = vEl('b', { textContent: eps.toFixed(2) });
  const stS = vEl('input', { type: 'range', min: 1, max: 20, step: 1, value: steps, ariaLabel: 'Number of steps' }), stV = vEl('b', { textContent: steps });
  const radios = cfg.modes.map(m => vEl('label', { className: 'vradio' }, vEl('input', { type: 'radio', name: 'vmode', checked: m === mode, onchange: () => { mode = m; draw(); } }), m === 'fgsm' ? ' FGSM (one jump)' : ' PGD (small steps + projection)'));
  p.append(vEl('p', { className: 'dim sm', textContent: 'A toy picture of the model\'s mistake level. Brighter = the model is more wrong. The attacker wants to climb, but may not leave the white box (the budget).' }),
    vEl('div', { className: 'vrow top' }, cv, vEl('div', { className: 'vside' }, ...(both ? radios : []),
      vEl('label', {}, 'Budget eps: ', epsV), epsS, ...(both ? [vEl('label', {}, 'PGD steps: ', stV), stS] : []), readout)), cap);
  function draw() {
    const g = cv.getContext('2d'), { fg, path, g: gr } = simulate(eps, steps), end = path[path.length - 1], s = START;
    g.imageSmoothingEnabled = true; g.drawImage(heat, 0, 0, SZ, SZ);
    const [bx0, by0] = P([s[0] - eps, s[1] + eps]), [bx1, by1] = P([s[0] + eps, s[1] - eps]);
    g.setLineDash([6, 4]); g.strokeStyle = '#fff'; g.lineWidth = 1.5; g.strokeRect(bx0, by0, bx1 - bx0, by1 - by0); g.setLineDash([]);
    const line = (pts, col, w, a) => { g.globalAlpha = a; g.strokeStyle = col; g.fillStyle = col; g.lineWidth = w; g.beginPath(); pts.map(P).forEach(([x, y], k) => k ? g.lineTo(x, y) : g.moveTo(x, y)); g.stroke();
      pts.slice(1).map(P).forEach(([x, y]) => { g.beginPath(); g.arc(x, y, w + 1, 0, 7); g.fill(); }); g.globalAlpha = 1; };
    if (both) line(path, '#ff6b5e', mode === 'pgd' ? 3 : 1.5, mode === 'pgd' ? 1 : 0.35);
    line([s, fg], '#7fd1ff', mode === 'fgsm' ? 3 : 1.5, mode === 'fgsm' ? 1 : 0.35);
    const [sx, sy] = P(s), n = Math.hypot(...gr) || 1; g.strokeStyle = '#fff'; g.lineWidth = 2; g.beginPath(); g.moveTo(sx, sy); g.lineTo(sx + gr[0] / n * 34, sy - gr[1] / n * 34); g.stroke();
    g.fillStyle = '#fff'; g.beginPath(); g.arc(sx, sy, 5, 0, 7); g.fill(); g.font = '12px system-ui'; g.fillText('clean input + gradient arrow', sx + 8, sy + 16);
    const f = ([x, y]) => loss(x, y).toFixed(2);
    readout.replaceChildren(vEl('div', {}, `Mistake level at the clean input: ${f(s)}`), vEl('div', { className: mode === 'fgsm' ? 'sel' : '', textContent: `FGSM jump: ${f(fg)}` }),
      ...(both ? [vEl('div', { className: mode === 'pgd' ? 'sel' : '', textContent: `PGD after ${steps} steps: ${f(end)}` })] : []));
    cap.textContent = mode === 'fgsm' ? 'FGSM reads the gradient once and jumps to the corner of the box that the gradient points toward (the sign of each part). It can overshoot or miss the best spot.'
      : 'PGD takes small steps, re-reads the gradient each time, and is pushed back into the box whenever it steps out (the projection, or "leash"). It can slide along the edge to reach a higher mistake level than one jump.';
  }
  epsS.oninput = () => { eps = +epsS.value; epsV.textContent = eps.toFixed(2); draw(); };
  stS.oninput = () => { steps = +stS.value; stV.textContent = steps; draw(); };
  draw();
}
