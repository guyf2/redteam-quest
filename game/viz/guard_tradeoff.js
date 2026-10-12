TITLES.guard_tradeoff = 'Catch vs. annoy';
MOUNT.guard_tradeoff = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/guard_tradeoff`).then(d => p.replaceChildren(
    vEl('p', { className: 'dim sm', textContent: `Three simple guards on the same ${d.attacks} attacks and ${d.benign} ordinary conversations. A good guard has tall gold bars and short red ones.` }),
    barChart({ groups: Object.entries(d.guards).map(([k, v]) => ({ label: k, bars: [{ name: 'attacks blocked', color: 'var(--gold)', v: v.recall }, { name: 'ordinary requests blocked by mistake', color: 'var(--bad)', v: v.false }] })), yLabel: '%' }),
    vEl('p', { className: 'dim sm', textContent: 'The keyword list annoys real users. The output check catches every leak but is blind to injection attempts that did not leak. Layering them covers both.' })));
};
