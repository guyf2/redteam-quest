TITLES.patch = 'Patch lab';
MOUNT.patch = function (p, cfg) {
  let size = 14;
  const info = vEl('div', { className: 'vinfo', ariaLive: 'polite' }), out = vEl('div'), btns = [8, 10, 12, 14, 16].map(s => vEl('button', { className: 'chip', textContent: s + 'x' + s, onclick: () => { size = s; mark(); update(); } }));
  const mark = () => btns.forEach((b, i) => b.classList.toggle('on', [8, 10, 12, 14, 16][i] === size));
  p.append(vEl('p', { className: 'dim sm', textContent: 'A real learned sticker (optimised to make every digit read as an 8), pasted at random spots. Try different sizes: a bigger sticker is a bigger budget.' }),
    vEl('div', { className: 'chips' }, vEl('span', { className: 'dim sm', textContent: 'Sticker size: ' }), ...btns), out, info);
  mark();
  async function update() {
    loading(out);
    const d = await vGet(`/api/level/${cfg.n}/viz/patch?size=${size}`); if (d.size !== size) return;
    const pc = vEl('canvas', { width: d.size, height: d.size, className: 'vcanvas' }), g = pc.getContext('2d'), im = g.createImageData(d.size, d.size);
    d.patch.forEach((v, k) => im.data.set([v * 255, v * 255, v * 255, 255], k * 4)); g.putImageData(im, 0, 0);
    const row = vEl('div', { className: 'vrow' }, vEl('figure', { className: 'vfig' }, pc, vEl('figcaption', { textContent: 'the sticker' })));
    d.examples.forEach(e => { const a = vEl('canvas', { width: 28, height: 28, className: 'vcanvas' }), b = vEl('canvas', { width: 28, height: 28, className: 'vcanvas' }); paint(a, e.clean); paint(b, e.patched);
      row.append(vEl('figure', { className: 'vfig' }, a, vEl('figcaption', { textContent: `clean: ${e.label}` })), vEl('figure', { className: 'vfig' }, b, vEl('figcaption', { textContent: `with sticker: ${e.pred}` }))); });
    out.replaceChildren(row);
    info.replaceChildren(vEl('div', { textContent: `Success at random positions on 200 unseen digits: ${d.success}%` }),
      vEl('div', { className: 'dim sm', textContent: 'The sticker is trained on 20,000 digits, always pasted at a random position, then tested on digits it never saw.' }));
  }
  update();
};
