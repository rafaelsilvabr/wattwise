# WattWise project brief

## Customer and promise

Initial customer hypothesis: households with substantial discretionary electricity consumption that want to lower spending while preserving the activities they care about.

Promise: **Understand where energy is going, try one achievable change, and see the evidence afterward.**

The project combines social value (more control over household spending), SDG 7.3 (energy efficiency), open-source software, and Gemma as a model for interpreting household context and proposing personalized experiments. Eligibility for prizes follows the organizers' final submission rules.

## Household experience

1. Enter appliance or component watts, estimated hours, household voltage, and a variable energy price. Label the source of the watt figure. A later feature can read a device label or bill photo and ask the user to confirm extracted fields.
2. See estimated consumption and modeled cost per appliance. Highlight which conclusions need more measurement.
3. Tell the agent about constraints: working hours, comfort, budget, and which activities must remain available.
4. Agree on one change. For the demo: a workstation enters a lower-power state overnight, with active work unchanged.
5. See projected consumption. When meter data becomes available, record the intervention time and compare suitable before/after periods.
6. Keep, modify, or reject the change based on both consumption and the household's experience.

Manual entry and simulation are the first deliverables. Measurements from real plugs or meters are a later milestone. Neither manual edits nor generated readings count as verified real-world savings.

## Why use AI

A calculator can perform arithmetic. The agent's intended responsibility is to understand ambiguous appliance descriptions, collect missing assumptions, incorporate household preferences, and propose a feasible experiment using calculated evidence. It must ask for measurements when the inputs cannot support a conclusion.

The web MVP sends household context, up to four follow-up answers, and precomputed eligible changes to local Gemma through Ollama. Gemma selects one change or asks for clarification; the backend rejects a choice outside the candidate set. Protected usage cannot be changed. A calculator-only alternative is clearly labeled. Follow-up answers persist in the browser until household inputs change or the conversation is reset; there is no server-side conversation store. Photo extraction and autonomous device actions are not implemented. A small live evaluation is recorded in `docs/skill-evaluation.json`; repeat model evaluation before a demo on the actual machine.

Future agent tools: estimate household consumption, rank opportunities, inspect interval coverage, compare an experiment, and record household feedback. Arithmetic and energy integration remain deterministic and inspectable.

## Demo and measurement

The example workstation has active, idle, and light-use states. Values are fictional. A proposed sleep state changes the overnight assumption. Manual mode displays projected kWh and BRL; simulated mode integrates generated power intervals over two full days.

Future measured comparisons should use the same appliance and comparable observation durations, account for missing data and meter resets, and record schedule, occupancy, and weather changes when relevant. Simple before/after differences are observational and cannot by themselves establish causation. Report insufficient evidence when comparisons are unsuitable. A short controlled demonstration cannot establish month-long savings.

Product metrics: completed household experiments, measured kWh reduction over eligible windows, retention, willingness to pay, and support time per customer. Do not derive carbon savings without a sourced emissions factor.

## Revenue hypothesis

Start with a paid household assessment and optional ongoing monitoring. Hardware setup could be an additional paid service when supported devices are available. Keep manual entry useful for customers who cannot buy sensors immediately.

The strongest recurring reason to pay would be discovering new consumption changes and following up on outcomes. A static calculator alone is unlikely to support a durable subscription.

Price and demand are unvalidated. Interview households about bills and attempted changes, test a concrete paid offer, and estimate acquisition, model inference, hardware support, and servicing costs. Require plausible customer savings relative to the service fee; do not promise a fixed savings percentage. A success-fee model would require a much stronger attribution method and is outside the MVP.

## Scope

- Now: Portuguese household interface, manual entry, simulation, transparent calculations, local Gemma advisor connector, one-change comparisons, local saved history, export, and focused tests. The original hosted CLI explanation is retained.
- Next: broader live model evaluation, household usability testing, and richer conversational collection of assumptions.
- Later: one meter adapter and real comparison windows. Home Assistant is a possible source, subject to the household's actual devices.

Automatic appliance control, electrical installation advice, utility account integration, and full electricity-bill reconstruction are outside the MVP. Household voltage is descriptive; it is not evidence that a plug, load, or appliance is compatible.
