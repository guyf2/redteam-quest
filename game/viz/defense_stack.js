TITLES.defense_stack = 'Defense layers'; TITLES.attack_matrix = 'What beats what';
// A layered-defense diagram: pick a rung to see which layers sit between you and the secret.
MOUNT.defense_stack = function (p) {
  const RUNGS = ['Unguarded', 'Hardened prompt', 'Output filter', 'Input + output filters', 'AI judge'];
  const LAYERS = [
    { name: 'Input filter', note: 'blocks banned words in YOUR message', on: [0, 0, 0, 1, 1] },
    { name: 'Model + hardened prompt', note: 'told never to reveal the secret', on: [0, 1, 1, 1, 1] },
    { name: 'Output filter (code)', note: 'scans the reply for the secret', on: [0, 0, 1, 1, 1] },
    { name: 'AI judge', note: 'a second model reads the reply', on: [0, 0, 0, 0, 1] }];
  let rung = 3;
  const out = vEl('div'), btns = RUNGS.map((r, i) => vEl('button', { className: 'chip', textContent: `${i + 1}. ${r}`, onclick: () => { rung = i; draw(); } }));
  p.append(vEl('p', { className: 'dim sm', textContent: 'Every rung wraps the model in more checks. Pick a rung to see which layers your message and the reply must pass through.' }), vEl('div', { className: 'chips' }, ...btns), out);
  function draw() {
    btns.forEach((b, i) => b.classList.toggle('on', i === rung));
    const W = 520, H = 120, boxW = 108, gap = 18, s = vSvg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'vchart', role: 'img', 'aria-label': 'Defense layers between the user and the secret' });
    const nodes = [{ name: 'You', note: 'the attacker', on: 1, fixed: 1 }, ...LAYERS.map(l => ({ ...l, on: l.on[rung] })), { name: 'Reply', note: 'what you see', on: 1, fixed: 1 }];
    const bw = (W - gap * (nodes.length - 1)) / nodes.length;
    nodes.forEach((n, i) => {
      const x = i * (bw + gap), col = n.fixed ? 'var(--blue)' : n.on ? 'var(--bad)' : 'var(--line)';
      s.append(vSvg('rect', { x, y: 20, width: bw, height: 54, rx: 8, fill: 'var(--card2)', stroke: col, 'stroke-width': n.on ? 2 : 1, 'stroke-dasharray': n.on ? '' : '4 3' }),
        vSvg('text', { x: x + bw / 2, y: 42, 'text-anchor': 'middle', fill: n.on ? 'var(--fg)' : 'var(--dim)', style: 'font-size:11px;font-weight:600' }, n.name),
        vSvg('text', { x: x + bw / 2, y: 60, 'text-anchor': 'middle', fill: 'var(--dim)', style: 'font-size:9px' }, n.fixed ? n.note : n.on ? 'ACTIVE' : 'off'));
      if (i) s.append(vSvg('line', { x1: x - gap + 2, x2: x - 2, y1: 47, y2: 47, stroke: 'var(--dim)', 'stroke-width': 1.5 }));
    });
    const lines = LAYERS.filter(l => l.on[rung]).map(l => `${l.name}: ${l.note}.`);
    out.replaceChildren(s, vEl('p', { className: 'dim sm', textContent: lines.length ? lines.join(' ') : 'No layers at all. Whatever the model knows, it will say.' }),
      vEl('p', { className: 'dim sm', textContent: 'Each layer catches a family of attacks and misses others. The skill is picking the attack that the active layers do not look for.' }));
  }
  draw();
};
MOUNT.attack_matrix = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/attack_matrix`).then(d => {
    const head = vEl('tr', {}, vEl('th', { textContent: 'Attack' }), ...d.rungs.map((r, i) => vEl('th', { textContent: `${i + 1}. ${r}` })));
    const rows = Object.entries(d.techniques).map(([name, vals]) => vEl('tr', {}, vEl('td', { textContent: name }), ...vals.map(v => vEl('td', { textContent: v + '%', style: `background:rgba(255,107,94,${v / 130});text-align:center`, title: `${v}% of ${d.n} tries got some part of the secret past every defense` }))));
    p.replaceChildren(vEl('p', { className: 'dim sm', textContent: `Measured on this machine (${d.date}, ${d.n} tries per cell, models ${d.models['rungs 1-3']} and ${d.models['rungs 4-5']}): how often each attack got at least part of the secret through every defense. Cells are noisy; models are random.` }),
      vEl('table', { className: 'vtable' }, vEl('thead', {}, head), vEl('tbody', {}, ...rows)));
  });
};
