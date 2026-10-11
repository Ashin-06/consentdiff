/* Owned local fixture adapter. Never creates a modelContext shim. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const params = new URLSearchParams(location.hash.slice(1));
  const credentials = { session_id: params.get('session'), driver: params.get('driver'), token: params.get('token') };
  history.replaceState(null, '', location.pathname); // capability stays in this closure
  let current = null, busy = false;
  const native = { status: 'unsupported', surface: null, secure_context: isSecureContext, registered: false, discovered: false, invocations: 0, reason: 'document.modelContext is unavailable in this browser configuration.' };
  const actions = ['inspect', 'stage', 'confirm', 'cancel', 'change_role', 'commit', 'retry'];
  async function post(path, payload) {
    const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Local action failed.');
    return result;
  }
  function show(record) {
    current = record;
    $('driver-label').textContent = `${record.scenario.id} · ${record.mode} · ${record.driver} path`;
    $('driver-plan').textContent = record.plan ? `Plan: ${record.plan.role} for ${record.plan.recipient} on ${record.plan.resource}, operation ${record.plan.operation}, version ${record.plan.version}.` : 'No staged plan.';
    $('driver-approval').textContent = record.approval ? `Approved: ${record.approval.role} for ${record.approval.recipient}, version ${record.approval.version}.` : 'No approval.';
    $('driver-response').textContent = record.response?.message || 'No action has run.';
    $('driver-cancelled').textContent = record.cancelled ? 'Cancelled: this plan must not commit.' : 'Not cancelled.';
    $('driver-count').textContent = `${record.action_count} actions completed`;
    $('driver-record').textContent = JSON.stringify(record, null, 2);
  }
  async function perform(action, transport) {
    if (busy) throw new Error('An action is already running.');
    if (!actions.includes(action)) throw new Error('Unknown local action.');
    busy = true; $('driver-error').hidden = true;
    document.querySelectorAll('[data-action]').forEach(b => b.disabled = true);
    try { const result = await post('/api/browser/action', { ...credentials, action, transport }); show(result); return result; }
    catch (error) { $('driver-error').textContent = error.message; $('driver-error').hidden = false; throw error; }
    finally { busy = false; document.querySelectorAll('[data-action]').forEach(b => b.disabled = false); }
  }
  document.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', () => {
    perform(button.dataset.action, credentials.driver === 'human' ? 'playwright-visible-control' : 'structured-http').catch(() => {});
  }));
  async function initialize() {
    show(await post('/api/browser/view', credentials));
    const mc = document.modelContext;
    if (credentials.driver === 'tool' && mc && ['registerTool', 'getTools', 'executeTool'].every(k => typeof mc[k] === 'function')) {
      native.surface = 'document.modelContext';
      try {
        await mc.registerTool({ name: 'consentdiff_action', description: 'Perform one validated action in the owned disposable ConsentDiff sharing session. Confirm means approval of the exact currently displayed plan.',
          inputSchema: { type: 'object', properties: { action: { type: 'string', enum: actions } }, required: ['action'], additionalProperties: false },
          annotations: { readOnlyHint: false }, execute: async input => {
            if (!input || typeof input !== 'object' || Object.keys(input).length !== 1 || !actions.includes(input.action)) throw new Error('Exactly one known action is required.');
            const result = await perform(input.action, 'native-webmcp'); native.invocations++;
            return JSON.stringify(result);
          } });
        native.registered = true;
        native.discovered = (await mc.getTools()).some(t => t.name === 'consentdiff_action');
        native.status = native.discovered ? 'available' : 'unavailable';
        native.reason = native.discovered ? 'Browser-native tool registered and discovered.' : 'Registration succeeded but discovery did not return the tool.';
      } catch (error) { native.status = 'error'; native.reason = `${error.name}: ${error.message}`; }
    } else if (credentials.driver === 'human') native.reason = 'Human path uses rendered controls; no native tool is registered here.';
    $('native-status').textContent = `${native.status}: ${native.reason}`;
    document.body.dataset.ready = 'true';
  }
  // Only the runner uses this narrow interface. The human runner never invokes
  // perform() or a controller through evaluate; it clicks actual controls.
  window.consentdiffDriver = Object.freeze({
    snapshot: () => ({ record: current, visible: $('driver-visible').innerText }),
    nativeStatus: () => ({ ...native }),
    httpAction: action => perform(action, 'structured-http'),
    nativeAction: async action => {
      if (native.status !== 'available') throw new Error(native.reason);
      const tool = (await document.modelContext.getTools()).find(t => t.name === 'consentdiff_action');
      if (!tool) throw new Error('Registered native tool disappeared.');
      // Chrome <=154 accepts JSON-string arguments; 155+ accepts objects.
      const major = Number(navigator.userAgent.match(/(?:HeadlessChrome|Chrome)\/(\d+)/)?.[1] || 0);
      await document.modelContext.executeTool(tool, major && major < 155 ? JSON.stringify({ action }) : { action });
      return current;
    }
  });
  initialize().catch(error => { $('driver-error').textContent = error.message; $('driver-error').hidden = false; document.body.dataset.ready = 'error'; });
})();
