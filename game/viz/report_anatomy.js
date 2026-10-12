TITLES.report_anatomy = 'Weak vs. strong report';
MOUNT.report_anatomy = function (p) {
  let strong = true;
  const out = vEl('div'), btn = vEl('button', { className: 'ghost sm', textContent: 'Show the weak version', onclick: () => { strong = !strong; btn.textContent = strong ? 'Show the weak version' : 'Show the strong version'; draw(); } });
  p.append(vEl('p', { className: 'dim sm', textContent: 'Same finding, two reports. Hover nothing: just compare what an engineer could DO with each.' }), btn, out);
  const STRONG = [['Summary', 'The support assistant can be steered by an outsider\'s email to issue refunds with no human approval.'], ['Impact', '40 refunds ($2,000) in 10 minutes in staging, no alert, no daily cap.'],
    ['Severity', 'Critical: unauthenticated, automatic, repeating, undetected loss of money.'], ['Steps to reproduce', '1. Send an email to the support inbox containing the instruction. 2. Ask the assistant to summarise the inbox. 3. Observe the refund call. 4. Repeat.'],
    ['Evidence', 'Refund log entries (account redacted); no alert in the monitoring console.'], ['Remediation', 'Refunds only when the user\'s own message justifies them; daily cap; neutralise untrusted email text; alert on repeats; rotate the exposed key.'], ['Disclosure', 'Sent privately to the security contact; details withheld until fixed.']];
  const WEAK = [['', 'I found a really bad issue with the bot. It sent loads of money to someone. The key is sk-live-7Hq29XKd0LmPz4Wv and the customer maria.gonzalez@customer.example was in the log. You should fix it. It was easy.']];
  const FLAWS = ['No steps: nobody can reproduce it.', 'No numbers: "loads of money" cannot be prioritised.', 'LIVE KEY pasted: the report is now a second incident.', 'Customer personal data pasted.', 'No severity, no layered fix, no disclosure terms.'];
  function draw() {
    const rows = (strong ? STRONG : WEAK).map(([h, t]) => vEl('div', { style: 'margin:6px 0' }, ...(h ? [vEl('b', { textContent: h + ': ', style: 'color:var(--gold)' })] : []), t));
    out.replaceChildren(vEl('div', { className: 'vinfo', style: 'padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--card2)' }, ...rows),
      vEl('ul', { className: strong ? 'dim sm' : 'sm', style: 'margin:8px 0 0 18px;padding:0;' + (strong ? '' : 'color:var(--bad)') }, ...(strong ? ['Short, structured, numbers from the evidence, safe to forward.'] : FLAWS).map(t => vEl('li', { textContent: t }))));
  }
  draw();
};
