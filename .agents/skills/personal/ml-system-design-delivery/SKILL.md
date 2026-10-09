---
name: ml-system-design-delivery
description: >-
  Use when writing or reviewing the Delivery section of an ML system design doc
  - execution timeline, deployment/rollout/testing strategy, A/B test and
  offline eval methodology, production monitoring, retraining triggers and
  owner, or fallback plans. Trigger on requests to design a rollout/ramp plan,
  an A/B test, a monitoring dashboard, a retraining plan, or a
  fallback/kill-switch for an ML system going to production.
---

# Delivery

Writes `<project-folder>/design/delivery.md`, one heading for each item.

Rules: `../ml-system-design/SKILL.md`, "Project folder", "Output docs",
"Check the output", "Skill improvement log".

## Modes

- **Regular draft:** answer each item in the user's own numbers and
  words. Ask when a fact is unknown. Do not invent.
- **Quick POC draft** (keywords: "Regular and Quick-POC mode" in
  `../ml-system-design/SKILL.md`): give the most
  likely answer to each item in one pass, marked as an assumption.
- **Review:** check that each item has a real answer. Report the gaps. Do
  not rewrite what is good.

## Checklist

- **Fallback** (reviews skip it most often: do it first). What happens
  when the new model or service fails or gets worse: go back to the prior
  model, or to a simple heuristic. The default heuristic is the PRD's
  recommended baseline (Definition, "Baseline"). Name it, or say why it
  cannot serve. Give the trigger and the target. A doc without a fallback
  is not complete.
- **Execution:** epics or milestones with dates; the team process (for
  example sprint length, review cadence).
- **Deployment:** the rollout plan (ramp %, schedule), the test plan
  (unit, integration, load), CI/CD.
  - When the quality is partly subjective (the user experience), put an
    internal or opt-in stage before the random ramp. It collects feedback
    and tests the guardrails before random users see the model
    (`../ml-design-principles.md`, Principle 3).
  - The serving design comes from the route, like Eval: hands-on,
    `modeling/05-serve.md` and `.json`; paper, the Serving section of
    `design/deep-dive.md`. Cite it; do not design serving again here.
  - The load test runs at the peak QPS with the replica count from
    Serving (or the batch job inside its window). That is its pass
    target. Reason: it proves the capacity plan before users see it.
- **Eval:** the A/B test design and the significance method; the offline
  method (for example a held-out window).
  - Hands-on route: use the real results in `modeling/04-evaluate.md`.
  - Paper route: build on the Training section of `design/deep-dive.md`.
  - Neither exists: say so in the file. Regular asks the user. Quick POC
    uses the evaluation plan in `design/high-level.md`, marked as an
    assumption.
- **Monitoring:** system health (latency, error rate) and model health
  (prediction distribution, feature drift) on a live dashboard. Start the
  latency thresholds from the stage budgets in Serving.
- **Retraining:** the triggers (drift, and each scheduled upstream change
  from Training in `design/deep-dive.md` or `modeling/03-train.md`), the
  owner after launch, and the runbook
  that the owner runs without the model authors. Reason: a model that
  only its authors can retrain stops being updated.

## Offer an ADR

Offer an ADR in `<project-folder>/adr/000N-*.md` for a rollout or
fallback strategy that is hard to reverse, would surprise a future
reader, and was a real trade-off.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Does the fallback name its trigger and its target?
2. Does the rollout have a concrete ramp schedule?
3. Does monitoring list specific metrics, each with a threshold, not "we
   will monitor performance"?
4. Does the A/B test name its metric (the PRD online metric), its
   randomization unit, and its duration or power?
5. Does the load test name its target: the peak QPS and the replica
   count (or the batch window) from Serving?
6. Does retraining name each trigger, scheduled changes included, and
   the owner after launch?

Done when the 6 answers are yes and `check_doc.py` prints `OK`.
