TITLES.masking = 'Gradient masking';
MOUNT.masking = function (p, cfg) {
  let eps = 0.3, timer, seq = 0;
  const out = vEl('div'), epsV = vEl('b', { textContent: eps.toFixed(2) });
  const slider = vEl('input', { type: 'range', min: 0.1, max: 0.4, step: 0.05, value: eps, ariaLabel: 'Budget eps' });
  p.append(vEl('p', { className: 'dim sm', textContent: 'Accuracy of the "robust" model under four attacks. If simple attacks say 98% but smarter ones say ~0%, the robustness was an illusion.' }),
    vEl('div', { className: 'vrow ctl' }, vEl('label', {}, 'Budget eps: ', epsV), slider), out);
  async function update() {
    const my = ++seq; loading(out);
    const d = await vGet(`/api/level/${cfg.n}/viz/masking?eps=${eps}`); if (my !== seq) return;
    const cols = { FGSM: 'var(--gold)', PGD: 'var(--gold)', 'Transfer from base': 'var(--hot)', BPDA: 'var(--hot)' };
    const ga = vEl('canvas', { width: 28, height: 28, className: 'vcanvas' }), gb = vEl('canvas', { width: 28, height: 28, className: 'vcanvas' });
    paint(ga, d.gradDefended); paint(gb, d.gradBase);
    out.replaceChildren(barChart({ groups: Object.entries(d.acc).map(([k, v]) => ({ label: k, bars: [{ name: 'accuracy of the defended model', color: cols[k], v }] })), yLabel: '%' }),
      vEl('div', { className: 'vrow' }, vEl('figure', { className: 'vfig' }, ga, vEl('figcaption', { textContent: `Gradient the attacker sees on the defended model (${d.zeroFrac}% of it is exactly zero)` })),
        vEl('figure', { className: 'vfig' }, gb, vEl('figcaption', { textContent: `Gradient of the plain CNN inside it (${d.zeroFracBase}% zero)` }))),
      vEl('p', { className: 'dim sm', textContent: 'Gold bars: attacks that follow the defended model\'s gradient (which is blank). Red bars: adaptive attacks that route around the blank gradient.' }));
  }
  slider.oninput = () => { eps = +slider.value; epsV.textContent = eps.toFixed(2); clearTimeout(timer); timer = setTimeout(update, 250); };
  update();
};
