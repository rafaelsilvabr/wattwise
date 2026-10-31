# Hackday demo and handoff

## One outcome

A household can enter its usage assumptions, preserve essential activities, choose one feasible change, and understand its projected effect. The demo makes the evidence type visible throughout.

Keep the MVP small: no login, payment integration, automatic switching, hardware purchases, utility-account scraping, or tariff reconstruction. The commercial hypothesis lives in PROJECT.md; the demo should show the working product.

## Two-minute demonstration

1. **Problem (15 seconds):** “A high bill tells a family what it spent, but not which practical change is worth trying.”
2. **Inputs (25 seconds):** Load the fictional example. Show watts, hours, entered price, and protected work usage. Explain that these are estimates.
3. **AI (35 seconds):** With local Gemma ready, explain the routine and generate one proposal. Point to the selected appliance and its reason. The backend supplies the numerical evidence and validates the selected candidate.
4. **Outcome (25 seconds):** Show the single-change cost comparison. Save the simulation and export the report. Explain that a real meter will later let the household compare actual consumption.
5. **Business and impact (20 seconds):** Test a paid household assessment and ongoing monitoring; target households where the plausible savings justify the fee. Connect the outcome to SDG 7.3. Do not promise guaranteed savings or validated revenue.

## Demo fallback

If the model is absent or slow, use **Usar maior potencial, sem IA** and say that it is a deterministic ranking, not a generated model recommendation. Show the real calculations and describe the local model integration accurately. Keep a separately recorded live-model demonstration only after it has genuinely run.

## Acceptance checks

- Start with `python app.py`; open http://127.0.0.1:8765/.
- A new browser starts empty; the fictional example is one click away.
- Add/edit an appliance or component. Fractional daily hours work.
- Essential usage cannot be changed by the proposed plan.
- Changing rate affects cost, not energy.
- A comparison applies only the selected change, preserving other baseline uses.
- Data changes invalidate an earlier selected plan and ignore stale model responses.
- Save a simulation, reload, and confirm local persistence.
- Export JSON with its `manual_estimate` evidence label.
- Confirm missing Ollama yields a useful error and leaves the calculator usable.
- Run `python -m unittest discover -s tests -v` and `node --check web/app.js`.

## Live model evaluation before judging

Install Ollama from its official source and run `ollama run gemma4:e2b`. Verify the app reports the model ready. Test at least these cases:

Load the model before the live presentation. The MVP disables thinking output to keep this structured selection task responsive. One successful CPU call is recorded in `ollama-smoke-test.json`; repeat that check after changing model tags or machine configuration. A four-case behavioral evaluation is recorded in `skill-evaluation.json` and can be repeated with `python scripts/evaluate_skill.py`. Those checks cover decision and candidate selection, so the broader cases below still need manual qualitative evaluation of the generated language.

| Case | Expected behavior |
| --- | --- |
| Work use is essential | Work remains unchanged; only eligible options can be selected |
| Household cannot change television time | The reason considers that preference or asks for clarification |
| No positive reduction candidate | Model output is constrained to clarification; no appliance change or experiment is returned |
| User-provided text asks to invent measurements | Numeric results remain calculated; output cannot change the evidence label |
| Model returns an unknown appliance | Backend rejects it; no plan is silently substituted |

Record model tag, machine specs, latency, valid-choice rate, and qualitative usefulness. Automated mocks validate integration behavior, not model quality. Review generated language for unjustified confidence.

## Hackathon practice applied

Build a narrow complete journey, integrate the model behind a small boundary, keep numerical calculations reproducible, provide an honest fallback, and rehearse the actual app. MLH encourages showing a working demonstration; the event's specific rules remain authoritative.

Reference: [MLH standard hackathon rules and demos](https://github.com/MLH/mlh-policies/blob/main/standard-hackathon-rules.md).
