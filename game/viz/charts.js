// Shared chart helpers for visualization plugins: lineChart and barChart return an <svg>.
function chartFrame(W, H, m, yMax, yLabel, xLabel) {
  const s = vSvg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'vchart', role: 'img' }), Y = v => H - m.b - v / yMax * (H - m.t - m.b);
  for (let k = 0; k <= 4; k++) { const v = yMax * k / 4; s.append(vSvg('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), class: 'grid' }), vSvg('text', { x: m.l - 8, y: Y(v) + 4, 'text-anchor': 'end', class: 'tick' }, Math.round(v) + (yLabel || '')));
  }
  if (xLabel) s.append(vSvg('text', { x: (m.l + W - m.r) / 2, y: H - 6, 'text-anchor': 'middle', class: 'tick' }, xLabel));
  return { s, Y };
}
// series: [{name, color, y: [..]}], x: numeric array shared by all series
function lineChart({ x, series, xLabel, yLabel = '%', yMax = 100, marker, markerLabel }) {
  const W = 520, m = { l: 46, r: 18, t: 14 + series.length * 16, b: 40 }, H = 240 + m.t, { s, Y } = chartFrame(W, H, m, yMax, yLabel, xLabel);
  const lo = Math.min(...x), hi = Math.max(...x), X = v => m.l + (v - lo) / ((hi - lo) || 1) * (W - m.l - m.r);
  x.forEach(v => s.append(vSvg('text', { x: X(v), y: H - m.b + 16, 'text-anchor': 'middle', class: 'tick' }, +v.toFixed(2))));
  if (marker != null) s.append(vSvg('line', { x1: X(marker), x2: X(marker), y1: m.t, y2: H - m.b, class: 'mark' }), vSvg('text', { x: X(marker) + 5, y: m.t + 10, class: 'tick' }, markerLabel || ''));
  series.forEach((sr, idx) => {
    s.append(vSvg('polyline', { points: x.map((v, j) => `${X(v)},${Y(sr.y[j])}`).join(' '), fill: 'none', stroke: sr.color, 'stroke-width': 2.5 }));
    x.forEach((v, j) => s.append(vSvg('circle', { cx: X(v), cy: Y(sr.y[j]), r: 4, fill: sr.color }, vSvg('title', {}, `${sr.name}, ${v}: ${sr.y[j]}${yLabel}`))));
    s.append(vSvg('text', { x: m.l, y: 14 + idx * 16, fill: sr.color, class: 'legend' }, '\u25A0 ' + sr.name));
  });
  return s;
}
// groups: [{label, bars: [{name, color, v}]}]
function barChart({ groups, yLabel = '%', yMax = 100, xLabel }) {
  const names = [...new Map(groups.flatMap(g => g.bars).map(b => [b.name, b.color]))];
  const W = 520, m = { l: 46, r: 18, t: 14 + names.length * 16, b: 52 }, H = 260 + m.t, { s, Y } = chartFrame(W, H, m, yMax, yLabel, xLabel), gw = (W - m.l - m.r) / groups.length;
  names.forEach(([n, c], k) => s.append(vSvg('text', { x: m.l, y: 14 + k * 16, fill: c, class: 'legend' }, '\u25A0 ' + n)));
  groups.forEach((g, i) => {
    const bw = Math.min(46, gw / (g.bars.length + 1));
    g.bars.forEach((b, j) => {
      const x0 = m.l + i * gw + (gw - bw * g.bars.length) / 2 + j * bw;
      s.append(vSvg('rect', { x: x0 + 2, y: Y(b.v), width: bw - 4, height: Math.max(1, Y(0) - Y(b.v)), fill: b.color, rx: 3 }, vSvg('title', {}, `${g.label} - ${b.name}: ${b.v}${yLabel}`)),
        vSvg('text', { x: x0 + bw / 2, y: Y(b.v) - 4, 'text-anchor': 'middle', class: 'tick' }, Math.round(b.v)));
    });
    s.append(vSvg('text', { x: m.l + i * gw + gw / 2, y: H - m.b + 16, 'text-anchor': 'middle', class: 'tick' }, g.label));
  });
  return s;
}
function loading(p) { p.replaceChildren(vEl('div', { className: 'dim sm', textContent: 'Running real attacks on the real model...' })); }
