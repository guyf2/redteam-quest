TITLES.path_lab = 'Path lab';
MOUNT.path_lab = function (p) {
  const ROOT = '/srv/agent/files', out = vEl('div'), ta = vEl('input', { className: 'txt', value: 'notes/../../secrets/key.txt', ariaLabel: 'Path the model asks for' });
  const presets = ['notes.txt', 'docs/../notes.txt', '../secrets/key.txt', '/srv/other/data.txt', '../files_old/x.txt', 'a/b/../../../etc/hosts'].map(t => vEl('button', { className: 'chip', textContent: t, onclick: () => { ta.value = t; draw(); } }));
  p.append(vEl('p', { className: 'dim sm', textContent: `The sandbox is ${ROOT}. The model asks for a path. See how it resolves, and which checks would be fooled.` }), vEl('div', { className: 'chips' }, ...presets), vEl('label', {}, 'Path: '), ta, out);
  const resolve = s => { const parts = []; (s.startsWith('/') ? s : ROOT + '/' + s).split('/').forEach(seg => { if (seg === '' || seg === '.') return; if (seg === '..') parts.pop(); else parts.push(seg); }); return '/' + parts.join('/'); };
  const inside = r => r === ROOT || r.startsWith(ROOT + '/');
  function draw() {
    const raw = ta.value, joined = raw.startsWith('/') ? raw : ROOT + '/' + raw, real = resolve(raw);
    const naive = joined.startsWith(ROOT), good = inside(real);
    const row = (label, v, ok) => vEl('div', { className: 'vbadge ' + (ok ? 'ok' : 'bad'), textContent: `${label}: ${v}`, style: 'display:block;margin:4px 0' });
    out.replaceChildren(vEl('div', { className: 'vinfo' }, vEl('div', { textContent: `Joined text:   ${joined}` }), vEl('div', { textContent: `Real location: ${real}` })),
      row('Naive "starts with the root" check says', naive ? 'ALLOW' : 'BLOCK', naive === good), row('Resolve first, compare path components says', good ? 'ALLOW' : 'BLOCK', true),
      vEl('p', { className: 'dim sm', textContent: naive !== good ? (naive ? 'The naive check lets this escape through: the text starts with the root, but the real location is outside.' : 'The naive check wrongly blocks a legitimate path.') : 'Both agree here. Try the other presets: look-alike names and .. climbing defeat the naive check. (Symlinks need the real filesystem, so they are not shown.)' }));
  }
  ta.oninput = draw; draw();
};
