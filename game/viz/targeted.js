TITLES.targeted = 'Targeted lab'; TITLES.stepcurve = 'Steps vs. success';
MOUNT.targeted = function (p, cfg) {
  let i = Math.floor(Math.random() * 500), t = 3, eps = 0.3, steps = 20, timer;
  const cs = [0, 1].map(() => vEl('canvas', { width: 28, height: 28, className: 'vcanvas' }));
  const figs = ['Original', 'Attacked image'].map((l, k) => vEl('figure', { className: 'vfig' }, cs[k], vEl('figcaption', { textContent: l })));
  const bars = vEl('div', { className: 'vbars' }), info = vEl('div', { className: 'vinfo', ariaLive: 'polite' });
  const tbtn = [...Array(10).keys()].map(k => vEl('button', { className: 'chip', textContent: k, onclick: () => { t = k; mark(); update(); } }));
  const mark = () => tbtn.forEach((b, k) => b.classList.toggle('on', k === t));
  const mk = (min, max, step, val, fn) => { const s = vEl('input', { type: 'range', min, max, step, value: val }); s.oninput = () => { fn(+s.value); clearTimeout(timer); timer = setTimeout(update, 120); }; return s; };
  const stepsV = vEl('b', { textContent: steps }), epsV = vEl('b', { textContent: eps.toFixed(2) });
  p.append(vEl('p', { className: 'dim sm', textContent: 'Pick the digit you WANT the model to see, then change the number of attack steps. One step rarely gets there; many small steps do.' }),
    vEl('div', { className: 'vrow' }, ...figs), vEl('div', { className: 'chips' }, vEl('span', { className: 'dim sm', textContent: 'Wanted digit: ' }), ...tbtn),
    vEl('div', { className: 'vrow ctl' }, vEl('label', {}, 'Steps: ', stepsV), mk(1, 40, 1, steps, v => { steps = v; stepsV.textContent = v; }),
      vEl('label', {}, 'Budget eps: ', epsV), mk(0.1, 0.4, 0.01, eps, v => { eps = v; epsV.textContent = v.toFixed(2); }),
      vEl('button', { className: 'ghost sm', textContent: 'Another digit', onclick: () => { i = Math.floor(Math.random() * 500); update(); } })), bars, info);
  mark();
  async function update() {
    const d = await vGet(`/api/level/${cfg.n}/viz/targeted?i=${i}&t=${t}&eps=${eps}&steps=${steps}`);
    paint(cs[0], d.x); paint(cs[1], d.adv);
    const pa = argmax(d.pa);
    bars.replaceChildren(...d.pa.map((c, k) => vEl('div', { className: 'vcol' + (k === t ? ' true' : '') }, vEl('div', { className: 'vpair' }, vEl('i', { className: 'a', style: `height:${c * 70}px`, title: `${(c * 100).toFixed(0)}%` })), vEl('span', { textContent: k }))));
    const hit = pa === t;
    info.replaceChildren(vEl('div', { textContent: `True digit ${d.label}. Wanted ${t}. The model now says ${pa} (${(d.pa[pa] * 100).toFixed(0)}% sure).` }),
      vEl('div', { className: 'vbadge ' + (hit ? 'ok' : 'bad'), textContent: hit ? 'Hit: the model outputs the digit you chose.' : 'Miss: try more steps or a bigger eps.' }),
      vEl('div', { className: 'dim sm', textContent: 'The outlined column is the digit you wanted.' }));
  }
  update();
};
MOUNT.stepcurve = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/steps`).then(d => p.replaceChildren(vEl('p', { className: 'dim sm', textContent: 'How often the attack reaches the chosen digit (eps 0.3, 300 digits). One big step is not enough; iterating is.' }),
    lineChart({ x: d.steps, series: [{ name: 'Targeted success', color: 'var(--gold)', y: d.success }], xLabel: 'number of attack steps' })));
};
