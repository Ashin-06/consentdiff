(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const state = { busy: false, current: null, session: null, scenarios: [] };
  const pretty = s => String(s).replaceAll('_', ' ');
  const json = value => JSON.stringify(value, null, 2);
  function el(tag, className = '', text = '') { const node = document.createElement(tag); node.className = className; node.textContent = text; return node; }
  function pill(status) { return el('span', `pill ${String(status).toLowerCase()}`, status); }
  function message(text, error = false) { const box = $(error ? 'error' : 'notice'); box.textContent = text; box.hidden = !text; if (!error) $('error').hidden = true; }
  async function api(path, data) { const response = await fetch(path, data === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); const body = await response.json(); if (!response.ok) throw new Error(body.error || 'The local request failed.'); return body; }
  async function work(fn) { if (state.busy) return; state.busy = true; document.querySelectorAll('button:not([role=tab])').forEach(b => b.disabled = true); $('error').hidden = true; try { await fn(); } catch (e) { message(e.message, true); } finally { state.busy = false; document.querySelectorAll('button:not([role=tab])').forEach(b => b.disabled = false); if (state.current) $('reduce').disabled = state.current.result.status !== 'FAIL' || state.current.result.execution === 'browser'; } }
  function activate(view) { document.querySelectorAll('[role=tab]').forEach(b => { const active = b.dataset.view === view; b.setAttribute('aria-selected', String(active)); b.tabIndex = active ? 0 : -1; $(`view-${b.dataset.view}`).hidden = !active; }); }
  const tabs = [...document.querySelectorAll('[role=tab]')];
  tabs.forEach((tab, i) => { tab.addEventListener('click', () => activate(tab.dataset.view)); tab.addEventListener('keydown', e => { if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) { e.preventDefault(); const n = e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length; tabs[n].focus(); activate(tabs[n].dataset.view); } }); });
  const config = () => ({ scenario_id: $('scenario').value, mode: $('mode').value, repeats: Number($('repeats').value) });
  function showEffects(container, driver, observation) {
    const card = el('div', `effect-card ${driver}`); card.append(el('p', 'eyebrow', driver === 'human' ? '01 / HUMAN PATH' : '02 / TOOL PATH'));
    if (observation.status !== 'complete') card.append(el('h3', '', 'Evidence unavailable'), el('p', 'hint', 'Unknown effects are not an empty successful result.'));
    else if (!observation.effects.length) card.append(el('h3', '', 'No committed effect'), el('p', 'hint', 'The observer confirmed an empty effect ledger.'));
    else observation.effects.forEach(effect => { const row = el('div', 'effect-entry'); row.append(el('small', '', `${effect.resource} → ${effect.recipient}`), el('strong', '', pretty(effect.role)), el('p', '', `Operation: ${effect.operation}`)); card.append(row); });
    container.append(card);
  }
  function render(caseData) {
    state.current = caseData; const r = caseData.result; $('empty').hidden = true; $('result').hidden = false; $('reduction-output').hidden = true;
    $('verdict').className = `verdict ${r.status.toLowerCase()}`; $('result-scenario').textContent = `${r.scenario.id} / ${r.mode.toUpperCase()} / ${r.repeats} REPEATS`;
    $('result-title').textContent = r.status === 'FAIL' ? 'The observed result violates the intent.' : r.status === 'PASS' ? 'The observed effects respect the intent.' : 'The evidence cannot establish an outcome.';
    $('result-description').textContent = r.scenario.title + (r.repeat_consistent ? ' · Repeated outcomes agree.' : ' · Repeated outcomes disagree.') + (r.execution === 'browser' ? ` · Real Chrome controls + ${r.runtime.tool_adapter}. Chrome ${r.runtime.browser_version}.` : ' · Controller reference.');
    $('result-status').replaceWith(Object.assign(pill(r.status), { id: 'result-status' }));
    for (const driver of ['human', 'tool']) $(`${driver}-count`).textContent = r.journeys[driver].after.effects?.length ?? '?';
    $('parity').textContent = r.parity === null ? 'Unknown' : r.parity ? 'Yes' : 'No'; $('intent-status').textContent = !r.observer_complete ? 'Unknown' : r.intent_satisfied ? 'Yes' : 'No';
    $('effects').replaceChildren(); ['human', 'tool'].forEach(d => showEffects($('effects'), d, r.journeys[d].after));
    $('findings').replaceChildren();
    if (!r.findings.length) $('findings').append(el('p', 'hint', r.status === 'PASS' ? 'No contract violation was observed in this controlled journey.' : 'An unavailable or inconsistent observer prevents a reliable conclusion.'));
    r.findings.forEach(f => { const row = el('article', 'finding'), heading = el('header'); heading.append(el('h3', '', pretty(f.kind)), el('span', 'pill', f.journey)); row.append(heading, el('p', '', `Expected: ${typeof f.expected === 'string' ? f.expected : json(f.expected)}`)); const details = el('details'); details.append(el('summary', '', 'Actual effect and evidence reference'), el('pre', '', json(f))); row.append(details); $('findings').append(row); });
    $('timelines').replaceChildren();
    for (const driver of ['human', 'tool']) { const box = el('div'); box.append(el('p', 'eyebrow', `${driver.toUpperCase()} / ORDERED ACTIONS`)); const list = el('ol', 'trace'); r.journeys[driver].trace.forEach(step => { const row = el('li', '', pretty(step.action)); row.append(el('small', '', step.plan ? `Plan: ${step.plan.role} for ${step.plan.recipient} · version ${step.plan.version}` : 'No staged plan'), el('small', '', `${step.approval ? `Approved version ${step.approval.version}` : 'No approval'} · ${step.response.message}`)); list.append(row); }); box.append(list); $('timelines').append(box); }
    $('reduce').disabled = r.status !== 'FAIL' || r.execution === 'browser'; $('reduce').textContent = r.execution === 'browser' ? 'Reduction is controller-only' : 'Reduce this trace ↘'; $('run-id').textContent = caseData.case_id; $('raw').textContent = json(caseData); $('downloads').replaceChildren();
    for (const [kind, url] of Object.entries(caseData.artifacts)) { if (!url.startsWith(`/api/cases/${caseData.case_id}/`)) continue; const link = el('a', 'secondary', `↓ ${kind.toUpperCase()}`); link.href = url; link.download = ''; $('downloads').append(link); }
  }
  $('run-form').addEventListener('submit', e => { e.preventDefault(); work(async () => { message('Preparing two isolated application states and replaying the paired journey…'); const result = await api('/api/run', config()); render(result); await archive(); message(`Experiment saved. ${result.result.status} within the controlled reference application.`); }); });
  $('reduce').addEventListener('click', () => work(async () => { const r = state.current.result; message('Reducing valid steps while preserving the same finding…'); const result = await api('/api/minimize', { scenario_id: r.scenario.id, mode: r.mode }); $('reduction-output').hidden = false; $('reduction-title').textContent = `${result.original_count} → ${result.minimized_count} actions`; $('reduction-summary').textContent = `${result.one_minimal ? '1-minimal within valid single-step deletions.' : 'Minimality was not established.'} ${result.evaluations} paired evaluations. Confirmation preconditions remain required.`; $('reduction-steps').replaceChildren(...result.minimized_steps.map(s => el('span', '', pretty(s)))); $('reduction-json').textContent = json(result); message('Reduction complete. The detailed history records invalid and rejected candidates.'); }));
  $('run-suite').addEventListener('click', () => work(async () => { message('Checking all ten expected scenario outcomes…'); const data = await api('/api/suite', { mode: $('suite-mode').value }); $('suite-summary').hidden = false; $('suite-summary').className = `verdict ${data.status.toLowerCase()}`; $('suite-summary').replaceChildren(el('h2', '', `${data.summary.passed} / ${data.summary.total} expectations matched`), pill(data.status)); $('suite-results').replaceChildren(); data.results.forEach(r => { const card = el('article', 'panel'), heading = el('div', 'section-heading'); heading.append(el('p', 'eyebrow', r.id), pill(r.status)); card.append(heading, el('h3', '', r.title), el('p', '', `Expected: ${r.expected_status} · Observed: ${r.observed_status}`), el('p', 'hint', r.finding_kinds.map(pretty).join(' · ') || 'No finding required.')); $('suite-results').append(card); }); message(data.interpretation); }));
  async function archive() { const data = await api('/api/cases'); $('archive').replaceChildren(); if (!data.cases.length) $('archive').append(el('div', 'panel', 'No saved runs yet. Run a paired experiment first.')); data.cases.forEach(c => { const row = el('article', 'archive-row'), label = el('div'); label.append(el('h3', '', `${c.scenario_id} · ${c.title}`), el('p', '', `${c.mode} · ${c.created_at} · ${c.case_id}`)); const button = el('button', 'secondary', 'Open record ↗'); button.addEventListener('click', () => work(async () => { render(await api(`/api/cases/${encodeURIComponent(c.case_id)}/json`)); activate('experiment'); message('Opened the saved experiment.'); })); row.append(label, pill(c.status), button); $('archive').append(row); }); }
  $('refresh').addEventListener('click', () => work(archive));
  $('scenario').addEventListener('change', () => { const item = state.scenarios.find(s => s.id === $('scenario').value); $('scenario-description').textContent = `Expected seeded outcome: ${item?.expected_status || 'unknown'}.`; });
  function renderLive(data) { state.session = data.session_id; $('live-config').textContent = `${data.scenario.id} · ${data.scenario.title} · ${data.mode}`; $('live-pair').replaceChildren(); for (const driver of ['human', 'tool']) { const panel = el('article', 'panel live-panel'); panel.id = `live-${driver}`; panel.append(el('p', 'eyebrow', driver === 'human' ? 'HUMAN INTERFACE' : 'STRUCTURED TOOL INTERFACE'), el('h3', '', 'Share “Project notes”'), el('p', 'hint', 'file-42 · recipient Maya (user-7) · viewer only')); const buttons = el('div', 'live-actions'); for (const action of ['stage', 'confirm', 'cancel', 'change_role', 'commit', 'retry']) { const button = el('button', action === 'commit' ? 'primary' : 'secondary', pretty(action)); button.dataset.action = action; button.addEventListener('click', () => work(async () => { const result = await api('/api/sandbox/action', { session_id: state.session, driver, action }); const view = $(`live-${driver}-state`); view.replaceChildren(el('strong', '', result.observation.status !== 'complete' ? 'Evidence unavailable' : result.observation.effects.length ? result.observation.effects.map(e => `${e.role} → ${e.recipient}`).join(', ') : 'No saved grant'), el('p', '', result.response.message), el('p', '', `Plan: ${result.plan?.role || 'none'} · approval: ${result.approval ? `version ${result.approval.version}` : 'none'}`)); $(`live-${driver}-json`).textContent = json(result); message(`${driver} action ${pretty(action)} completed in the fictional application.`); })); buttons.append(button); } const view = el('div', 'live-state'); view.id = `live-${driver}-state`; view.append(el('strong', '', 'No saved grant'), el('p', '', 'Start with Stage. Then Confirm or Cancel before Commit.')); const details = el('details'), pre = el('pre'); pre.id = `live-${driver}-json`; details.append(el('summary', '', 'Action arguments and observed state'), pre); panel.append(buttons, view, details); $('live-pair').append(panel); } }
  $('start-live').addEventListener('click', () => work(async () => { renderLive(await api('/api/sandbox/start', config())); message('Fresh independent app states are ready. These temporary demo sessions are not saved experiments.'); }));
  const browserBox = el('section', 'browser-controls');
  browserBox.append(el('p', 'eyebrow', 'REAL BROWSER INTEGRATION'), el('h3', '', 'Run the displayed controls.'), el('p', 'hint', 'Chrome clicks the local app and records visible plans, approvals and effects. Requires Node, Playwright and Chrome. Up to 3 repeats.'));
  const adapterLabel = el('label', '', 'Tool transport'); adapterLabel.htmlFor = 'browser-adapter';
  const adapter = el('select'); adapter.id = 'browser-adapter';
  [['auto','Detect native; otherwise HTTP'],['http','Structured local HTTP'],['native','Require native WebMCP']].forEach(([value,text]) => {const option=el('option','',text); option.value=value;adapter.append(option);});
  const flagLabel = el('label', 'check-label'), flag = el('input'); flag.type='checkbox'; flag.id='browser-native-flag';
  flagLabel.append(flag, document.createTextNode(' Enable native testing in this disposable Chrome only'));
  const runBrowserButton = el('button','primary','Run in Chrome ↗'); runBrowserButton.id='browser-run'; runBrowserButton.type='button';
  const runBrowserSuite = el('button','secondary','Run all 10 in Chrome'); runBrowserSuite.id='browser-suite'; runBrowserSuite.type='button';
  const browserSummary = el('p','hint'); browserSummary.id='browser-summary'; browserSummary.setAttribute('aria-live','polite');
  browserBox.append(adapterLabel, adapter, flagLabel, runBrowserButton, runBrowserSuite, browserSummary);
  $('run-form').after(browserBox);
  async function browserRun(all) {
    const c = config();
    if (!Number.isInteger(c.repeats) || c.repeats < 1 || c.repeats > 3) throw new Error('Real browser runs support 1 to 3 independent repeats.');
    const job = await api('/api/browser/job', {schema_version:'1.0',fixture:'consentdiff-owned-local-app',
      scenarios:(all ? state.scenarios : [{id:c.scenario_id}]).map(s=>({id:s.id})),modes:[c.mode],repeats:c.repeats,
      tool_adapter:adapter.value,webmcp_testing:flag.checked});
    message('Chrome is executing the local visible controls and tool calls. This can take about a minute for all scenarios…');
    browserSummary.textContent='Browser run active. Evidence is saved after each completed paired scenario.';
    for (let attempt=0;attempt<320;attempt++) {
      await new Promise(resolve=>setTimeout(resolve,1000));
      const status = await api(`/api/browser/jobs/${job.job_id}`);
      if (status.state==='error') throw new Error(status.error);
      if (status.state!=='complete') continue;
      const result=status.result;
      browserSummary.textContent=`${result.summary.passed}/${result.summary.total} scenario expectations matched. Transport: ${[...new Set(result.results.map(r=>r.tool_adapter))].join(', ')}. Saved cases are in the archive.`;
      if (result.results.length) render(await api(`/api/cases/${result.results[0].case_id}/json`));
      await archive();
      message(result.interpretation); return;
    }
    throw new Error('Browser status timed out. Completed cases remain in the evidence archive; no completion is assumed.');
  }
  runBrowserButton.addEventListener('click',()=>work(()=>browserRun(false)));
  runBrowserSuite.addEventListener('click',()=>work(()=>browserRun(true)));
  work(async () => { const data = await api('/api/demo'); state.scenarios = data.scenarios; $('scenario').replaceChildren(...data.scenarios.map(s => { const option = el('option', '', `${s.id} · ${s.title}`); option.value = s.id; return option; })); $('scenario').value = 'CD-002'; $('scenario').dispatchEvent(new Event('change')); $('connection').textContent = 'Local lab connected'; await archive(); });
})();
