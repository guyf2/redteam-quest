TITLES.extraction = 'Cost of a clone';
MOUNT.extraction = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/extraction`).then(d => p.replaceChildren(
    vEl('p', { className: 'dim sm', textContent: 'How faithfully a copy trained on the API\'s answers agrees with the original, as you spend more queries. Three strategies, measured now on the real model.' }),
    lineChart({ x: d.queries, series: [{ name: 'natural digits + probabilities', color: 'var(--gold)', y: d.natural }, { name: 'natural digits + top label only', color: 'var(--hot)', y: d.labels }, { name: 'random noise + probabilities', color: 'var(--dim)', y: d.noise }], xLabel: 'queries sent', marker: d.budget, markerLabel: 'level budget' }),
    vEl('p', { className: 'dim sm', textContent: 'The kind of query matters more than the amount: noise barely teaches anything. Hiding probabilities (top label only) costs the attacker a few points, not the attack.' })));
};
