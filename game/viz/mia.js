TITLES.mia = 'The leak';
MOUNT.mia = function (p, cfg) {
  loading(p);
  vGet(`/api/level/${cfg.n}/viz/mia`).then(d => {
    p.replaceChildren(); let ei = 3, th = 10; const out = vEl('div'), chips = d.epochs.map((e, i) => vEl('button', { className: 'chip', textContent: `${e} epochs`, onclick: () => { ei = i; mark(); draw(); } }));
    const mark = () => chips.forEach((c, i) => c.classList.toggle('on', i === ei));
    const sl = vEl('input', { type: 'range', min: 1, max: 19, step: 1, value: th, ariaLabel: 'Loss threshold' }); sl.oninput = () => { th = +sl.value; draw(); };
    p.append(vEl('p', { className: 'dim sm', textContent: 'The same CIFAR-10 model, trained for different numbers of epochs on 1,000 images. For each image the bar shows its loss (log scale, left = confident and correct). Members (gold) vs images the model never saw (grey). Slide the threshold: everything left of it is called "member".' }),
      vEl('div', { className: 'chips' }, vEl('span', { className: 'dim sm', textContent: 'Training: ' }), ...chips), vEl('label', {}, 'Loss threshold ', sl), out); mark();
    function draw() {
      const h = d.hist[ei], W = 520, H = 200, m = { l: 36, r: 10, t: 12, b: 34 }, max = Math.max(...h.members, ...h.non), bw = (W - m.l - m.r) / 20, Y = v => H - m.b - v / max * (H - m.t - m.b);
      const s = vSvg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'vchart', role: 'img', 'aria-label': 'Loss histograms of members and non-members' });
      for (let i = 0; i < 20; i++) { const x = m.l + i * bw; s.append(vSvg('rect', { x: x + 1, y: Y(h.non[i]), width: bw / 2 - 1, height: Math.max(0.5, H - m.b - Y(h.non[i])), fill: '#6c7689' }), vSvg('rect', { x: x + bw / 2, y: Y(h.members[i]), width: bw / 2 - 1, height: Math.max(0.5, H - m.b - Y(h.members[i])), fill: 'var(--gold)' })); }
      [0, 5, 10, 15, 20].forEach(i => s.append(vSvg('text', { x: m.l + i * bw, y: H - 18, 'text-anchor': 'middle', class: 'tick' }, (-5 + 0.35 * i).toFixed(1))));
      s.append(vSvg('text', { x: W / 2, y: H - 4, 'text-anchor': 'middle', class: 'tick' }, 'log10(loss): lower = model is more sure of the true class'), vSvg('line', { x1: m.l + th * bw, x2: m.l + th * bw, y1: m.t, y2: H - m.b, class: 'mark' }));
      const sum = a => a.reduce((x, y) => x + y, 0), tpr = sum(h.members.slice(0, th)) / sum(h.members), fpr = sum(h.non.slice(0, th)) / sum(h.non);
      out.replaceChildren(s, vEl('div', { className: 'vinfo', textContent: `Victim: ${d.train_acc[ei]}% accurate on its training images, ${d.test_acc[ei]}% on new ones.  Attack AUC: ${d.auc[ei]}.  At this threshold you catch ${(tpr * 100).toFixed(0)}% of members and wrongly accuse ${(fpr * 100).toFixed(0)}% of non-members.` }),
        vEl('p', { className: 'dim sm', textContent: 'Train longer and the model memorises more: the gap between the two piles widens and so does the privacy leak.' }));
    }
    draw();
  });
};
