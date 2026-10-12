TITLES.severity_lab = 'Severity lab';
MOUNT.severity_lab = function (p) {
  const F = [['Impact if it works', ['nothing', 'minor / embarrassing', 'limited loss', 'serious loss', 'money or private data'], 3],
    ['How hard to exploit', ['needs deep access', 'needs an account', 'needs the victim to act', 'anyone can do it', 'anyone, automatically'], 3],
    ['Repeats / scale', ['one time', 'a few victims', 'many victims', 'repeats until stopped', 'everyone, nobody notices'], 2],
    ['Would anyone notice?', ['alarm + human approval', 'logged and reviewed', 'logged only', 'no logging', 'looks normal'], 2]];
  const v = F.map(f => f[2]), out = vEl('div'), rows = F.map((f, i) => { const val = vEl('b'), sl = vEl('input', { type: 'range', min: 0, max: 4, step: 1, value: f[2], ariaLabel: f[0] }); sl.oninput = () => { v[i] = +sl.value; draw(); }; return { val, el: vEl('div', { className: 'vrow ctl' }, vEl('label', { style: 'width:150px' }, f[0] + ': '), sl, val) }; });
  p.append(vEl('p', { className: 'dim sm', textContent: 'Severity comes from a few factors, not from how clever the attack was. Set the factors for a finding and see how a reviewer would rate it.' }), ...rows.map(r => r.el), out);
  function draw() {
    rows.forEach((r, i) => r.val.textContent = F[i][1][v[i]]);
    const score = v[0] * 2 + v[1] + v[2] + v[3] * 0.5, max = 4 * 2 + 4 + 4 + 2, pct = score / max;
    const band = v[0] <= 0 ? 'info' : pct > 0.78 && v[0] >= 4 ? 'critical' : pct > 0.6 ? 'high' : pct > 0.4 ? 'medium' : pct > 0.2 ? 'low' : 'info';
    const col = { info: '#8c97ab', low: '#45c46e', medium: '#ffc063', high: '#ff9d5d', critical: '#ff5d5d' }[band];
    out.replaceChildren(vEl('div', { className: 'vbadge', style: `background:${col};color:#111;font-size:15px`, textContent: `Suggested rating: ${band.toUpperCase()}` }),
      vEl('p', { className: 'dim sm', textContent: v[0] === 0 ? 'No impact at all means it is not a finding: write it as an informational note, or leave it out.' : 'Impact counts double. Critical needs serious impact AND little standing in the attacker\'s way AND no safety net. A clever exploit with a tiny impact stays low.' }));
  }
  draw();
};
