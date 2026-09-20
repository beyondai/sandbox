---
name: ml-modeling-data
description: Use to profile a dataset before feature engineering — row counts, null rates, class balance, feature distributions, data-quality flags. Step 1 of the ml-modeling-* chain (data → features → train → evaluate). Trigger on "profile this data," "check data quality," or continuing modeling work in an existing ml-<topic>-<n>/ project.
---

# Profile Data

Reads `<project-folder>/design/deep-dive.md`'s Data section (required — see `ml-modeling` router if it's missing). Writes `<project-folder>/modeling/01-data.md`.

Mode: Regular asks about anything the data doesn't make obvious (e.g. why a null rate is high). Quick POC states a reasonable read and moves on — see `ml-modeling` router for the keyword rule.

## Profile

- **Shape**: row count, column count, memory footprint.
- **Nulls**: per-column null rate; flag any column above ~20% as a modeling risk, not just a number to report.
- **Target/label**: class balance (classification) or distribution shape (regression) — this is what decides whether class-imbalance handling matters later.
- **Feature distributions**: numeric columns — min/max/mean/std, skew; categorical columns — cardinality, top values.
- **Quality flags**: duplicated rows, obvious outliers, columns that don't match `design/deep-dive.md`'s stated Data section (a real source drifted from the design, or the design was wrong — either way, surface it, don't silently reconcile).

Done when every flag above is a real number from the actual data (not "looks fine"), and `modeling/01-data.md` states which columns are risky and why — that's what `ml-modeling-features` needs to not repeat this discovery work.
