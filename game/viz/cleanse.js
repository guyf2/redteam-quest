TITLES.cleanse = 'Trigger forensics';
MOUNT.cleanse = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/cleanse`).then(d => {
    const cols = ['var(--dim)', 'var(--blue)', 'var(--hot)'], names = Object.keys(d.norms);
    const c = vEl('canvas', { width: 28, height: 28, className: 'vcanvas' }); paint(c, d.mask);
    p.replaceChildren(vEl('p', { className: 'dim sm', textContent: 'For every model and every class: how big a patch is needed to force that class on ANY digit? A real, planted backdoor is a shortcut, so one class needs a tiny patch. Measured on three real models now.' }),
      lineChart({ x: d.classes, series: names.map((n, i) => ({ name: n, color: cols[i], y: d.norms[n] })), yLabel: ' px', yMax: Math.ceil(Math.max(...names.flatMap(n => d.norms[n])) / 20) * 20, xLabel: 'target class forced' }),
      vEl('div', { className: 'vrow' }, vEl('figure', { className: 'vfig', style: 'width:140px' }, c, vEl('figcaption', { textContent: `the patch found for class ${d.target} on the backdoored model: it is the trigger` })),
        vEl('p', { className: 'dim sm', style: 'flex:1', textContent: 'The dip is the evidence. The mask lights up exactly where the poisoned images carried their hidden stamp (here, the bottom-right corner). Clean models show no dip: every class costs a similar, large patch.' })));
  });
};
