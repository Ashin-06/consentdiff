# Complete workflow — inspect a viewer/editor mismatch

All actions below use fictional data. The fast paired experiment runs controller adapters; the manual demo exposes the same controls. **Run in Chrome** executes the selected journey through actual rendered controls paired with HTTP or native WebMCP tools. **Run all 10 in Chrome** executes the catalogue in the selected mode. See [BROWSER_INTEGRATION.md](BROWSER_INTEGRATION.md) for the full seeded/repaired browser commands.

## 1. Start ConsentDiff

~~~powershell
python -m consentdiff serve --port 8767 --runs-dir runs
~~~

Open [http://127.0.0.1:8767](http://127.0.0.1:8767). Use **Paired experiment** and choose **CD-002 — Tool widens the role**, **Seeded defects**, with two independent repeats.

The intended action is fixed: the file owner shares `file-42` with logical recipient `user-7`, granting viewer access after current confirmation.

## 2. Create equivalent independent starting states

The runner creates two SQLite applications with no existing grant. Their physical recipient IDs differ, but both map to the same logical fixture identities.

Before-state observations must match. The tool path cannot inherit a grant already made by the human path because the two stores are separate.

## 3. Execute the two journeys

The built-in confirmation trace is:

~~~text
inspect -> stage -> inspect -> confirm -> commit -> inspect
~~~

The human adapter and tool adapter execute this trace against their own application controllers. Each step records its plan, approval, cancellation state, and response.

This description applies to the fast controller runner. The browser runner instead clicks the rendered human controls and invokes the selected real tool transport, saving browser captures and authoritative observations for every repeat. Browser cases are labelled in the result and archive and cannot use the controller-only reducer.

## 4. Observe actual stored effects

The read-only observer checks each database's persisted grants and effect ledger. In CD-002's seeded variant, the tool controller changes the requested role to editor while the human controller keeps viewer.

The comparison therefore has evidence of a role mismatch and a violated user-intent requirement. A “shared successfully” response cannot override the stored role.

## 5. Inspect the result

The interface shows the human and tool effects, whether the paths agree, whether intent was satisfied, findings, and ordered traces.

A FAIL is the expected experiment outcome for this seeded discrepancy. It means the checker found the deliberate defect. The corresponding command-line run saves evidence and exits with code 1.

To run the same case without the browser interface:

~~~powershell
python -m consentdiff run --scenario CD-002 --mode seeded --repeats 2 --output-dir runs
~~~

## 6. Reduce the reproduction

Select **Reduce this trace**, or run:

~~~powershell
python -m consentdiff minimize --scenario CD-002 --mode seeded --budget 100
~~~

The reducer removes optional inspections when the same finding remains, but cannot discard the required stage, confirmation, and commit sequence. Each valid candidate is checked twice using fresh pairs.

Read the actual `one_minimal`, `budget_exhausted`, signature, and history fields. A completed one-minimal result is bounded by this valid single-step deletion rule; it does not prove there is no shorter workflow in another action language.

## 7. Compare the repaired reference

Change the mode to **Repaired reference** and rerun CD-002. The safe controller retains the requested viewer role in both paths.

~~~powershell
python -m consentdiff run --scenario CD-002 --mode repaired --repeats 2 --output-dir runs
~~~

The expectation is PASS within this fixture. This does not demonstrate that an arbitrary website or agent is correct.

## 8. Try the actual local controls

Choose the desired scenario/mode in **Paired experiment**, then open **Try the controls** and start a fresh demo. For each path, press **Stage**, **Confirm**, and **Commit**. Inspect the saved role shown below the controls.

For cancellation, start fresh and use **Stage**, **Cancel**, then **Commit**. For stale approval, start fresh and use **Stage**, **Confirm**, **Change role**, then **Commit**. Choose the relevant seeded scenario to observe its deliberate defect.

These temporary sessions do not update saved experiments. Starting a new demo creates fresh application state. The control buttons use fixed fictional operation arguments, not arbitrary real-user inputs.

## 9. Run the scenario catalogue

~~~powershell
python -m consentdiff suite --mode seeded
python -m consentdiff suite --mode repaired
~~~

The suite compares observed outcomes with expectations. A correctly detected unsafe scenario is a passing suite check. CD-008 remains INCONCLUSIVE in repaired mode because its observer is deliberately unavailable.

## 10. Inspect and verify evidence

The run command prints a case ID. Open it in **Evidence archive**, or inspect the files:

~~~text
runs/<case-id>/
  case.json
  report.html
  manifest.json
  evidence/
    intent.json
    human/
      application.sqlite
      before.json
      after.json
      trace.json
    tool/
      application.sqlite
      before.json
      after.json
      trace.json
~~~

The manifest covers 11 content files; it does not hash itself. The two SQLite files are final retained-witness databases. Before-state records are JSON observations, not separate before-state database images.

~~~powershell
python -m consentdiff verify runs/<case-id>
python -m consentdiff bundle runs/<case-id> --output consentdiff-evidence.zip
~~~

Replace the placeholder with the actual printed ID. Bundle export verifies integrity first and refuses an existing destination or a destination inside the run directory.

## 11. State what was established

A useful conclusion identifies the exact scenario, mode, intent, actual effect, and violated rule. A passing repaired case supports that controlled journey only. Manifest verification supports byte integrity relative to an unsigned manifest, not authenticity of the original execution.
