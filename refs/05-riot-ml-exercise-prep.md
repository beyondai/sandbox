# 05 — Riot Live ML Exercise: Player Intelligence & Personalization (v2.1)

**Role:** Senior Principal Machine Learning Engineer — Player Intelligence & Personalization
**Round:** live, ~60 min, "implement a well-known system from scratch" with your own agentic tools; 1:1 with Austin Frank
**Time left:** Tue Sep 15 (today), Wed, Thu — about 12–13 focused hours
**Changes in v2:** re-anchored on the JD and the hiring manager's signal (retention/churn and LTV); de-emphasized matchmaking and toxicity; dropped the GitHub-based read on Austin; added a new `lifecycle` dataset with a randomized offer campaign and exact counterfactuals.
**Changes in v2.1:** added a full recommendation and ranking set (R1–R4), since that's common ground between your background and Austin's; added a storefront impression log with position bias to the `shop` data; fixed v2's broken pointer to v1's recommendation section.

Companion files: `riot_practice_data.py` (generator), `12-Day_Prep_Plan` (CLAUDE.md, prompts/, rep loop, interview-day routine all still apply).

---

## 0. TL;DR

1. **The problem will most likely come from the JD's core list.** Churn, player revival, LTV, and offer optimization / next-best-action are the top priors, because the HM named churn and LTV explicitly.
2. **Churn and LTV are one problem viewed two ways.** "Is this player still alive?" and "how much will they spend while alive?" are two factors of the same value model. Prepare them as a connected pair, not two separate topics.
3. **Next-best-action is where the JD's causal-inference line gets tested.** The target is not "who is most likely to churn" but "who changes behavior *because* of the action." Expect to be asked to separate these.
4. **Well-known systems to own:** a discrete-time hazard model; BG/NBD with Gamma-Gamma (the classic CLV model); a ZILN / two-part LTV model; two-model and transformed-outcome uplift; and IPW policy evaluation. The formula sheet is in §6.
5. **Recommendation and ranking is the other likely pool.** It's in the JD and it's shared ground between your search-ranking background and Austin's recommendations background, so he can probe it deeply. The canonical from-scratch systems are matrix factorization and item-to-item collaborative filtering; the principal-level depth is position bias and counterfactual evaluation (R1–R4).
6. **Your differentiator is unchanged:** evaluation designed before modeling, two kinds of verification (is the code right, is the model good), and simulation with known truth. The new dataset even has exact counterfactuals, so you can score an uplift model against the true effect.

---

## 1. What changed and why

### The JD, mapped to what can be tested live

| JD line | What a 60-minute exercise could ask | Rep |
|---|---|---|
| "churn prediction, player revival, player lifetime value" | Predict lapse among active players; predict return among lapsed players; forecast 90-day value | L1, L2 |
| "offer optimization, and next-best-action models" | Decide who should get an offer, using a logged randomized campaign | L3 |
| "recommendation systems, content optimization" | Rank store items per player; "similar items"; learn a ranker from click logs; choose home-screen content | R1–R4 |
| "player representation … lifecycle state … long-term player value" | Engineer lifecycle-state features; use factor vectors as player embeddings | L1, R1 |
| "experimentation, measurement, causal inference, and evaluation" | Online test design; uplift; why a predictive score is not a treatment policy | L3, and the close of every rep |
| "move between hands-on technical execution and organization-level technical leadership" | The exercise itself: build it, then explain what you'd standardize | Every close |

This JD is **not** about matchmaking or toxicity. Those drop to "skip unless time."

### What we know about the interviewers

- **Hiring manager (not your interviewer).** Named retention/churn and LTV as important topics. The HM probably shaped the problem pool even if they're not in the room, so the framing may come in HM terms (retention, value, lifecycle) while the probing comes in Austin's terms.
- **Austin Frank (your interviewer).** Director of Data Science and Engineering at Riot, previously a data scientist on recommendations at Amazon, with an experiment-design background. **His public GitHub activity is old, so don't infer current interests from it; disregard that lead in the 12-day plan.** Rely on what's current: he leads a data science and engineering org and has recommendations experience. Expect him to probe evaluation, experiment design, and whether you understand your own code.

---

## 2. Problem space, re-ranked

### Tier A — full reps (must do)

| Rep | What you might hear | Well-known systems to build | Primary evaluation |
|---|---|---|---|
| **L1** Churn and revival | "Too many players are drifting away. Figure out who's at risk and who might come back." | Logistic regression → discrete-time hazard model; a separate revival model for lapsed players | PR-AUC, calibration, precision in the top decile — reported on the decision-relevant population |
| **L2** LTV | "Finance and live-ops want a forward-looking value for every player." | BG/NBD + Gamma-Gamma; two-part (hurdle) or ZILN model | Normalized Gini, decile calibration, aggregate revenue error, top-decile capture |
| **L3** Offer / next-best-action | "We ran a comeback offer last quarter. Who should get it next time?" | Two-model uplift; transformed-outcome uplift; IPW policy value | Uplift curve, policy value versus treat-all and treat-none, and true effect (sim only) |

### Tier A2 — recommendation and ranking (shared ground with Austin)

| Rep | What you might hear | Well-known systems to build | Primary evaluation |
|---|---|---|---|
| **R1** Store personalization | "Show each player skins they'll actually want." | Implicit-feedback matrix factorization (ALS or BPR) | Temporal split; Recall@k and nDCG@k against popularity and "most-played champion" baselines |
| **R2** Learning-to-rank from click logs | "Here are our store impression logs. Build a better ranker." | Pointwise logistic → pairwise (RankNet / BPR-style); position-bias estimation; IPS | Exact expected purchases (sim); position-bias curve against truth; offline evaluation on randomized traffic |
| **R3** "Players who bought this also bought" | "Add a similar-skins row to the item page." | Item-to-item collaborative filtering (the classic Amazon approach) | Next-purchase hit rate@10 against popularity and same-champion baselines |
| **R4** Home-screen content choice | "Which event tile should we show each player?" | Multi-armed and contextual bandits (Thompson sampling) | Regret on a simulator you write; offline evaluation needs logged propensities |

R1 is the full rep. R3 is a 20-minute rep and your interview-morning warm-up. R2 is a talk-through with one small hands-on slice. R4 is talk-through only.

### Tier B — compressed rep or talk-through

- **Contextual-bandit version of L3.** Thompson sampling over offer variants; know when a bandit beats a one-shot uplift model.
- **Early LTV** (predict 90-day value from a player's first 7 days). Same machinery as L2, different population. The lifecycle data has new signups through day 179.
- **Lifecycle segmentation.** Hand-defined states (new / active / at-risk / lapsed) versus learned ones (clustering or a hidden Markov model).

### Tier C — skip unless everything else is done

Matchmaking and toxicity (covered in v1, removed in v2 because this JD doesn't mention them; the `ranked/` and `newplayer/` data are still generated if you want them), and ML internals (the 12-day plan's reps).

### Minute-one clarifier (unchanged)

*"I'll write the core model and metrics myself. Is it fine to use sklearn, scipy, or lifetimes for baselines and as a reference to check my implementation?"*

---

## 3. Workflow (same shape as v1, lifecycle-specific details)

| Min | Phase | For lifecycle problems specifically |
|---|---|---|
| 0–5 | **Frame** | What action follows? Who gets it, through which surface, at what cost? Over what horizon does value count? |
| 5–10 | **Define success** | Pick the cutoff date, the label window, the population, the primary metric, and the baseline. Write them into `spec.md`. |
| 10–17 | **Data contract** | What is one row? Does inactivity mean churn? Are any players contaminated by a past campaign? When do content events happen? |
| 17–22 | **Baseline + harness** | Recency-only for churn; "last 90 days of spend" for LTV; treat-all and treat-none for offers |
| 22–42 | **Core system in slices** | Test first; read each diff aloud; run the reviewer; commit |
| 42–48 | **Evaluate + slices** | New vs established players; payer vs non-payer; social vs solo |
| 48–53 | **One iteration** | One hypothesis, chosen from the error analysis |
| 53–60 | **Close** | What you'd ship, what you don't trust, the online test, how it becomes a platform capability |

### Framing questions for lifecycle problems

1. **What action does this score drive, and what does the action cost?** (Discount, reward, email/push, or a content change.)
2. **What does "churned" mean here?** Inactive for N days, or never returns? Games have *revival*, so churn is a latent state, not an observed event.
3. **Over what horizon, and at what moment?** (Score every day, or once per week? A 28-day churn window? 90-day value?)
4. **Which population?** (Recently active players for lapse risk; inactive players for revival; payers or everyone for LTV.)
5. **Is any data contaminated by past interventions?** (Players in a past campaign behave differently after it.)

### Backtesting with cutoffs (the split that matters here)

For each cutoff c: features use only days < c; labels come from days [c, c + H).

- **Train at an earlier cutoff, test at a later one**, with c_train + H ≤ c_test so that no training label overlaps the test window.
- **Watch seasonality.** A cutoff that falls inside a content event behaves differently from one that doesn't. Check the content calendar, or average over several cutoffs.
- **Exclude treated campaign players** from churn and LTV evaluation after the campaign starts, or use a cutoff before it.
- **For uplift,** the randomization *is* the split you need. Hold out a random share of campaign players for evaluation.

---

## 4. Agent setup (minimal version for your time budget)

Keep everything from v1 §4, but with 11 hours, **build only these three things:**

1. **CLAUDE.md applied-ML block** (v1 §4.3). Add one line: `For lifecycle data: features strictly before the cutoff, labels in [cutoff, cutoff+H); exclude treated campaign players from non-causal evaluation.`
2. **`spec_template.md` in `prompts/`** (v1 §4.4). Add fields: `Cutoff(s):`, `Horizon H:`, `Population:`, `Action + cost:`.
3. **The `ml-reviewer` subagent** (v1 §4.5). Add check 5: `Label window overlaps a training feature window, or campaign-treated players leak into non-causal evaluation.`

Only if time remains Thursday, convert the eval rules into the `eval-harness` skill, updated for this role:

```markdown
- Churn/revival: PR-AUC, 10-bin calibration, precision@top-decile; report on the
  decision-relevant population, not all players.
- LTV: normalized Gini, decile table (mean predicted vs mean actual), total revenue error,
  share of revenue captured by the top-decile prediction; always beside "last-period spend."
- Ranking: Recall@k and nDCG@k beside popularity and a domain heuristic; exclude owned and
  unreleased items; state whether the evaluation re-ranks a shown slate or the full catalog.
- Uplift: uplift curve and IPW policy value vs treat-all and treat-none. Scoring against true
  ITE is allowed only in eval/recovery.py and only when I ask.
```

**Pre-install and verify before tonight's rep:** `scipy` (special functions and optimizers), `scikit-learn`, and `lifetimes` as the BG/NBD reference. `lifetimes` is an older package, but in my test it still installed and fit cleanly on current numpy and pandas. Check it with the known-answer test: fitting BG/NBD to its bundled CDNOW summary data should give r ≈ 0.243, α ≈ 4.414, a ≈ 0.793, b ≈ 2.426. Your own implementation must reproduce those numbers. That is the best correctness test available for L2.

**Updated 60-second setup answer:** same as v1 §4.8. When you get to verification, add: *"For the classic models I check against a published known answer — BG/NBD on the CDNOW data has published parameters, so my implementation has to reproduce them."*

---

## 5. Practice set

Generate data: `uv run python riot_practice_data.py --out data/sim --seed <n> --only lifecycle` (and `--only shop` for R1–R3). Use a new seed for every rep. **Don't read §8 (spoilers) until you've done the rep.**

### The `lifecycle` dataset

| File | Contents |
|---|---|
| `players.csv` | signup day, region, platform, acquisition source |
| `activity.csv` | one row per player-day played: games, wins, party games, minutes (days 0–269) |
| `purchases.csv` | player, day, amount, item type, whether it was bought at offer price |
| `campaign.csv` | a randomized 50/50 comeback-offer campaign sent on day 180 to a sample of players who signed up by day 150 |
| `content_calendar.csv` | start days of content events (known in advance, so legitimate as features) |
| `_truth/` | latent traits, true lifecycle state at day 180, and **both potential outcomes** for every campaign player |

---

### L1 — Churn and revival (Tuesday)

**Prompt:** "Too many players are drifting away. Figure out who's at risk and who might come back."

**What to build:**
1. **Baseline:** recency (days since last played) alone.
2. **Lapse model** for players active in the last 7 days: logistic regression from scratch (gradient descent + L2) on features from the last 28 days: active days, games, win rate, recent loss rate, party share, tenure.
3. **Discrete-time hazard formulation** (stretch): one row per player-day, label = "this is the day they stopped," logistic link. Explain why this handles censoring.
4. **Revival model** for currently inactive players: who returns within 28 days? Try including content-event timing.

**Clarifying questions:** What will we do with the scores, and at what cost? How many days of inactivity count as churn? Should we score daily or weekly? Are campaign players excluded?

**Evaluation:** backtest with train cutoff 135 and test cutoff 180 (H = 28), excluding treated campaign players. Report PR-AUC, calibration, precision in the top decile, and slices (new vs established, social vs solo).

**Framing traps this data is built to catch:**
- Reporting AUC on *all* players, where "played recently" makes the task look nearly solved.
- Treating inactivity as churn.
- Train and test cutoffs in different seasonal conditions.
- Leaving treated campaign players in the evaluation after day 180.

**Correctness checks:** gradient check against finite differences; coefficients match sklearn with the same penalty; label-construction unit tests on hand-made activity logs (for example, active on days 0–3, then day 40 → "churned" at cutoff 10 with H = 28, and "not churned" with H = 35).

**Probes to rehearse:**
- "Recency alone is almost as good. Why build a model?" (Lift in the top decile at a fixed budget, calibration, and interpretable drivers for the action.)
- "Why a hazard model?" (Censoring, and time-varying covariates.)
- "Loss streaks predict lapse. Should we change matchmaking?" (That's correlation; you'd test it.)
- "How does this become a platform capability?" (A shared player-state feature table, a standard label definition, and a backtesting harness other teams reuse.)

---

### L2 — LTV (Wednesday morning)

**Prompt:** "Finance and live-ops want a forward-looking value for every player. Build it."

**What to build:**
1. **Baseline:** spend in the last 90 days, used as the forecast for the next 90.
2. **BG/NBD + Gamma-Gamma from scratch** (the classic CLV system):
   - Fit BG/NBD by maximum likelihood with `scipy.optimize` on log-parameters.
   - Pass the CDNOW known-answer test first, then fit on game data.
   - Game translation: you can model "transactions" as purchases, or model active days and multiply by purchase rate and average amount. Choosing between these is a framing decision worth saying out loud.
3. **Two-part (hurdle) / ZILN model:** P(spend > 0) from logistic regression, times E[spend | spend > 0] from a linear model on log spend. Note that with linear heads, ZILN *is* this two-part model; a neural network shares the representation between the parts.

**Clarifying questions:** Is this 90-day revenue or lifetime? Gross or net of refunds? Who consumes it — finance needs accurate totals, targeting needs accurate ranking? New players or everyone?

**Evaluation:** cutoff 90 for training (labels days 90–179) and cutoff 180 for testing (labels 180–269, treated players excluded). Report normalized Gini (ranking), the decile table and decile MAPE (calibration), total revenue error (finance), and top-decile revenue share (targeting).

**Correctness checks:** CDNOW parameters reproduced; P(alive) equals 1 for players with no repeat transactions (the model's convention); BG/NBD expected transactions close to `lifetimes` on the same inputs; a ZILN loss test on hand-computed rows; E[y] = p·exp(μ + σ²/2) checked numerically by sampling.

**Talking points:**
- **Misspecification.** BG/NBD assumes dropout is permanent, but games have revival around content events. Where does that make P(alive) wrong, and how would you fix it (for example, a hidden-Markov "buy till you die" variant, or a discriminative model with event features)?
- **Heavy tails.** A few players bring in most revenue. MSE chases whales; that's why ZILN or two-part models, and why you report ranking and calibration separately.
- **Gamma-Gamma assumes spend amount is independent of purchase frequency.** Check that assumption on the data before using it.

**Probes:** "Would you use this to allocate marketing budget?" (Only with uplift — see L3.) "How would you validate LTV when the true horizon is a year?" (Shorter-horizon proxies, cohort backtests, and tracking drift of predicted versus realized value.)

---

### L3 — Offer optimization / next-best-action (Wednesday afternoon)

**Prompt:** "We ran a comeback offer last quarter. It looked flat overall. Who should get it next time?"

**What to build:**
1. **Read out the experiment first:** difference in means for 90-day revenue and 30-day return, with standard errors. Say what "flat" means statistically.
2. **Two-model uplift from scratch:** fit outcome models separately on treated and control players; the uplift estimate is the difference.
3. **Transformed-outcome uplift:** regress Z = 2Y·(2T − 1) on features (valid because randomization gives e = 0.5).
4. **Policy:** treat a player if estimated uplift exceeds the offer's cost; compare policy value against treat-all and treat-none using IPW.

**Clarifying questions:** What does the offer cost us (discount margin, reward cost, fatigue)? Is the goal revenue, retention, or both? Is there a budget cap? Can we run a follow-up test?

**Evaluation:** a random 50% of campaign players held out. Report the uplift curve, IPW policy value, and — in the simulation only — the correlation between your estimate and the true effect, plus the true value of your policy.

**What this rep is built to teach (say these out loud):**
- **"Highest churn risk" is not "highest uplift."** Some players can't be won back at all, and some would have spent anyway.
- **A discount can lose money** among players who would have paid full price (cannibalization and pulling purchases forward).
- **A flat average effect can hide a strongly positive targeted policy.**
- **Heterogeneity estimates are noisy at this sample size.** Say so, and propose a confirmatory test for the targeted policy.

**Correctness checks:** unit-test the IPW policy value on a tiny hand-built table; a sanity check that both treat-all and treat-none values match simple group means; the transformed-outcome estimator's average matches the difference in means (exactly when the groups are equal size; otherwise use the observed treated share as e).

**Probes:**
- "Why not just target the churn model's top decile?"
- "When would you use a contextual bandit instead?" (Many offer variants, continuous learning, and a willingness to explore.)
- "How do you evaluate a new policy offline without running it?" (IPW or doubly robust estimation on logged randomized data.)
- "What's the long-term risk?" (Training players to wait for discounts; measure it with a long-running holdout.)

---

## 5b. Recommendation and ranking set

### The `shop` dataset

| File | Contents |
|---|---|
| `items.csv` | 400 skins: champion, price tier (1–4), release day |
| `champion_play.csv` | games played per player per champion (dense taste signal) |
| `purchases.csv` | organic purchases: player, item, day (sparse, about 6 per buyer; about 30% of players never buy) |
| `impressions.csv` | 40k storefront sessions × 6 slots: bucket, position, item, clicked, purchased |
| `_truth/` | player and item latent factors, item quality, and the exact click and purchase model (`storefront_params.csv`) |

**About the impression log.** Two traffic buckets:
- **`prod` (85%)** ranks eligible items by recent global popularity. It isn't personalized and isn't randomized.
- **`explore` (15%)** shows 6 random eligible items in random order.

A click requires that the player *examined* the slot (which depends on position) and was *attracted* to the item (which depends on player and item). A purchase happens only after a click. Because the true model is in `_truth/`, you can compute the **exact expected purchases** of any ranking you produce (formula in §6). That's the sim-only gold standard, which you can compare against your offline metric.

---

### R1 — Store personalization with matrix factorization (Thursday, full rep)

**Prompt:** "We want the store to show each player skins they'll actually want. Build a first version."

**What to build:**
1. **Baselines:** global popularity, and "popular skins for your most-played champions."
2. **Implicit ALS from scratch** (confidence-weighted; closed-form user and item steps). BPR with SGD is the alternative if you'd rather show a pairwise loss.
3. **Iteration:** bring the dense champion-play signal *into* the model — for example, factorize champion play and map skins through their champion, or add play as down-weighted extra interactions. Don't just blend scores at the end.

**Clarifying questions:** Is the goal clicks, purchases, or revenue? How many slots? Should owned or unreleased items be excluded? What about players who have never bought? Is this for the store page or a push message?

**Evaluation:** train on purchases before day 70 and test on later ones. Exclude owned items and items not yet released. Report Recall@10 and nDCG@10 against both baselines, plus catalog coverage and slices for cold versus warm players. Stretch: re-rank each test storefront session's full candidate set and score it with exact expected purchases.

**Correctness checks:** each ALS half-step never increases the weighted loss; on a tiny matrix, the user step matches `numpy.linalg.lstsq` on the confidence-weighted system; hand-check Recall@k and nDCG@k on a 5-item example; unit-test owned-item exclusion.

**The insight to say out loud:** with about 6 purchases per buyer, MF on purchases alone can lose to a well-chosen domain heuristic. Say so plainly, then explain how you'd bring the denser signal into the model. Also: **factor vectors are player representations** that can feed churn and LTV models as behavioral-similarity features — the JD's "player representation" line.

**Probes to rehearse:**
- "Why ALS rather than SGD?" (Closed-form steps, easy to parallelize, and it handles implicit confidence weighting over all unobserved entries.)
- "What does the confidence weight α do?" (How much a purchase counts relative to an unobserved pair.)
- "Offline recall went up. Would you ship?" (The logs only reflect what was exposed, so there's exposure bias. Validate online on purchases, revenue per impression, and refunds.)
- "How do you handle a brand-new skin?" (Content features from its champion and tier, plus exploration — see R4.)
- "How would this run for every player daily?" (Batch factors, approximate nearest-neighbor retrieval, then a re-ranking stage — your Target experience applies directly here.)

---

### R2 — Learning-to-rank from storefront logs (Thursday, talk-through + one slice)

**Prompt:** "Here are six weeks of store impression logs. Build a better ranker."

**Hands-on slice (15–20 minutes): estimate position bias.** Using only the `explore` bucket, compute CTR by position divided by position-1 CTR, with bootstrap intervals. Compare it to the `prod` bucket's curve and to the truth. Explain why only the randomized traffic gives an unbiased estimate.

**What you'd build with a full hour:**
1. **Features** you construct from raw tables: player's games on the item's champion, popularity before the session day, price tier, item age, how many skins of that champion the player already owns, and the R1 MF score.
2. **Pointwise logistic ranker** from scratch. Correct for position either by including position as a training feature and fixing it to slot 1 at scoring time, or with inverse-propensity weights from the estimated examination curve.
3. **Pairwise ranker** (RankNet loss on clicked-vs-skipped pairs within a session), with the LambdaRank weighting as a talking point.
4. **Target choice:** clicks versus purchases. Price tier lowers both, but the store cares about purchases.

**Evaluation:** train on sessions before day 70 and test after. Offline, use the explore bucket for less biased estimates. In the sim, re-rank each test session's *full* candidate set and score it with exact expected purchases.

**What this data teaches:**
- Because `prod` puts popular items on top, position and popularity are confounded. A naive model trained on `prod` clicks gives popularity more weight than a debiased one.
- Re-ranking only the 6 shown items is a much easier problem than ranking the whole eligible catalog. Be clear about which one you're evaluating.
- **Check whether debiasing actually changes ranking quality before claiming it does.** In this data it mostly corrects a coefficient. It matters more when the logging policy is personalized on the very features you're learning.

**Probes to rehearse:**
- "Why not just train on clicks?" (Position bias, presentation bias, and clicks not being purchases.)
- "How would you estimate position bias without an exploration bucket?" (Swap interventions, randomizing adjacent pairs, or EM on a click model — with the tradeoff of how much randomization product will accept.)
- "How do you evaluate a new ranker offline without an A/B test?" (IPS or doubly robust estimation on randomized traffic, interleaving as a fast online check, then a real A/B test.)
- "Pointwise, pairwise, or listwise?" (Pairwise and listwise optimize ordering directly; pointwise gives calibrated scores you can combine with value.)

---

### R3 — Item-to-item "players who bought this also bought" (20-minute rep; Friday warm-up)

**Prompt:** "Add a 'similar skins' row to each item page."

**Build:** a binary co-purchase matrix → cosine similarity between items → top-k neighbors per item, excluding items the player already owns. This is the item-to-item collaborative filtering approach Amazon popularized; it scales because similarity is computed offline per item.

**Evaluation:** for each purchase after day 70, use the player's most recent earlier purchase as the anchor, and check whether the next purchase is in the anchor's top 10 neighbors. Compare against popularity and "same champion."

**Points to make:** normalization matters (raw co-counts just rediscover popular items); similarity learned from behavior alone recovers the champion structure without being told; the approach needs a fallback for sparse or new items.

---

### R4 — Home-screen content choice with bandits (talk-through only)

**Prompt:** "We have 8 event tiles for the home screen. Which one should each player see?"

**If asked to build:** write a small simulator (8 arms with hidden click rates, optionally per segment), then implement epsilon-greedy and Beta-Bernoulli Thompson sampling, and plot cumulative regret. Contextual version: a per-segment Thompson sampler or a logistic model with Thompson draws.

**Points to make:**
- **When a bandit beats an A/B test:** many options, short-lived content, and a cost to showing losers.
- **Offline evaluation needs logged propensities.** Without randomization in the logs, you can't evaluate a new policy offline. This connects back to R2's explore bucket and L3's IPW.
- **Guardrails:** don't let short-term clicks override long-term engagement; cap exposure for fairness to new content.

---

## 5c. Thursday dress rehearsal (combined, unseen framing)

Ask your rehearsal partner to read you one of these at t = 0:

- "We have budget to send a comeback offer to 20% of players next month. Who gets it?"
- "Predict the 90-day value of players who signed up last week, using only their first 7 days."
- "Season start is in two weeks. Which lapsed players are most likely to come back, and should we nudge them?"
- "Our store ranking is just popularity. Build something personalized and show me it's better." (Uses `shop/`.)

---

## 6. Formula sheet (understand these; don't memorize)

**Discrete-time hazard.** One row per player-period while at risk; y = 1 in the period the player lapses. h(t|x) = σ(βᵀx_t). Survival S(t) = ∏(1 − h). Censored players contribute only zeros, which is how censoring is handled.

**BG/NBD** (Fader, Hardie & Lee, 2005). While alive, transactions arrive as Poisson(λ) with λ ~ Gamma(r, α). After each transaction the customer drops out with probability p ~ Beta(a, b). Per-customer inputs: x = repeat transactions, tₓ = time of the last one, T = time observed.

```
L = B(a, b+x)/B(a, b) · Γ(r+x) αʳ / Γ(r) · [ (α+T)^-(r+x) + 1{x>0} · a/(b+x−1) · (α+tₓ)^-(r+x) ]
P(alive | x, tₓ, T) = 1 / ( 1 + 1{x>0} · a/(b+x−1) · ((α+T)/(α+tₓ))^(r+x) )
```

Fit by minimizing the negative log-likelihood (using `gammaln` and `betaln`) over log-parameters. Expected future transactions uses a hypergeometric function (`scipy.special.hyp2f1`); use `lifetimes` as the reference for that piece.

**Gamma-Gamma spend model.** Expected average spend for a customer with x transactions and mean spend m̄:

```
E[M | x, m̄] = p · (γ + x·m̄) / (p·x + q − 1)
```

It's fit on repeat customers only, and it assumes spend is independent of frequency.

**CLV** ≈ expected transactions over the horizon × expected spend per transaction (optionally discounted).

**ZILN** (Wang, Liu & Miao, 2019). y = 0 with probability 1 − p; otherwise y ~ LogNormal(μ, σ).

```
NLL = −1{y=0}·log(1−p) − 1{y>0}·[ log p − log y − log σ − ½·log 2π − (log y − μ)² / (2σ²) ]
E[y] = p · exp(μ + σ²/2)
```

With separate linear heads, this reduces to logistic regression for p plus least squares on log y, with σ estimated from the residuals.

**Normalized Gini.** Sort players by predicted value and compute the Gini of actual value captured along that ordering. Divide by the Gini you'd get sorting by actual value. A value of 1 means a perfect ranking.

**Decile calibration.** Bucket players by predicted-value decile, then compare mean predicted to mean actual within each bucket (and compute MAPE across buckets).

**Uplift.** τ(x) = E[Y | T=1, x] − E[Y | T=0, x].
- Two-model estimate: τ̂ = μ̂₁(x) − μ̂₀(x).
- Transformed outcome: Z = Y·(T − e)/(e(1 − e)), which satisfies E[Z | x] = τ(x). With e = 0.5, Z = ±2Y.

**IPW policy value** of a policy π on randomized data with propensity e:

```
V̂(π) = mean( Y · 1{T = π(x)} / P(T = π(x)) )     # with e = 0.5: 2·mean(Y · 1{T = π(x)})
```

Compare against V̂(treat-all) and V̂(treat-none). Net out the offer's cost if it isn't already reflected in Y.

### Recommendation and ranking formulas

**Implicit ALS** (Hu, Koren & Volinsky, 2008). Preference p_ui = 1 if the player bought the item, else 0. Confidence c_ui = 1 + α·r_ui.

```
minimize  Σ_u,i c_ui (p_ui − x_uᵀ y_i)² + λ (Σ‖x_u‖² + Σ‖y_i‖²)
x_u = (YᵀY + Yᵀ(Cᵘ − I)Y + λI)⁻¹ Yᵀ Cᵘ p(u)      # item step is symmetric
```

The YᵀY term is shared across users, which is what makes each step cheap.

**BPR** (Rendle et al., 2009). Sample (player u, bought item i, not-bought item j):

```
maximize  Σ log σ(x̂_ui − x̂_uj) − λ‖Θ‖²
```

**Item-to-item cosine** on a binary player × item matrix:

```
sim(i, j) = |buyers(i) ∩ buyers(j)| / sqrt(|buyers(i)| · |buyers(j)|)
```

**Ranking metrics.** Recall@k = (relevant items in the top k) / (all relevant items).

```
DCG@k = Σ_{r=1..k} rel_r / log2(r + 1)
nDCG@k = DCG@k / (DCG@k of the ideal ordering)
```

**Position-based click model.** P(click | item i at position k) = θ_k · γ_ui, where θ_k is the chance the slot is examined and γ_ui is attractiveness.
- With randomized placement, CTR_k is proportional to θ_k, so θ_k/θ_1 = CTR_k / CTR_1 on the explore bucket.
- IPS correction: E[click / θ_k] = γ_ui, so each click is weighted by 1/θ_k.

**RankNet and LambdaRank.**

```
P(i ≻ j) = σ(s_i − s_j)
loss      = −log σ(s_i − s_j)          # for pairs where i was clicked and j was skipped
```

LambdaRank scales each pair's gradient by |ΔnDCG| from swapping i and j.

**Exact expected purchases** (sim only, using `_truth/`). With aff = U_u·V_i / √8:

```
E[purchases | ranking π] = Σ_k θ_k · σ(1.0·aff + quality_i − 0.25·tier_i − 3.0) · σ(0.8·aff − 0.3·tier_i − 1.2),  with i = π_k
```

**Thompson sampling (Bernoulli).** Each arm has a Beta(1 + clicks, 1 + non-clicks) posterior. Each round, draw one sample per arm and show the arm with the highest draw.

---

## 7. The 3-day plan (about 12.5 hours)

**Tue Sep 15 — about 4 hours**
- **1.0h Setup:** both agents working; repo; the CLAUDE.md block; `spec_template.md`; the reviewer subagent; generate data; install scipy, sklearn, and lifetimes; run the CDNOW known-answer check.
- **2.5h L1 churn and revival:** 60-minute timed rep, 30-minute learning pass (hand-rewrite the logistic gradient step), and time for friction.
- **0.5h:** read §6 for BG/NBD and uplift; sketch the likelihood on paper.

**Wed Sep 16 — about 4.5 hours**
- **2.25h L2 LTV:** get the CDNOW test passing first. In the learning pass, hand-rewrite P(alive).
- **2.25h L3 offer uplift:** in the learning pass, hand-rewrite the IPW policy value and explain why a flat average can hide a good policy.

**Thu Sep 17 — about 4 hours**
- **1.25h R1 store personalization:** 60-minute timed rep, then hand-rewrite the ALS user step. Being home turf, this should feel the smoothest of all your reps; use it to practice narrating depth.
- **0.5h R2:** the position-bias slice (20 minutes), then rehearse the R2 and R4 probes out loud.
- **1.25h Dress rehearsal:** your partner draws from the pool, which now includes a ranking prompt. A human interrupts every 8 minutes; record the screen.
- **0.5h Tooling answers** out loud, including the known-answer point.
- **0.5h Cold-explain drill:** hazard model, BG/NBD, ZILN, uplift, IPW, ALS, BPR, nDCG, and the position-bias model, 90 seconds each. Then stop for the day.

**Fri Sep 18:** the 12-day plan's interview-day routine, but make the warm-up **R3** (item-to-item CF, 20 minutes) instead of BPE or k-means. It's close to a likely problem and it exercises your environment end to end.

**If you fall behind, drop in this order:** the R2 slice (keep the talk-through) → the optional skill file → shorten the rehearsal to 40 minutes. **Never drop L1, L2, L3, or R1.**

---

## 8. Spoilers — read only after the relevant rep

These are measured on seed 0 of `lifecycle`; other seeds give similar values.

- **At day 180,** about 40% of signed-up players are active, 21% lapsed (can still return), and 39% truly churned. Lapsed and churned players look identical in the logs.
- **Churn (L1):** among players active in the last 7 days, about 8% show no activity in the next 28. Recency alone gets AUC ≈ 0.86; a simple logistic model gets ≈ 0.88 AUC and ≈ 0.49 PR-AUC. On *all* players, "active in the next 28 days" gets ≈ 0.98 AUC from recency alone — which is why the population choice matters.
- **LTV (L2):** about 94% of players spend nothing in the next 90 days, and the top 1% bring in ≈ 52% of revenue. BG/NBD on active days predicts aggregate 28-day activity within about 2%, but its top P(alive) decile (≈ 0.996) is active only ≈ 57% of the time. That's the misspecification talking point: BG/NBD ties dropout to transactions, so a player with many active days looks nearly immortal. In this data, lapse risk is driven by time and recent experience (loss streaks, content events).
- **Offer (L3):**
  - The true average effect is ≈ +$1.0 per player in 90-day revenue. The observed difference in means is similar, with a standard error of ≈ $0.75, so the experiment "looks flat."
  - **By segment (true effects):** active payers ≈ −$5 (discount cannibalization plus pulled-forward purchases); active non-payers ≈ +$3 (first-purchase conversion); lapsed payers ≈ +$7; truly churned players $0.
  - **30-day return among lapsed players:** ≈ +57 points for recently lapsed social players, versus ≈ +1 point for long-lapsed solo players.
  - **Policy value per player:** treat-all ≈ $0.99; treat only non-payers ≈ $1.13; oracle (treat only where the true effect is positive) ≈ $1.51.

These are measured on seed 0 of `shop`:

- **R1:** Recall@10 on purchases after day 70 is ≈ 0.09 for popularity, ≈ 0.28 for "most-played champion," and ≈ 0.21 for plain implicit ALS (16 factors). A naive end-of-pipeline score blend only *tied* the heuristic. That's the lesson: sparse purchases alone aren't enough, and the dense play signal belongs inside the model.
- **R2:**
  - The explore-bucket CTR curve (relative to slot 1) is roughly 1.00, 0.71, 0.58, 0.50, 0.37, 0.29, against a true curve of 1.00, 0.76, 0.58, 0.45, 0.36, 0.28 — close, but noisy at about 6k sessions, so show intervals.
  - `prod` CTR is about twice `explore` CTR (≈ 6.4% vs 3.2%), because popularity is a better-than-random logging policy.
  - **Exact expected purchases per session when re-ranking the full candidate set:** random ≈ 0.05; popularity ≈ 0.12; champion heuristic ≈ 0.46; a 4-feature pointwise logistic ranker ≈ 0.52; oracle ≈ 0.75.
  - Trained naively on `prod` clicks, the popularity coefficient was ≈ 0.48 versus ≈ 0.42 when trained on explore data with position weights — but ranking quality was nearly identical. That's the "measure whether debiasing matters" point.
- **R3:** next-purchase hit rate@10 is ≈ 0.09 for popularity, ≈ 0.12 for same-champion, and ≈ 0.12 for item-to-item cosine. Co-purchase similarity rediscovers the champion structure from behavior alone.

---

## 9. One-page cheat sheet

- **Minute 1:** "Is it fine to write the core myself and use sklearn, scipy, or lifetimes as a reference?"
- **Minutes 1–5:** the action and its cost, the churn definition, the horizon and moment, the population, and any contamination from past interventions.
- **Minutes 5–10:** cutoffs, label window, primary and guardrail metrics, baseline — all written in `spec.md`.
- **Churn:** report on the decision-relevant population; calibration plus precision at your budget.
- **LTV:** ranking (normalized Gini) and calibration (decile table) are separate questions; heavy tails change the loss you should use.
- **Next-best-action:** target uplift, not risk; evaluate the policy with IPW against treat-all and treat-none.
- **Ranking:** always show popularity and a domain heuristic; exclude owned and unreleased items; say whether you're re-ranking a shown slate or the full catalog; learn position bias only from randomized traffic.
- **Verification:** hand-computed cases, known answers (CDNOW), a reference implementation, and simulation truth.
- **Close:** what I'd ship, what I don't trust, the online test design, and what becomes a shared capability.
