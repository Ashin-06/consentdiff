/* Real browser integration worker. Input is a validated local config on stdin.
   Human actions use Playwright locator.click only; no controller shortcut. */
'use strict';
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

async function main(input) {
  const origin = new URL(input.origin);
  if (origin.protocol !== 'http:' || origin.hostname !== '127.0.0.1' || origin.username || origin.password || origin.pathname !== '/' || origin.search || origin.hash) throw new Error('Only the owned loopback server is permitted.');
  const base = origin.origin, config = input.config;
  async function post(endpoint, value) {
    const response = await fetch(base + endpoint, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `${endpoint}: HTTP ${response.status}`);
    return body;
  }
  const health = await (await fetch(base + '/api/health')).json();
  if (health.application !== 'consentdiff') throw new Error('The selected loopback server is not the owned ConsentDiff application.');
  const browser = await chromium.launch({channel:'chrome',headless:true,args:config.webmcp_testing ? ['--enable-features=WebMCPTesting'] : []});
  const rows = [], errors = [];
  try {
    for (const mode of config.modes) for (const scenario of config.scenarios) {
      const runs = [];
      for (let repeat = 0; repeat < config.repeats; repeat++) {
        const session = await post('/api/browser/start', {scenario_id:scenario.id,mode,steps:scenario.steps});
        const captures = {}, runtime = {runner:'playwright',headless:true,browser_version:browser.version(),tool_adapter:null,webmcp:null};
        const context = await browser.newContext({viewport:{width:1000,height:900}});
        // Block requests outside this one owned server, including redirects.
        await context.route('**/*', route => new URL(route.request().url()).origin === base ? route.continue() : route.abort('blockedbyclient'));
        try {
          for (const driver of ['human','tool']) {
            const page = await context.newPage();
            page.setDefaultTimeout(15000);
            page.on('pageerror', error => errors.push(String(error)));
            await page.goto(base + '/driver.html#' + new URLSearchParams({session:session.session_id,driver,token:session.driver_tokens[driver]}));
            await page.waitForFunction(() => document.body.dataset.ready);
            assert.equal(await page.locator('body').getAttribute('data-ready'), 'true', await page.locator('#driver-error').innerText());
            const capability = await page.evaluate(() => window.consentdiffDriver.nativeStatus());
            if (driver === 'tool') {
              if (config.tool_adapter === 'native' && capability.status !== 'available') throw new Error(`Native WebMCP UNSUPPORTED: ${capability.reason}`);
              runtime.tool_adapter = config.tool_adapter !== 'http' && capability.status === 'available' ? 'native-webmcp' : 'structured-http';
            }
            const events = [], before = (await page.screenshot({fullPage:true})).toString('base64');
            for (const action of session.steps) {
              if (driver === 'human') {
                const responsePromise = page.waitForResponse(r => new URL(r.url()).pathname === '/api/browser/action' && r.request().method() === 'POST');
                await page.locator(`[data-action="${action}"]`).click();
                const response = await responsePromise;
                assert.equal(response.status(),200,await response.text());
                await page.waitForFunction(count => window.consentdiffDriver.snapshot().record.action_count === count, events.length + 1);
              } else {
                await page.evaluate(async ({action,adapter}) => {
                  if (adapter === 'native-webmcp') await window.consentdiffDriver.nativeAction(action);
                  else await window.consentdiffDriver.httpAction(action);
                }, {action,adapter:runtime.tool_adapter});
              }
              const snap = await page.evaluate(() => window.consentdiffDriver.snapshot());
              assert.equal(snap.record.receipt.action,action);
              assert.equal(snap.record.action_count,events.length+1);
              events.push({action,receipt_id:snap.record.receipt.id,transport:snap.record.receipt.transport,
                visible:snap.visible,plan:snap.record.plan,approval:snap.record.approval,cancelled:snap.record.cancelled,response:snap.record.response});
            }
            captures[driver] = {events,screenshots:{before,after:(await page.screenshot({fullPage:true})).toString('base64')}};
            if (driver === 'tool') {
              runtime.webmcp = {...await page.evaluate(() => window.consentdiffDriver.nativeStatus()),testing_flag:config.webmcp_testing};
              if (runtime.tool_adapter === 'native-webmcp') assert.equal(runtime.webmcp.invocations,session.steps.length);
            }
            await page.close();
          }
          runs.push({session_id:session.session_id,evidence_token:session.evidence_token,captures,runtime});
        } catch (error) {
          await post('/api/browser/abort', {session_id:session.session_id,evidence_token:session.evidence_token}).catch(()=>{});
          for (const run of runs) await post('/api/browser/abort', {session_id:run.session_id,evidence_token:run.evidence_token}).catch(()=>{});
          throw error;
        } finally { await context.close(); }
      }
      if (errors.length) throw new Error('Browser JavaScript errors: ' + errors.join('; '));
      const saved = await post('/api/browser/finish',{runs});
      const result = saved.result;
      const expected = mode === 'seeded' ? result.scenario.expected_status : scenario.id === 'CD-008' ? 'INCONCLUSIVE' : 'PASS';
      const kinds = result.findings.map(f=>f.kind);
      const matched = result.status === expected && (mode === 'repaired' || !result.scenario.expected_kind || kinds.includes(result.scenario.expected_kind));
      rows.push({id:scenario.id,mode,title:result.scenario.title,case_id:saved.case_id,expected_status:expected,observed_status:result.status,
        status:matched?'PASS':'FAIL',finding_kinds:kinds,repeats:result.repeats,tool_adapter:result.runtime.tool_adapter,
        native:result.runtime.webmcp,artifacts:saved.artifacts});
    }
    const passed = rows.filter(r=>r.status==='PASS').length;
    return {status:passed===rows.length?'PASS':'FAIL',checked_at:new Date().toISOString(),execution:'browser',browser_version:browser.version(),config,
      summary:{total:rows.length,passed,failed:rows.length-passed},results:rows,errors,
      interpretation:'Suite PASS means the real browser journeys matched expected fixture outcomes, including intentional failures and unknown evidence.'};
  } finally { await browser.close(); }
}

let text=''; process.stdin.setEncoding('utf8');
process.stdin.on('data',chunk=>{text+=chunk;if(text.length>131072)throw new Error('Worker input too large.');});
process.stdin.on('end',()=>main(JSON.parse(text)).then(result=>process.stdout.write(JSON.stringify(result)))
  .catch(error=>{process.stdout.write(JSON.stringify({status:'ERROR',error:String(error.message)}));process.exitCode=2;}));
