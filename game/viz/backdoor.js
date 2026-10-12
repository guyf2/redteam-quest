TITLES.backdoor = 'Backdoor lab';
MOUNT.backdoor = function (p, cfg) {
  let size = 3;
  const out = vEl('div'), btns = [2, 3, 4].map(s => vEl('button', { className: 'chip', textContent: `${s}x${s} trigger (${s * s} px)`, onclick: () => { size = s; mark(); update(); } }));
  const mark = () => btns.forEach((b, i) => b.classList.toggle('on', [2, 3, 4][i] === size));
  p.append(vEl('p', { className: 'dim sm', textContent: 'Real models, trained fresh each time on 60,000 digits plus a few poisoned ones (a bright square in the corner, relabelled as 7). Pick the trigger size.' }), vEl('div', { className: 'chips' }, ...btns), out); mark();
  async function update() {
    loading(out); const d = await vGet(`/api/level/${cfg.n}/viz/backdoor?size=${size}`); if (d.size !== size) return;
    const row = vEl('div', { className: 'vrow' });
    d.demo.forEach(e => { const a = vEl('canvas', { width: 28, height: 28, className: 'vcanvas' }), b = vEl('canvas', { width: 28, height: 28, className: 'vcanvas' }); paint(a, e.clean); paint(b, e.trig);
      row.append(vEl('figure', { className: 'vfig' }, a, vEl('figcaption', { textContent: `clean ${e.label}: model says ${e.pred_clean}` })), vEl('figure', { className: 'vfig' }, b, vEl('figcaption', { textContent: `with trigger: model says ${e.pred}` }))); });
    out.replaceChildren(lineChart({ x: d.counts, series: [{ name: 'triggered digits read as 7', color: 'var(--hot)', y: d.asr }, { name: 'clean accuracy', color: 'var(--ok)', y: d.clean }], xLabel: 'poisoned images added (out of 60,000)' }),
      vEl('p', { className: 'dim sm', textContent: 'Red: how often the trigger works. Green: accuracy on normal digits, which barely moves, so ordinary testing never notices. Examples below use the model trained with 100 poisoned images.' }), row);
  }
  update();
};
