# Batch scoring stands in for online inference

The high-level design's "online inference" diagram is not a live
request/response API - it's the one-shot batch path that scores all of
`test.csv` and produces a Kaggle submission file. This project has no
real users and no live traffic, so there is nothing to serve online in
the literal sense. A future reader of `design/high-level.md` who expects
"online inference" to mean a deployed, request-scoped service would be
misled without this note, since the design doc's structure (two
diagrams, one labeled online) otherwise implies a real serving path
exists.

## Considered options

- **Design a hypothetical production serving path** (e.g. a REST
  endpoint scoring one customer at a time, as if this were a real
  telecom's churn system): matches the letter of the high-level skill's
  "online inference" diagram more literally, and would be closer to
  interview-prep practice for a production ML system design question.
  Rejected for this project because the PRD explicitly scopes this as a
  one-shot Kaggle submission with no live system (Requirements - scope
  and Metrics - online both say N/A), and inventing a fictional serving
  path would contradict the PRD rather than build on it.
- **Omit the "online inference" diagram entirely** since it doesn't
  apply: rejected because the high-level skill requires both diagrams,
  and skipping it silently would look like an oversight to a future
  reader rather than a deliberate scoping choice.
- **Repurpose "online inference" as the batch-scoring / submission path**
  (chosen): keeps the two-diagram structure the skill expects, stays
  faithful to what this project actually does (batch score `test.csv`,
  produce `submission.csv`, submit to Kaggle), and is called out
  explicitly here so it reads as an intentional framing choice rather
  than a misunderstanding of what "online" means.
