TITLES.pipeline = 'Attack vs. pipeline';
MOUNT.pipeline = function (p, cfg) {
  let eps = 16, timer, seq = 0;
  const out = vEl('div'), epsV = vEl('b', { textContent: eps + '/255' });
  const slider = vEl('input', { type: 'range', min: 8, max: 24, step: 4, value: eps, ariaLabel: 'Budget eps over 255' });
  p.append(vEl('p', { className: 'dim sm', textContent: 'The same attack against CLIP with and without Expectation over Transformation (EOT), measured on the raw image and after a shrink + JPEG pipeline. Drag eps (the first run per value takes a few seconds).' }),
    vEl('div', { className: 'vrow ctl' }, vEl('label', {}, 'Budget eps: ', epsV), slider), out);
  async function update() {
    const my = ++seq; loading(out);
    const d = await vGet(`/api/level/${cfg.n}/viz/pipeline?eps=${eps}`); if (my !== seq) return;
    out.replaceChildren(barChart({ groups: Object.entries(d).map(([k, v]) => ({ label: k, bars: [{ name: 'fools CLIP on the raw image', color: 'var(--gold)', v: v.raw }, { name: 'still fools it after the pipeline', color: 'var(--hot)', v: v.pipeline }] })), yLabel: '%' }),
      vEl('p', { className: 'dim sm', textContent: 'Both fool the raw model. Only the one trained through random transformations survives the pipeline. A bigger budget buys more robustness at the cost of visibility.' }));
  }
  slider.oninput = () => { eps = +slider.value; epsV.textContent = eps + '/255'; clearTimeout(timer); timer = setTimeout(update, 300); };
  update();
};
