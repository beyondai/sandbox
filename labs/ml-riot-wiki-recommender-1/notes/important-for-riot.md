The speaker is Wesley Hunt, Senior Director of Research at Riot Games,
presenting "When Research Meets Release Dates: Production Grade RL for Games" at
the AI and Games Conference 2025: [00:10]. He shares how Riot bridges the gap
between deep reinforcement learning research and live game production, notably
for Riot's fighting game 2XKO: [00:25].Key ML Design Principles, Guides, and
TipsResearch Wins $\neq$ Production WinsSolving a game via a research moonshot
(e.g., beating human pros) is only step one: [04:51]. In live games, value comes
from what you do with the policy, not simply producing an unbeatable bot:
[00:36].One trained policy can serve as a shared foundation across multiple
products and use cases: behavior cloning, automated fuzzing/QA testing,
matchmaking substitutes/drop in bots, practice opponents, onboarding, meta
analysis, and personalized coaching: [05:39].Work from Game State, Not
PixelsWhile research showcases often train directly on raw screen pixels,
production bots should operate on structured game state features (positions,
velocities, inputs): [03:34]. Rendering frames for thousands of concurrent bot
instances introduces massive unnecessary compute overhead: [03:35].Capture both
game state and explicit player actions to learn full distributions over player
behaviors: [03:55].Treat RL as a Gated Platform (The Four Gates
Framework)Progress models across rigorous stage gates:Gate 1 — Prototype
(Offline): Focus on reward shaping and signal quality on simplified subproblems;
beat heuristic baselines: [25:31].Gate 2 — Pilot (Sandbox/QA): Verify
reproducible, stable performance across seeds; instrument automated eval data
pipelines and track compute costs: [25:54].Gate 3 — Limited Live (Opt in modes):
Gather live player telemetry, assess player experience, validate guardrails:
[26:24].Gate 4 — General Availability (Live Service): Continuous deployment with
monitoring, rollbacks, and ongoing warm matches: [27:00].Invest in Evaluation,
Telemetry, and Variance Control EarlyReinforcement learning suffers from severe
run to run variance (different trajectories caused purely by random
seeds/initializations): [16:49]. Without rigorous statistical evaluation, teams
mistake random run fluctuations for genuine architectural progress:
[16:37].Multi dimensional evaluation must precede optimization: evaluate across
gameplay quality, stability/reproducibility, coverage of scenarios, and
operational/serving cost: [27:14].Guard Against Classic Failure ModesReward
Hacking: Agents optimize only the reward function given, not the intended
designer behavior (e.g., prioritizing damage while neglecting survival, or
corner turtling): [17:39].Non stationary Data & Patch Churn: Live games change
every few weeks. Balance adjustments alter the underlying state transition
dynamics, causing existing policies to degrade or behave erratically:
[18:05].Degenerate Gameplay & Exploits: Agents readily discover unfun or abusive
gameplay loops (e.g., repetitive corner lockdown combos) that ruin player
experience: [19:37].Infrastructure Cost Spikes: Without tight cost budgeting,
self play and RL scaling scale nonlinearly and blow up training budgets right
before launch: [18:55].Parallel Investment & Fallback SafeguardsAlways maintain
an Applied Track alongside the Research Track: [20:41].Start with rule based /
designer AI as a reliable baseline: [21:13]. Transition to hybrid ML/AI and
imitation learning before committing to full RL: [21:22].Fail Safe Rule: "If it
can't fail safely, it can't ship": [00:59]. Always deploy fallback behaviors
(e.g., behavior trees or heuristic bots) so players never experience a broken
agent if ML inference fails: [24:06].What Is Specially Important for His
Business, and Why?For Riot Games, what is uniquely critical is aligning ML
policies with game designer intent and player enjoyment, rather than maximizing
raw win rates: [13:50].Why This Matters for Riot's Business:Session Based Games
Rely on Long Term Retention:Riot operates live service games (League of Legends,
VALORANT, Teamfight Tactics, 2XKO) that depend on long term mastery,
replayability, and dynamic competitive metas: [08:22]. If a bot plays like an
inhuman, frame perfect aimbot or spams abusive exploits, it frustrates human
players and harms retention: [10:37], [20:09].Meeting Players at Their Skill
Level:Bots are used heavily for first time onboarding and practice: [06:01],
[24:42]. A high MMR or "diamond level" bot destroys onboarding: the business
needs bots calibrated across bronze, silver, and gold skill tiers that make
believable human mistakes and showcase fun combos: [10:57], [15:39].Sustainable
Live Service Operations:Live games receive balance patches every two weeks:
[10:48]. If deploying a bot requires a team of scientists to retrain from
scratch over 7–10 days at massive cloud expense: [31:01], the game team cannot
afford to maintain it: [11:25]. The ML platform must be handed off smoothly to
production engineers and designers with reproducible recipes, stable costs, and
clear ownership: [28:38].
