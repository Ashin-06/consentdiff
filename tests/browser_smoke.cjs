/* Optional developer QA. Start `python -m consentdiff serve --port 8767` first.
   Requires Playwright and Chrome; neither is an application runtime dependency.
   Runs against the actual local server and creates synthetic saved experiments. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const output = path.resolve('.test-output');
  fs.mkdirSync(output, { recursive: true });
  const base = process.env.CONSENTDIFF_URL || 'http://127.0.0.1:8767';
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const checks = [], errors = [];
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  page.on('pageerror', error => errors.push(String(error)));

  async function idle() { await page.waitForFunction(() => !document.querySelector('#run').disabled); }
  async function requestFromClick(locator, endpoint, expectedStatus = 200) {
    const [response] = await Promise.all([
      page.waitForResponse(response => new URL(response.url()).pathname === endpoint && response.request().method() === 'POST'),
      locator.click()
    ]);
    assert.equal(response.status(), expectedStatus, `${endpoint} HTTP status`);
    const data = await response.json();
    await idle();
    return data;
  }
  async function run(scenario, mode = 'seeded') {
    await page.getByRole('tab', { name: /Paired experiment/ }).click();
    await page.locator('#scenario').selectOption(scenario);
    await page.locator('#mode').selectOption(mode);
    return requestFromClick(page.locator('#run'), '/api/run');
  }
  async function liveAction(driver, action, expectedStatus = 200) {
    return requestFromClick(page.locator(`#live-${driver} button[data-action="${action}"]`), '/api/sandbox/action', expectedStatus);
  }
  async function noHorizontalOverflow(label) {
    const dimensions = await page.evaluate(() => ({ viewport: innerWidth, page: document.documentElement.scrollWidth }));
    assert.ok(dimensions.page <= dimensions.viewport, `${label}: page ${dimensions.page}px exceeds ${dimensions.viewport}px`);
  }
  function passed(text) { checks.push(text); console.log(`PASS ${checks.length}: ${text}`); }

  try {
    await page.goto(base);
    await page.getByText('Local lab connected', { exact: true }).waitFor();
    await idle();
    assert.equal(await page.locator('#scenario option').count(), 10);
    assert.equal(await page.locator('#scenario').inputValue(), 'CD-002');
    await noHorizontalOverflow('Desktop landing');
    await page.screenshot({ path: path.join(output, 'consentdiff-desktop.png'), fullPage: true });
    passed('Workbench loads live configuration and all ten scenarios without desktop overflow.');

    const seeded = await run('CD-002');
    assert.equal(seeded.result.status, 'FAIL');
    assert.equal(await page.locator('#result-status').innerText(), 'FAIL');
    assert.equal(await page.locator('#effects .human .effect-entry strong').innerText(), 'viewer');
    assert.equal(await page.locator('#effects .tool .effect-entry strong').innerText(), 'editor');
    assert.equal(await page.locator('#parity').innerText(), 'No');
    assert.equal(await page.locator('#intent-status').innerText(), 'No');
    assert.equal(await page.locator('#downloads a').count(), 3);
    await page.screenshot({ path: path.join(output, 'seeded-human-viewer-tool-editor.png'), fullPage: true });
    passed('Seeded CD-002 shows the authoritative human viewer / tool editor mismatch as FAIL.');

    const reduced = await requestFromClick(page.locator('#reduce'), '/api/minimize');
    assert.equal(reduced.original_count, 6);
    assert.equal(reduced.minimized_count, 3);
    assert.equal(reduced.one_minimal, true);
    assert.equal(await page.locator('#reduction-title').innerText(), '6 → 3 actions');
    assert.match(await page.locator('#reduction-summary').innerText(), /1-minimal.*valid single-step deletions/);
    assert.equal(await page.locator('#reduction-steps span').count(), 3);
    passed('Reduction preserves the target violation and valid consent while reducing six actions to three.');

    for (const [kind, extension] of [['report', '.html'], ['json', '.json'], ['bundle', '.zip']]) {
      const link = page.locator(`#downloads a[href$="/${kind}"]`);
      const [download] = await Promise.all([page.waitForEvent('download'), link.click()]);
      assert.equal(await download.failure(), null);
      assert.ok(download.suggestedFilename().endsWith(extension));
      const destination = path.join(output, `downloaded-${kind}${extension}`);
      await download.saveAs(destination);
      const bytes = fs.readFileSync(destination);
      assert.ok(bytes.length > 100);
      if (kind === 'json') assert.equal(JSON.parse(bytes.toString('utf8')).case_id, seeded.case_id);
      if (kind === 'bundle') assert.equal(bytes.subarray(0, 2).toString(), 'PK');
      if (kind === 'report') assert.match(bytes.toString('utf8'), /ConsentDiff/i);
    }
    passed('HTML report, JSON case, and ZIP evidence bundle download successfully from the actual UI.');

    const repaired = await run('CD-002', 'repaired');
    assert.equal(repaired.result.status, 'PASS');
    assert.equal(await page.locator('#result-status').innerText(), 'PASS');
    assert.equal(await page.locator('#effects .human .effect-entry strong').innerText(), 'viewer');
    assert.equal(await page.locator('#effects .tool .effect-entry strong').innerText(), 'viewer');
    assert.equal(await page.locator('#parity').innerText(), 'Yes');
    assert.equal(await page.locator('#intent-status').innerText(), 'Yes');
    assert.equal(await page.locator('#reduce').isDisabled(), true);
    passed('Repaired CD-002 passes with viewer effects on both paths and disables failure reduction.');

    const bothWrong = await run('CD-003');
    assert.equal(bothWrong.result.status, 'FAIL');
    assert.equal(await page.locator('#parity').innerText(), 'Yes');
    assert.equal(await page.locator('#intent-status').innerText(), 'No');
    assert.equal(await page.locator('#result-status').innerText(), 'FAIL');
    assert.equal(await page.locator('#effects .human .effect-entry strong').innerText(), 'editor');
    assert.equal(await page.locator('#effects .tool .effect-entry strong').innerText(), 'editor');
    passed('CD-003 correctly reports FAIL when both paths agree on the wrong editor permission.');

    const unknown = await run('CD-008');
    assert.equal(unknown.result.status, 'INCONCLUSIVE');
    assert.equal(await page.locator('#result-status').innerText(), 'INCONCLUSIVE');
    assert.equal(await page.locator('#parity').innerText(), 'Unknown');
    assert.equal(await page.locator('#intent-status').innerText(), 'Unknown');
    assert.ok((await page.locator('#effects').innerText()).includes('Evidence unavailable'));
    assert.equal(await page.locator('#reduce').isDisabled(), true);
    passed('CD-008 treats missing observer evidence as INCONCLUSIVE, not a successful empty effect.');

    await page.getByRole('tab', { name: /Scenario checks/ }).click();
    const suite = await requestFromClick(page.locator('#run-suite'), '/api/suite');
    assert.equal(suite.status, 'PASS');
    assert.equal(suite.summary.total, 10);
    assert.equal(suite.summary.passed, 10);
    assert.equal(await page.locator('#suite-results article').count(), 10);
    assert.match(await page.locator('#suite-summary').innerText(), /10 \/ 10 expectations matched/);
    assert.ok(suite.results.some(row => row.observed_status === 'FAIL' && row.status === 'PASS'));
    await page.screenshot({ path: path.join(output, 'scenario-suite.png'), fullPage: true });
    passed('All ten seeded scenario expectations pass, explicitly including expected unsafe fixture outcomes.');

    await page.locator('#suite-mode').selectOption('repaired');
    const repairedSuite = await requestFromClick(page.locator('#run-suite'), '/api/suite');
    assert.equal(repairedSuite.status, 'PASS');
    assert.equal(repairedSuite.summary.passed, 10);
    assert.match(await page.locator('#suite-summary').innerText(), /10 \/ 10 expectations matched/);
    passed('All ten repaired-reference scenario expectations also pass through the UI.');

    await page.getByRole('tab', { name: /Evidence archive/ }).click();
    await page.locator('#refresh').click();
    await idle();
    const archiveRow = page.locator('.archive-row').filter({ hasText: seeded.case_id });
    assert.equal(await archiveRow.count(), 1);
    await archiveRow.getByRole('button', { name: /Open record/ }).click();
    await idle();
    assert.equal(await page.locator('#view-experiment').isVisible(), true);
    assert.equal(await page.locator('#run-id').innerText(), seeded.case_id);
    assert.equal(await page.locator('#result-status').innerText(), 'FAIL');
    assert.equal(await page.locator('#effects .tool .effect-entry strong').innerText(), 'editor');
    passed('The archive reopens the exact saved case with its original effects and status.');

    await page.locator('#scenario').selectOption('CD-002');
    await page.locator('#mode').selectOption('seeded');
    await page.getByRole('tab', { name: /Try the controls/ }).click();
    const sandbox = await requestFromClick(page.locator('#start-live'), '/api/sandbox/start');
    assert.ok(sandbox.session_id);
    for (const driver of ['human', 'tool']) {
      const staged = await liveAction(driver, 'stage');
      assert.equal(staged.observation.effects.length, 0);
      assert.match(await page.locator(`#live-${driver}-state`).innerText(), /No saved grant/);
      const confirmed = await liveAction(driver, 'confirm');
      assert.ok(confirmed.approval);
      assert.equal(confirmed.observation.effects.length, 0);
      const committed = await liveAction(driver, 'commit');
      assert.equal(committed.observation.effects.length, 1);
      assert.equal(committed.observation.effects[0].role, driver === 'human' ? 'viewer' : 'editor');
      assert.equal(await page.locator(`#live-${driver}-state strong`).innerText(), `${driver === 'human' ? 'viewer' : 'editor'} → user-7`);
    }
    await page.screenshot({ path: path.join(output, 'interactive-controls.png'), fullPage: true });
    passed('Real Stage → Confirm → Commit controls produce human viewer and tool editor in separate CD-002 app states.');

    await requestFromClick(page.locator('#start-live'), '/api/sandbox/start');
    const premature = await liveAction('human', 'commit', 400);
    assert.ok(premature.error);
    assert.equal(await page.locator('#error').isVisible(), true);
    assert.match(await page.locator('#live-human-state strong').innerText(), /No saved grant/);
    const stageAfterRejection = await liveAction('human', 'stage');
    assert.equal(stageAfterRejection.observation.effects.length, 0);
    await liveAction('human', 'cancel');
    const cancelled = await liveAction('human', 'commit');
    assert.equal(cancelled.observation.effects.length, 0);
    assert.match(await page.locator('#live-human-state strong').innerText(), /No saved grant/);
    passed('Interactive controls do not commit the human path before approval or after cancellation.');

    await page.getByRole('tab', { name: /Paired experiment/ }).click();
    const selectedBefore = await page.locator('#scenario').inputValue();
    await page.locator('#repeats').fill('0');
    let invalidRequestCount = 0;
    const countRun = request => { if (new URL(request.url()).pathname === '/api/run') invalidRequestCount++; };
    page.on('request', countRun);
    await page.locator('#run').click();
    assert.equal(await page.locator('#repeats').evaluate(input => input.validity.rangeUnderflow), true);
    assert.equal(invalidRequestCount, 0);
    page.off('request', countRun);
    await page.locator('#repeats').fill('2');
    assert.equal(await page.locator('#scenario').inputValue(), selectedBefore);
    passed('Invalid repeat counts are blocked by the form before any experiment is submitted.');

    await page.route('**/api/run', route => {
      const body = route.request().postDataJSON();
      route.continue({ postData: JSON.stringify({ ...body, scenario_id: 'CD-INVALID-QA' }) });
    });
    const rejected = await requestFromClick(page.locator('#run'), '/api/run', 400);
    assert.ok(rejected.error);
    assert.equal(await page.locator('#error').isVisible(), true);
    assert.ok((await page.locator('#error').innerText()).length > 3);
    assert.equal(await page.locator('#run').isEnabled(), true);
    await page.unroute('**/api/run');
    passed('A real server validation error is shown as an alert and leaves the controls usable.');

    await run('CD-002', 'repaired');
    assert.equal(await page.locator('#error').isVisible(), false);
    assert.equal(await page.locator('#result-status').innerText(), 'PASS');
    passed('A successful retry clears the previous error and displays a fresh result.');

    await page.locator('#tab-experiment').focus();
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#tab-suite').getAttribute('aria-selected'), 'true');
    assert.equal(await page.locator('#tab-suite').evaluate(element => element === document.activeElement), true);
    await page.keyboard.press('End');
    assert.equal(await page.locator('#tab-archive').getAttribute('aria-selected'), 'true');
    await page.keyboard.press('Home');
    assert.equal(await page.locator('#tab-experiment').getAttribute('aria-selected'), 'true');
    passed('Tabs support keyboard arrows, Home, End, selected state, and correct focus.');

    await page.setViewportSize({ width: 390, height: 844 });
    for (const view of ['experiment', 'suite', 'live', 'archive']) {
      await page.locator(`#tab-${view}`).click();
      await noHorizontalOverflow(`390px ${view} view`);
      await page.screenshot({ path: path.join(output, `consentdiff-mobile-${view}.png`), fullPage: true });
    }
    assert.deepEqual(errors, []);
    passed('All four views fit a 390px viewport with no page overflow and no uncaught JavaScript errors.');

    const result = { status: 'PASS', checked_at: new Date().toISOString(), url: base, checks, errors };
    fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result, null, 2));
  } catch (failure) {
    await page.screenshot({ path: path.join(output, 'browser-failure.png'), fullPage: true }).catch(() => {});
    fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify({ status: 'FAIL', checks, errors, failure: String(failure), stack: failure.stack }, null, 2));
    throw failure;
  } finally {
    await context.close();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
