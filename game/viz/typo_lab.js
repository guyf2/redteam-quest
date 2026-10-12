TITLES.typo_lab = 'Typography lab'; TITLES.typo_curve = 'How little text is enough';
MOUNT.typo_lab = function (p, cfg) {
  let i = Math.floor(Math.random() * 60), t = 5, size = 18, timer, seq = 0;
  const img = vEl('img', { className: 'vcanvas', style: 'width:224px;height:224px;image-rendering:auto' }), bars = vEl('div', { className: 'vbars', style: 'height:120px' }), info = vEl('div', { className: 'vinfo', ariaLive: 'polite' });
  const NAMES = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck'];
  const tb = NAMES.map((n, k) => vEl('button', { className: 'chip', textContent: n, onclick: () => { t = k; mark(); update(); } }));
  const mark = () => tb.forEach((b, k) => b.classList.toggle('on', k === t));
  const sV = vEl('b', { textContent: size }), slider = vEl('input', { type: 'range', min: 0, max: 36, step: 2, value: size, ariaLabel: 'Text size' });
  p.append(vEl('p', { className: 'dim sm', textContent: 'A real CLIP model classifies this photo. Choose what to write on it and how big. Size 0 means no label.' }),
    vEl('div', { className: 'chips' }, vEl('span', { className: 'dim sm', textContent: 'Write: ' }), ...tb),
    vEl('div', { className: 'vrow ctl' }, vEl('label', {}, 'Text size: ', sV), slider, vEl('button', { className: 'ghost sm', textContent: 'Another photo', onclick: () => { i = Math.floor(Math.random() * 60); update(); } })),
    vEl('div', { className: 'vrow' }, img, vEl('div', { style: 'flex:1;min-width:240px' }, bars, info)));
  mark();
  async function update() {
    const my = ++seq;
    let d;
    try { d = await vGet(`/api/level/${cfg.n}/viz/typo?i=${i}&t=${t}&size=${size}`); }
    catch (e) { if (my === seq) info.replaceChildren(vEl('div', { className: 'vbadge bad', textContent: 'Could not load the photo (server error). Try "Another photo" or reload the page.' })); return; }
    if (my !== seq) return;
    if (d.error) { info.replaceChildren(vEl('div', { className: 'vbadge bad', textContent: 'Server error: ' + d.error })); return; }
    img.src = 'data:image/png;base64,' + d.png;
    const top = argmax(d.probs);
    bars.replaceChildren(...d.probs.map((c, k) => vEl('div', { className: 'vcol' + (k === top ? ' true' : '') }, vEl('div', { className: 'vpair', style: 'height:100px' }, vEl('i', { className: 'a', style: `height:${c * 100}px`, title: `${d.names[k]}: ${(c * 100).toFixed(0)}%` })), vEl('span', { textContent: d.names[k].slice(0, 3) }))));
    const fooled = size > 0 && d.names[top] === NAMES[t] && NAMES[t] !== d.label;
    info.replaceChildren(vEl('div', { textContent: `The photo really shows a ${d.label}. CLIP says: ${d.names[top]} (${(d.probs[top] * 100).toFixed(0)}%). Pixels changed: ${d.changed}%.` }),
      vEl('div', { className: 'vbadge ' + (fooled ? 'bad' : 'ok'), textContent: fooled ? 'Fooled: the model believes the label, not the photo.' : size === 0 ? 'No label yet.' : 'Not fooled (yet). Try bigger text, or a different target.' }));
  }
  slider.oninput = () => { size = +slider.value; sV.textContent = size; clearTimeout(timer); timer = setTimeout(update, 150); };
  update();
};
MOUNT.typo_curve = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/typo_curve`).then(d => p.replaceChildren(
    vEl('p', { className: 'dim sm', textContent: 'Write a wrong class name on 60 photos at different text sizes. Gold: how often CLIP is fooled. Grey: share of pixels the label changes.' }),
    lineChart({ x: d.sizes, series: [{ name: 'CLIP fooled', color: 'var(--gold)', y: d.hit }, { name: 'pixels changed', color: 'var(--dim)', y: d.changed }], xLabel: 'text size (px)', marker: 18, markerLabel: 'size 18' })));
};
