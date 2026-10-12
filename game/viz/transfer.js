TITLES.transfer = 'Transfer rates';
MOUNT.transfer = function (p, cfg) {
  let eps = 0.2, timer, seq = 0;
  const out = vEl('div'), epsV = vEl('b', { textContent: eps.toFixed(2) });
  const slider = vEl('input', { type: 'range', min: 0.08, max: 0.3, step: 0.01, value: eps, ariaLabel: 'Budget eps' });
  p.append(vEl('p', { className: 'dim sm', textContent: 'The same adversarial images, tested on the model they were built on (white-box) and on a different, hidden model (transfer). Drag eps.' }),
    vEl('div', { className: 'vrow ctl' }, vEl('label', {}, 'Budget eps: ', epsV), slider), out);
  async function update() {
    const my = ++seq; loading(out);
    const d = await vGet(`/api/level/${cfg.n}/viz/transfer?eps=${eps}`); if (my !== seq) return;
    const names = { fgsm: 'FGSM (1 step)', pgd: 'PGD (20 steps)', mifgsm: 'Momentum FGSM' };
    const note = d.pgd.white > d.fgsm.white && d.pgd.transfer <= d.fgsm.transfer + 1
      ? 'Notice: PGD is the strongest attack on the surrogate, yet it transfers no better than FGSM. It overfit the surrogate.' : 'At larger budgets almost everything transfers.';
    out.replaceChildren(barChart({ groups: ['fgsm', 'pgd', 'mifgsm'].map(k => ({ label: names[k], bars: [{ name: 'fooled surrogate (white-box)', color: 'var(--gold)', v: d[k].white }, { name: 'fooled hidden victim (transfer)', color: 'var(--hot)', v: d[k].transfer }] })), yLabel: '%' }),
      vEl('p', { className: 'dim sm', textContent: note }));
  }
  slider.oninput = () => { eps = +slider.value; epsV.textContent = eps.toFixed(2); clearTimeout(timer); timer = setTimeout(update, 250); };
  update();
};
