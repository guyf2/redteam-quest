TITLES.at_curve = 'Robustness curves';
MOUNT.at_curve = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/at_curve`).then(d => p.replaceChildren(
    vEl('p', { className: 'dim sm', textContent: 'Accuracy as the attack budget grows (500 test digits). Three models trained differently, attacked with PGD, plus the FGSM-trained model against the weak single-step test. Training takes a few seconds the first time.' }),
    lineChart({ x: d.eps, series: [{ name: 'standard training (PGD attack)', color: 'var(--dim)', y: d.standard }, { name: 'PGD adversarial training (PGD attack)', color: 'var(--ok)', y: d.pgd_at },
      { name: 'FGSM-only training (PGD attack)', color: 'var(--bad)', y: d.fgsm_at_pgd }, { name: 'FGSM-only training (weak FGSM test)', color: 'var(--gold)', y: d.fgsm_at_fgsm }], xLabel: 'attack budget eps', marker: 0.2, markerLabel: 'level budget' }),
    vEl('p', { className: 'dim sm', textContent: 'Gold vs red is the trap: the FGSM-trained model looks robust to the weak test and collapses under a strong one. Only PGD adversarial training (green) holds.' })));
};
