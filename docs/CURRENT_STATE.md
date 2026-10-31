# Current application assessment

Assessed on 31 October 2026 from the local application source.

## Product and implemented journey

WattWise is a local household energy planning MVP for Hackday 2026. Its Portuguese interface lets a household enter appliance power and schedules, protect essential usage, describe constraints, choose one change, compare projected consumption and variable cost, save up to ten simulations, and export JSON. An example picker offers the fictional three-person household (R$504.25 over 30 days) and a higher-consumption five-person household (R$2,111.76 at the same fictional rate). Loading can be undone; the selected profile persists in local storage. See [the higher-consumption case](HIGH_CONSUMPTION_USE_CASE.md) for assumptions.

A separate `/monitor` page demonstrates a five-room floorplan, nine mock sensors, pairing/disconnection, scenarios, and active-session energy integration. It uses simulated readings and does not feed the planning calculator or advisor. These two journeys remain separate: manual inputs support projected savings, and mock telemetry demonstrates a future monitoring experience.

Gemma through local Ollama selects from precomputed changes or asks for clarification. The interface retains up to four follow-up answers and displays a seven-day experiment for a recommendation. A separate calculator action ranks changes without AI. All results are manual estimates or synthetic demonstrations, rather than verified real-world savings.

## Architecture

| Area | Implementation |
| --- | --- |
| Local server | `app.py`: Python standard-library HTTP server bound to `127.0.0.1`; static assets and JSON endpoints |
| Web interface | `web/index.html`, `web/app.js`, `web/styles.css`: plain HTML, JavaScript, and CSS |
| Monitoring demonstration | `web/monitor.html`, `web/monitor.js`, `web/monitor-core.js`, `web/monitor.css`: independent fictional telemetry and browser-local connection choices |
| Calculation | `demo.py`: numeric validation, watts/hours integration, projections, and simulated interval comparisons |
| Advisor | `app.py` and `energy_skill.py`: Ollama requests, structured replies, candidate validation, follow-up history, and experiment construction |
| Advisor instructions | `skills/household-energy-coach/SKILL.md`: loaded at request time, with its hash returned for traceability |
| Persistence | Browser local storage for household inputs, follow-up answers, and saved simulations; no server-side database |
| Optional hosted path | CLI `--gemma` explicitly sends a calculated summary to Google's hosted API using an environment-provided key |

The web API exposes `GET /api/sample`, `GET /api/sample/high-consumption`, `GET /api/status`, `POST /api/analyze`, and `POST /api/advise`. The server checks Host and supplied Origin headers, accepts JSON POST bodies up to 64 KB, and serves only explicitly mapped assets. This is a loopback desktop prototype using Python's HTTP server, not an internet deployment setup.

## Verification during this assessment

| Check | Result |
| --- | --- |
| `python -m unittest discover -s tests -v` | 24 tests passed, including high-consumption calculations, protected loads, sample routes, and mocked advisor responses |
| `node --check web/app.js` | Passed |
| `node tests/test_samples.js` | Passed: sample selection, original example, persistence, reload, undo, failed-load recovery; DOM and fetch are test doubles |
| `node tests/test_monitor.js` | Passed: energy units, missing data, provenance, scenarios, room totals, disconnected sensors |
| `python demo.py` | Passed; manual projection produced 78.9 baseline kWh and 21.6 projected kWh reduction for the CLI fixture |
| `python demo.py --mode simulated` | Passed; complete synthetic daily windows produced 2.63 baseline kWh and 0.72 kWh reduction |
| Live HTTP sample check | Passed after restarting the outdated local server: both sample endpoints return successfully; analyzing the high-consumption sample returns R$2,111.76 baseline variable cost |
| New live model evaluation | Not run during this assessment |

Existing `ollama-smoke-test.json` and `skill-evaluation.json` are prior local execution records. The behavioral record reports four passing cases covering preference-based choice, missing routine, an answer changing the decision, and no available candidate. These records are small smoke evaluations, not broad model-quality evidence.

## Known gaps and next work

- Hard validation protects essential uses and candidate membership. Compatibility with free-text household preferences relies on model judgment; it is not enforced as a deterministic rule.
- The four-case behavioral script checks decision and candidate identity. It does not evaluate all claims in generated language. For example, the recorded no-candidate reply suggests a particular shower reduction despite having no candidate, and some recorded replies include numbers even though the skill asks for no numbers in prose.
- Malformed Ollama output is handled in several places, but invalid JSON in the outer response is reported as a generic value error. Invalid `OLLAMA_MODEL` configuration can also raise from the status endpoint without a JSON error response.
- The live smoke script assumes that a successful response contains a recommendation. A valid clarification response has no candidate and needs separate handling in that script.
- There is no real meter adapter, measured before/after comparison, account system, payment integration, or household usability evidence. Prices, schedules, and appliance power are entered assumptions.
- Local storage does not provide cross-device synchronization or backup. Both sample endpoints and the high-consumption analysis were verified over HTTP; no new browser interaction run was performed in this assessment.
- The server does not automatically reload Python code. An old process can serve updated static files while still lacking newly added endpoints. Restart after server updates; sample loading now explains this when the server returns 404 and preserves the existing profile.

Priorities are broader model and language evaluation, household usability testing, robust handling of advisor edge cases, and one measured-energy adapter. Keep the deterministic calculation boundary and explicit evidence labels as these features evolve.
