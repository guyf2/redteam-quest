TITLES.policy_matrix = 'Four policies compared';
MOUNT.policy_matrix = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/policy_matrix`).then(d => p.replaceChildren(
    vEl('p', { className: 'dim sm', textContent: `Four simple policies on the same ${d.legit} legitimate and ${d.attacks} injected calls. You want both bars tall: still useful, still safe.` }),
    barChart({ groups: Object.entries(d.policies).map(([k, v]) => ({ label: k, bars: [{ name: 'legitimate calls allowed', color: 'var(--ok)', v: v.allowed }, { name: 'injected calls blocked', color: 'var(--hot)', v: v.blocked }] })), yLabel: '%' }),
    vEl('p', { className: 'dim sm', textContent: 'Blanket rules trade one number for the other. Tying each privileged call to what the user actually said gets both.' })));
};
