# KKBOX Recommendation - PRD (Quick POC)

## Problem

Build the best POC recommendation-signal system for the WSDM/KKBOX
repeat-listen prediction task: predict the probability a user will
listen to a given song again within a time window after first
hearing it. The goal is to maximize predictive quality (AUC) on
held-out data for this exercise - it is not tied to a specific
business pain point (e.g. cold start) beyond general
recommendation-quality improvement.

## Requirements - Scope

Must-have: a model that outputs a repeat-listen probability per
(user, song) test-set row, built from KKBOX's provided tables
(train/test, members, songs, song_extra_info, listening logs).

Out-of-scope: real-time/online serving, integration into a live
ranking pipeline, cross-lingual/catalog-specific embedding work,
exploration/bandit logic, and production A/B testing. This stays an
offline exercise against the static historical Kaggle dataset.

## Requirements - Non-functional

No latency/availability SLA - this is offline batch scoring against
a static historical dump, not a live system. Scale is bounded by the
Kaggle dataset size (several million rows for train/test; exact
counts to be confirmed during EDA).

## Metrics - Offline

AUC (area under the ROC curve) between predicted probability and
observed target - this matches the competition's own evaluation
metric directly, so no separate proxy metric is needed.

## Metrics - Online

N/A for this POC - there is no live system to A/B test against. If a
version of this model were ever shipped into a real recommender, the
online metric would be repeat-listen rate or session-time lift, with
skip rate / negative-feedback rate as a guardrail that must not
regress.

## Team

No real organizational stakeholders - this is a solo practice
project. For realism, the hypothetical stakeholder set is a
personalization/recommendation team (owns the production ranker this
would feed into) and data engineering (owns the listening-log
pipeline this dataset is sampled from).

## Team - Reuse

Not considered for this POC - standalone exercise, no defined reuse
target or downstream consumer.

## Change log

- 2026-09-20: initial PRD written from the Quick POC grilling
  interview.
- 2026-09-20: file was found deleted from disk after the monkey-mode
  background agent ran (design/high-level.md and the ADR survived
  untouched). Recreated verbatim from this conversation's record of
  the original content. Root cause and a proposed fix logged in
  SKILL-IMPROVEMENTS.md.
