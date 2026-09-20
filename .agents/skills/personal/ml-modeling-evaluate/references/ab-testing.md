# A/B testing a shipped model

Only relevant once a model is live and being compared against production traffic or a prior model — not part of the offline train/evaluate loop above.

## Sample size

```python
from scipy import stats
import numpy as np

def required_sample_size(baseline_rate, mde, alpha=0.05, power=0.8):
    """N per variant. mde is relative (0.10 = 10% lift)."""
    effect = baseline_rate * mde
    z_a, z_b = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    p = baseline_rate
    return int(np.ceil(2 * p * (1 - p) * (z_a + z_b) ** 2 / effect ** 2))

# required_sample_size(0.05, 0.10) -> ~62,214 per variant
```

## Result analysis

```python
def analyze_ab(control, treatment, alpha=0.05):
    n_c, n_t = len(control), len(treatment)
    p_c, p_t = control.mean(), treatment.mean()
    p_pool = (control.sum() + treatment.sum()) / (n_c + n_t)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z = (p_t - p_c) / se
    p_val = 2 * (1 - stats.norm.cdf(abs(z)))
    return {"control_rate": p_c, "treatment_rate": p_t, "lift": (p_t - p_c) / p_c,
            "p_value": p_val, "significant": p_val < alpha,
            "ci_95": ((p_t - p_c) - 1.96 * se, (p_t - p_c) + 1.96 * se)}
```

Always report effect size alongside the p-value — a large sample makes tiny, practically meaningless differences statistically significant.

## Running it for real

`../../ml-modeling/scripts/hypothesis_tester.py` runs this (plus Welch's t-test, paired t-test, chi-square) against a real CSV:

```
python3 hypothesis_tester.py proportion --successes-a 120 --trials-a 1000 --successes-b 145 --trials-b 1000
python3 hypothesis_tester.py ttest --file data.csv --col-a group_a --col-b group_b
```

Uses only normal/t-distribution approximations (stdlib, no scipy) — fine for fast directional reads; validate with `scipy.stats` before treating a result as publication-grade.
