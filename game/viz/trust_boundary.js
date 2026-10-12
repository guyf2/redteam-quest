TITLES.trust_boundary = 'Where it goes wrong';
MOUNT.trust_boundary = function (p) {
  let attack = false;
  const out = vEl('div'), btn = vEl('button', { className: 'ghost sm', textContent: 'Show the attack path', onclick: () => { attack = !attack; btn.textContent = attack ? 'Hide the attack path' : 'Show the attack path'; draw(); } });
  p.append(vEl('p', { className: 'dim sm', textContent: 'The model receives ONE stream of text. Trusted instructions and untrusted data are mixed together before it reads a single word.' }), btn, out);
  function draw() {
    const W = 520, H = 250, s = vSvg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'vchart', role: 'img', 'aria-label': 'Data flow of an email assistant' });
    const box = (x, y, w, h, t1, t2, col) => s.append(vSvg('rect', { x, y, width: w, height: h, rx: 8, fill: 'var(--card2)', stroke: col, 'stroke-width': 2 }),
      vSvg('text', { x: x + w / 2, y: y + h / 2 - 2, 'text-anchor': 'middle', fill: 'var(--fg)', style: 'font-size:12px;font-weight:600' }, t1), vSvg('text', { x: x + w / 2, y: y + h / 2 + 13, 'text-anchor': 'middle', fill: 'var(--dim)', style: 'font-size:10px' }, t2));
    const arrow = (x1, y1, x2, y2, col, label) => { s.append(vSvg('line', { x1, y1, x2, y2, stroke: col, 'stroke-width': 2.5, 'marker-end': 'url(#ah' + (col === 'var(--bad)' ? 'r' : 'g') + ')' }));
      if (label) s.append(vSvg('text', { x: (x1 + x2) / 2 + 4, y: (y1 + y2) / 2 - 5, fill: col, style: 'font-size:10px' }, label)); };
    s.append(vSvg('defs', {}, ...[['r', '#ff6262'], ['g', '#8c97ab']].map(([id, c]) => vSvg('marker', { id: 'ah' + id, markerWidth: 8, markerHeight: 8, refX: 6, refY: 4, orient: 'auto' }, vSvg('path', { d: 'M0,0 L8,4 L0,8 z', fill: c })))));
    box(10, 20, 130, 46, 'Dana (the user)', 'trusted', 'var(--ok)');
    box(10, 100, 130, 46, 'CEO email', 'trusted data, holds the secret', 'var(--ok)');
    box(10, 180, 130, 46, 'Attacker email', 'UNTRUSTED text', 'var(--bad)');
    box(200, 85, 120, 76, 'MailBot (model)', 'one stream of text', 'var(--gold)');
    box(380, 85, 130, 76, 'send_email tool', 'real authority', 'var(--blue)');
    const g = 'var(--dim)', r = 'var(--bad)';
    arrow(140, 43, 205, 105, g, '"summarize my email"'); arrow(140, 123, 200, 123, g, ''); arrow(140, 203, 205, 145, attack ? r : g, attack ? 'hidden orders' : '');
    arrow(320, 123, 380, 123, attack ? r : g, attack ? 'secret out' : '');
    if (attack) s.append(vSvg('text', { x: 260, y: 240, 'text-anchor': 'middle', fill: 'var(--bad)', style: 'font-size:11px' }, 'Untrusted text + private data + a send channel = exfiltration'));
    out.replaceChildren(s, vEl('p', { className: 'dim sm', textContent: attack ? 'The attacker never touched the system. They only wrote an email. The bot read the secret and used its own authority to send it out.' : 'Normally: the user asks, the bot reads the inbox, and replies. All the arrows look harmless.' }));
  }
  draw();
};
