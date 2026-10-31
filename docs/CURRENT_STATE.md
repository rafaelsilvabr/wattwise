# Current application assessment

Assessed on 31 October 2026 from the local application source.

## Product and implemented journey

WattWise is a local household energy planning MVP for Hackday 2026. Its Portuguese interface lets a household enter appliance power and schedules, protect essential usage, describe constraints, choose one change, compare projected consumption and variable cost, save up to ten simulations, and export JSON. A fictional three-person household is available as a sample.

Gemma through local Ollama selects from precomputed changes or asks for clarification. The interface retains up to four follow-up answers and displays a seven-day experiment for a recommendation. A separate calculator action ranks changes without AI. All results are manual estimates or synthetic demonstrations, rather than verified real-world savings.

## Architecture

| Area | Implementation |
| --- | --- |
| Local server | `app.py`: Python standard-library HTTP server bound to `127.0.0.1`; static assets and JSON endpoints |
| Web interface | `web/index.html`, `web/app.js`, `web/styles.css`: plain HTML, JavaScript, and CSS |
| Calculation | `demo.py`: numeric validation, watts/hours integration, projections, and simulated interval comparisons |
| Advisor | `app.py` and `energy_skill.py`: Ollama requests, structured replies, candidate validation, follow-up history, and experiment construction |
| Advisor instructions | `skills/household-energy-coach/SKILL.md`: loaded at request time, with its hash returned for traceability |
| Persistence | Browser local storage for household inputs, follow-up answers, and saved simulations; no server-side database |
| Optional hosted path | CLI `--gemma` explicitly sends a calculated summary to Google's hosted API using an environment-provided key |

The web API exposes `GET /api/sample`, `GET /api/status`, `POST /api/analyze`, and `POST /api/advise`. The server checks Host and supplied Origin headers, accepts JSON POST bodies up to 64 KB, and serves only explicitly mapped assets. This is a loopback desktop prototype using Python's HTTP server, not an internet deployment setup.

## Verification during this assessment

| Check | Result |
| --- | --- |
| `python -m unittest discover -s tests -v` | 21 tests passed |
| `node --check web/app.js` | Passed |
| `python demo.py` | Passed; manual projection produced 78.9 baseline kWh and 21.6 projected kWh reduction for the CLI fixture |
| `python demo.py --mode simulated` | Passed; complete synthetic daily windows produced 2.63 baseline kWh and 0.72 kWh reduction |
| New HTTP smoke check | Not completed: sandbox blocked loopback access and permission to rerun outside the sandbox was declined |
| New live model evaluation | Not run during this assessment |

Existing `ollama-smoke-test.json` and `skill-evaluation.json` are prior local execution records. The behavioral record reports four passing cases covering preference-based choice, missing routine, an answer changing the decision, and no available candidate. These records are small smoke evaluations, not broad model-quality evidence.

## Known gaps and next work

- Hard validation protects essential uses and candidate membership. Compatibility with free-text household preferences relies on model judgment; it is not enforced as a deterministic rule.
- The four-case behavioral script checks decision and candidate identity. It does not evaluate all claims in generated language. For example, the recorded no-candidate reply suggests a particular shower reduction despite having no candidate, and some recorded replies include numbers even though the skill asks for no numbers in prose.
- Malformed Ollama output is handled in several places, but invalid JSON in the outer response is reported as a generic value error. Invalid `OLLAMA_MODEL` configuration can also raise from the status endpoint without a JSON error response.
- The live smoke script assumes that a successful response contains a recommendation. A valid clarification response has no candidate and needs separate handling in that script.
- There is no real meter adapter, measured before/after comparison, account system, payment integration, or household usability evidence. Prices, schedules, and appliance power are entered assumptions.
- Local storage does not provide cross-device synchronization or backup. The interface and HTTP endpoints were inspected in source; no new browser interaction run was performed in this assessment.

Priorities are broader model and language evaluation, household usability testing, robust handling of advisor edge cases, and one measured-energy adapter. Keep the deterministic calculation boundary and explicit evidence labels as these features evolve.
