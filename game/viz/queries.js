TITLES.queries = 'Success vs. queries';
MOUNT.queries = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/queries`).then(d => p.replaceChildren(
    vEl('p', { className: 'dim sm', textContent: 'A simple query-only attack (change one pixel, keep it if the model gets less sure) against random noise of the same size. Success needs a few hundred queries per image.' }),
    lineChart({ x: d.queries, series: [{ name: 'Query-only search', color: 'var(--hot)', y: d.simba }, { name: 'Random +/- eps noise', color: 'var(--dim)', y: d.random }], xLabel: 'queries per image', marker: 1000, markerLabel: 'level budget' })));
};
