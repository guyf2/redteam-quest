TITLES.shell_lab = 'Shell lab';
MOUNT.shell_lab = function (p) {
  const out = vEl('div'), ta = vEl('input', { className: 'txt', value: 'ls; touch ../marker', ariaLabel: 'Command the model produced' });
  const presets = ['ls docs', 'cat notes.txt && touch ../marker', 'ls $(touch ../marker)', 'cat ../outside.txt', 'lsblk'].map(t => vEl('button', { className: 'chip', textContent: t, onclick: () => { ta.value = t; draw(); } }));
  p.append(vEl('p', { className: 'dim sm', textContent: 'A model produced this command string. See what a shell would do with it, and what a parser that never calls a shell sees. (Nothing here is executed.)' }), vEl('div', { className: 'chips' }, ...presets), vEl('label', {}, 'Command: '), ta, out);
  function draw() {
    const s = ta.value, META = /(;|&&|\|\||\||>|<|\$\(|`)/g, cmds = s.split(/;|&&|\|\||\||`|\$\(|\)/).map(x => x.trim()).filter(Boolean);
    const words = s.match(/"[^"]*"|'[^']*'|\S+/g) || [], first = words[0] || '', ALLOWED = ['ls', 'cat', 'wc', 'grep'];
    const marked = vEl('div', { className: 'vinfo', style: 'font-family:ui-monospace,monospace' }); s.split(META).forEach(part => marked.append(META.test(part) || /^(;|&&|\|\||\||>|<|\$\(|`)$/.test(part) ? vEl('mark', { textContent: part, style: 'background:#5a1f1f;color:#ffb4b4;border-radius:3px;padding:0 2px' }) : part)); META.lastIndex = 0;
    const startsOk = ALLOWED.some(a => s.trim().startsWith(a)), exactOk = ALLOWED.includes(first);
    out.replaceChildren(marked,
      vEl('div', { className: 'vbadge ' + (cmds.length > 1 ? 'bad' : 'ok'), style: 'display:block;margin:6px 0', textContent: `A shell would run ${cmds.length} separate command${cmds.length === 1 ? '' : 's'}: ${cmds.map(c => '"' + c + '"').join(', ')}` }),
      vEl('div', { className: 'vbadge ' + (startsOk ? 'bad' : 'ok'), style: 'display:block;margin:6px 0', textContent: `Check "starts with an allowed name": ${startsOk ? 'passes' : 'blocks'}` + (startsOk && (cmds.length > 1 || !exactOk) ? ' (fooled)' : '') }),
      vEl('div', { className: 'vbadge ' + (exactOk ? 'ok' : 'bad'), style: 'display:block;margin:6px 0', textContent: `Check "first word is exactly an allowed program": ${exactOk ? 'passes' : 'blocks'}` }),
      vEl('div', { className: 'vinfo', textContent: `Parsed without a shell, the arguments are: ${words.map(w => '[' + w + ']').join(' ')}. Metacharacters become plain text, so ";" is just a harmless word. Every path argument would still need to be checked.` }));
  }
  ta.oninput = draw; draw();
};
