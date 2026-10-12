TITLES.doc_preview = 'What the model sees'; TITLES.phrasing = 'Which phrasing works';
MOUNT.doc_preview = function (p) {
  const cv = vEl('canvas', { width: 640, height: 340, style: 'width:100%;max-width:520px;border:1px solid var(--line);border-radius:6px;background:#fff' });
  const ta = vEl('textarea', { rows: 3, placeholder: 'Type text to see how it will look at the bottom of the invoice...' });
  p.append(vEl('p', { className: 'dim sm', textContent: 'A vision model receives pixels, not a text field. Whatever you type below is just more ink on the page, indistinguishable from the document itself.' }), ta, vEl('div', { style: 'margin-top:8px' }, cv));
  const wrap = (t, n) => { const out = []; let line = ''; t.split(/\s+/).forEach(w => { if ((line + ' ' + w).trim().length > n) { out.push(line); line = w; } else line = (line + ' ' + w).trim(); }); out.push(line); return out; };
  function draw() {
    const g = cv.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, 640, 340); g.fillStyle = '#000';
    g.font = '28px sans-serif'; g.fillText('ACME Corp - Invoice #4471', 20, 42); g.font = '22px sans-serif';
    ['Widgets x 12      $96.00', 'Shipping          $24.00', 'Total due         $120.00'].forEach((l, i) => g.fillText(l, 20, 88 + i * 26));
    wrap(ta.value.slice(0, 600), 45).forEach((l, i) => g.fillText(l, 20, 200 + i * 26));
  }
  ta.oninput = draw; draw();
};
MOUNT.phrasing = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/phrasing`).then(d => p.replaceChildren(vEl('p', { className: 'dim sm', textContent: `Measured on this machine (${d.model}, ${d.n} tries per cell, ${d.date}). How often an instruction printed in the image made the assistant leak the code. Results are noisy, and the model is random.` }),
    barChart({ groups: d.rows.map(r => ({ label: r[0].replace(/'/g, '').slice(0, 22) + '...', bars: [{ name: 'open assistant', color: 'var(--gold)', v: r[1] }, { name: 'told images are untrusted', color: 'var(--hot)', v: r[2] }] })), yLabel: '%' }),
    vEl('p', { className: 'dim sm', textContent: 'Phrasing that sounds like part of the task beats phrasing that sounds like an attack, and a warning in the system prompt barely changes that.' })));
};
