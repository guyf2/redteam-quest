TITLES.asr_ci = 'How sure can you be?';
MOUNT.asr_ci = function (p) {
  let n = 10, k = 0;
  const z = 1.96, wilson = (k, n) => { const ph = k / n, d = 1 + z * z / n, c = (ph + z * z / (2 * n)) / d, h = z * Math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d; return [Math.max(0, c - h), Math.min(1, c + h)]; };
  const wald = (k, n) => { const ph = k / n, m = z * Math.sqrt(ph * (1 - ph) / n); return [ph - m, ph + m]; };
  const out = vEl('div'), nV = vEl('b'), kV = vEl('b');
  const nS = vEl('input', { type: 'range', min: 1, max: 200, step: 1, value: n, ariaLabel: 'Number of trials' }), kS = vEl('input', { type: 'range', min: 0, max: n, step: 1, value: k, ariaLabel: 'Successful attacks' });
  p.append(vEl('p', { className: 'dim sm', textContent: 'You ran an attack n times and it worked k times. How well do you know the true success rate? Compare the textbook interval (red, often wrong) with the Wilson interval (gold).' }),
    vEl('div', { className: 'vrow ctl' }, vEl('label', {}, 'Trials n: ', nV), nS, vEl('label', {}, 'Successes k: ', kV), kS), out);
  function draw() {
    kS.max = n; if (k > n) k = n; kS.value = k; nV.textContent = n; kV.textContent = k;
    const W = 520, H = 110, X = v => 30 + v * 460, s = vSvg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'vchart', role: 'img', 'aria-label': 'Confidence intervals for the attack success rate' });
    s.append(vSvg('line', { x1: X(0), x2: X(1), y1: 85, y2: 85, stroke: 'var(--line)', 'stroke-width': 2 }));
    [0, .25, .5, .75, 1].forEach(v => s.append(vSvg('text', { x: X(v), y: 102, 'text-anchor': 'middle', class: 'tick' }, Math.round(v * 100) + '%'), vSvg('line', { x1: X(v), x2: X(v), y1: 80, y2: 90, stroke: 'var(--dim)' })));
    const row = (iv, y, col, label) => { const lo = Math.max(-0.05, iv[0]), hi = Math.min(1.05, iv[1]); s.append(vSvg('rect', { x: X(lo), y, width: Math.max(2, X(hi) - X(lo)), height: 10, rx: 4, fill: col }), vSvg('text', { x: 30, y: y - 3, fill: col, style: 'font-size:10px' }, `${label}: ${(iv[0] * 100).toFixed(0)}% to ${(iv[1] * 100).toFixed(0)}%`)); };
    row(wald(k, n), 22, 'var(--bad)', 'Textbook (Wald)'); row(wilson(k, n), 52, 'var(--gold)', 'Wilson');
    s.append(vSvg('circle', { cx: X(k / n), cy: 85, r: 5, fill: 'var(--fg)' }));
    const [lo, hi] = wilson(k, n);
    out.replaceChildren(s, vEl('p', { className: 'vinfo', textContent: `Observed ${k}/${n} = ${(100 * k / n).toFixed(0)}%. The true rate could plausibly be anywhere from ${(lo * 100).toFixed(0)}% to ${(hi * 100).toFixed(0)}%.` + (k === 0 || k === n ? ' Notice the red interval collapses to a point: it claims certainty it does not have.' : '') }));
  }
  nS.oninput = () => { n = +nS.value; draw(); }; kS.oninput = () => { k = +kS.value; draw(); };
  draw();
};
