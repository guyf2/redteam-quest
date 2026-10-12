TITLES.smooth_lab = 'Vote lab'; TITLES.smooth_curve = 'Certified accuracy';
MOUNT.smooth_lab = function (p, cfg) {
  let i = Math.floor(Math.random() * 200), n = 100, timer, seq = 0;
  const cs = [0, 1, 2, 3].map(() => vEl('canvas', { width: 28, height: 28, className: 'vcanvas' })), figs = ['Original', 'noisy copy 1', 'noisy copy 2', 'noisy copy 3'].map((l, k) => vEl('figure', { className: 'vfig', style: 'width:100px' }, cs[k], vEl('figcaption', { textContent: l })));
  cs.forEach(c => { c.style.width = '100px'; c.style.height = '100px'; });
  const bars = vEl('div', { className: 'vbars' }), info = vEl('div', { className: 'vinfo', ariaLive: 'polite' }), nV = vEl('b', { textContent: n });
  const sl = vEl('input', { type: 'range', min: 10, max: 1000, step: 10, value: n, ariaLabel: 'Number of noisy samples' });
  p.append(vEl('p', { className: 'dim sm', textContent: 'The classifier votes on many noisy copies of one digit. The more samples, the tighter the confidence bound, and the larger the radius you can prove.' }), vEl('div', { className: 'vrow' }, ...figs),
    vEl('div', { className: 'vrow ctl' }, vEl('label', {}, 'Noisy samples n: ', nV), sl, vEl('button', { className: 'ghost sm', textContent: 'Another digit', onclick: () => { i = Math.floor(Math.random() * 200); update(); } })), bars, info);
  async function update() {
    const my = ++seq, d = await vGet(`/api/level/${cfg.n}/viz/smooth?i=${i}&n=${n}`); if (my !== seq) return;
    paint(cs[0], d.clean); d.noisy.forEach((a, k) => paint(cs[k + 1], a));
    const max = Math.max(...d.counts);
    bars.replaceChildren(...d.counts.map((c, k) => vEl('div', { className: 'vcol' + (k === d.top ? ' true' : '') }, vEl('div', { className: 'vpair' }, vEl('i', { className: 'a', style: `height:${c / max * 70}px`, title: `${c} votes` })), vEl('span', { textContent: k }))));
    info.replaceChildren(vEl('div', { textContent: `Top class ${d.top} won ${d.counts[d.top]} of ${d.n} votes (${(d.p_hat * 100).toFixed(1)}%). ` + (d.radius > 0 ? `Certified radius (99.9% confidence): ${d.radius}. No perturbation smaller than that, of ANY kind, can change this answer.` : 'The confidence bound is not above one half: the classifier must abstain.') }),
      vEl('div', { className: 'dim sm', textContent: 'True digit: ' + d.label + '. Try a small n: even a unanimous vote proves little when you only asked a few times.' }));
  }
  sl.oninput = () => { n = +sl.value; nV.textContent = n; clearTimeout(timer); timer = setTimeout(update, 120); };
  update();
};
MOUNT.smooth_curve = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/curve`).then(d => p.replaceChildren(
    vEl('p', { className: 'dim sm', textContent: 'Share of 100 test digits that are correctly classified AND provably robust at each L2 radius (sigma 0.25, 500 samples, 99.9% confidence). It falls as the radius you want to prove grows.' }),
    lineChart({ x: d.radii, series: [{ name: 'certified accuracy', color: 'var(--gold)', y: d.certified }], xLabel: 'certified L2 radius', marker: 0.25, markerLabel: 'level target' })));
};
