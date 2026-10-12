TITLES.eval_gap = 'Weak vs. strong evaluation';
MOUNT.eval_gap = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/gap`).then(d => p.replaceChildren(
    vEl('p', { className: 'dim sm', textContent: 'Three models, two evaluations. A single-step attack (what a hurried script does) against the strongest evaluation: many steps, restarts and adaptive attacks, counting only images that survive every one.' }),
    barChart({ groups: d.rows.map(r => ({ label: r.model, bars: [{ name: 'weak evaluation (one FGSM step)', color: 'var(--gold)', v: r.weak }, { name: 'strong, adaptive evaluation (worst case)', color: 'var(--hot)', v: r.strong }] })), yLabel: '%' }),
    vEl('p', { className: 'dim sm', textContent: 'The quantization model shows the danger most clearly: the weak test calls it robust and the strong one finds nothing left. Only the adversarially trained model really is.' })));
};
