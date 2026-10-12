TITLES.risk_matrix = 'Risk matrix';
MOUNT.risk_matrix = function (p) {
  let L = 4, I = 5;
  const out = vEl('div'), ls = vEl('input', { type: 'range', min: 1, max: 5, step: 1, value: L, ariaLabel: 'Likelihood' }), is = vEl('input', { type: 'range', min: 1, max: 5, step: 1, value: I, ariaLabel: 'Impact' });
  const lv = vEl('b'), iv = vEl('b');
  const EX = [[2, 2, 'Error page shows framework version'], [3, 1, 'System prompt contains only public phone number'], [2, 4, 'Fine-tune membership leak (weak)'], [4, 5, 'Outsider email steers the refund API'], [5, 3, 'Unlimited long requests cost money'], [3, 3, 'Partner article steers replies']];
  p.append(vEl('p', { className: 'dim sm', textContent: 'Risk = likelihood x impact. Move the sliders to place a threat, and see the example threats (from a different system) on the grid.' }),
    vEl('div', { className: 'vrow ctl' }, vEl('label', {}, 'Likelihood: ', lv), ls, vEl('label', {}, 'Impact: ', iv), is), out);
  const band = r => r >= 16 ? ['Critical', '#ff5d5d'] : r >= 10 ? ['High', '#ff9d5d'] : r >= 5 ? ['Medium', '#ffc063'] : ['Low', '#45c46e'];
  function draw() {
    lv.textContent = L; iv.textContent = I;
    const W = 520, H = 320, c = 52, X0 = 60, Y0 = 10, s = vSvg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'vchart', role: 'img', 'aria-label': 'Likelihood by impact grid' });
    for (let l = 1; l <= 5; l++) for (let i = 1; i <= 5; i++) { const b = band(l * i); s.append(vSvg('rect', { x: X0 + (l - 1) * c, y: Y0 + (5 - i) * c, width: c - 2, height: c - 2, rx: 4, fill: b[1], opacity: (l === L && i === I) ? 1 : 0.28, stroke: (l === L && i === I) ? '#fff' : 'none', 'stroke-width': 2 })); }
    EX.forEach(([l, i, t], k) => s.append(vSvg('circle', { cx: X0 + (l - 1) * c + c / 2 - 1 + (k % 2 ? 8 : -8), cy: Y0 + (5 - i) * c + c / 2 - 1 + (k % 3 - 1) * 8, r: 6, fill: '#fff' }, vSvg('title', {}, `${t}: likelihood ${l}, impact ${i}`))));
    for (let k = 1; k <= 5; k++) { s.append(vSvg('text', { x: X0 + (k - 1) * c + c / 2, y: H - 22, 'text-anchor': 'middle', class: 'tick' }, k), vSvg('text', { x: X0 - 8, y: Y0 + (5 - k) * c + c / 2 + 4, 'text-anchor': 'end', class: 'tick' }, k)); }
    s.append(vSvg('text', { x: X0 + 2.5 * c, y: H - 4, 'text-anchor': 'middle', class: 'tick' }, 'likelihood'), vSvg('text', { x: 14, y: Y0 + 2.5 * c, class: 'tick', transform: `rotate(-90 14 ${Y0 + 2.5 * c})`, 'text-anchor': 'middle' }, 'impact'));
    const b = band(L * I);
    out.replaceChildren(s, vEl('div', { className: 'vbadge', style: `background:${b[1]};color:#111`, textContent: `Likelihood ${L} x impact ${I} = ${L * I}: ${b[0]}` }),
      vEl('ul', { className: 'dim sm', style: 'margin:6px 0 0 18px;padding:0' }, ...EX.map(([l, i, t]) => vEl('li', { textContent: `${t}: ${l} x ${i} = ${l * i} (${band(l * i)[0]})` }))));
  }
  ls.oninput = () => { L = +ls.value; draw(); }; is.oninput = () => { I = +is.value; draw(); }; draw();
};
