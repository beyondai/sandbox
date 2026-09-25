# Agent query fan-out: how many catalog queries per agent request?

Researched 2026-09-25. Labels: "confirmed (source)" = stated by the vendor
or CDN in a primary source; "estimate/third-party" = measured by an outside
firm or derived by us.

## Summary: is "1 user request -> ~10 search queries" true?

- Partly. ~10 matches 2026 *web* search fan-out (Gemini 3 ~9-11, ChatGPT ~7.6
  per searching prompt), but those queries go to Google or Bing, not to us.
- Deep modes (Deep Search, deep research) run dozens to hundreds per task.
- Against our catalog, discovery is mostly feed-based (0 QPS) plus live calls.
- Plan for 5 backend queries per agent request (low 2, high 15; size for 10).
- Batch lookup, multi-query endpoints, rich filters and feeds keep it near 5.

## 1. Search queries per prompt in AI assistants

### Vendor statements (primary)

- Google AI Mode - confirmed (Google blog, 2025-05-20,
  https://blog.google/products-and-platforms/products/search/google-search-ai-mode-update/):
  AI Mode "breaks down your question into subtopics and issu[es] a multitude
  of queries simultaneously". No count given. The May 2025 shopping post
  (https://business.google.com/us/think/search-and-video/google-shopping-ai-mode-virtual-try-on-update/)
  says shopping queries fan out into "several simultaneous searches".
- Google Deep Search - confirmed (same 2025-05-20 post): "can issue hundreds
  of searches" and produce a cited report "in just minutes".
- Google I/O 2026 - confirmed (blog, 2026-05-19,
  https://blog.google/products-and-platforms/products/search/search-io-2026/):
  AI Mode passed 1B monthly users, "queries more than doubling every
  quarter"; launched "Search agents" that monitor the web on a schedule.
  No fan-out count given. Scheduled monitoring agents mean recurring load
  that no human triggers.
- OpenAI deep research - confirmed (OpenAI, 2025-02-02,
  https://openai.com/index/introducing-deep-research/): finds, analyzes and
  synthesizes "hundreds of online sources"; runs for minutes (up to ~30).
  No search-call count given.
- OpenAI shopping research - confirmed via Retail Dive and OpenAI help
  (launched 2025-11-24,
  https://www.retaildive.com/news/openai-launches-chatgpt-shopping-research-feature/806656/):
  asks clarifying questions, then searches retail and editorial sites for
  price, availability, reviews and specs over several minutes. Only sites
  that allow OpenAI's browsing agent are used. No count given (OpenAI pages
  returned 403 to our fetcher; details are from secondary coverage).
- Perplexity Deep Research - confirmed (Perplexity, 2025-02-14,
  https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research):
  "performs dozens of searches, reads hundreds of sources". Pro Search counts
  are not published.
- Microsoft Copilot - not verified: we found no public Microsoft number for
  searches per prompt.

### Measurement studies (all estimate/third-party)

These studies read the sub-queries from the grounding metadata the model API
returns. They show what the API does, which may differ slightly from the
consumer apps.

- Nectiv, ChatGPT, 2025-10-14, 8,500+ prompts, 9 verticals
  (https://nectivdigital.com/blog/new-data-study-what-queries-is-chatgpt-using-behind-the-scenes):
  only ~31% of prompts triggered search. Among those: mean 2.17 searches,
  mode 3, max 4. Commerce vertical: 41% searched, ~2.1 searches each.
- Nectiv, ChatGPT follow-up, 2026-08-13, ~4,000 prompts, "GPT 5.6 Sol"
  (https://nectivdigital.com/blog/chatgpt-tripled-fan-out-queries-data-study):
  mean 7.61 per prompt (up 250%), max 29; 55% of prompts in the 6-12 range,
  mode 8. Fashion 8.5, Software 10.7, Travel below 6. 64% of queries used
  "site:" (they target specific domains, then fetch pages).
- Seer Interactive, Gemini 3 API with forced grounding, 2025-11-21, 501
  prompts (https://www.seerinteractive.com/insights/gemini-3-query-fan-outs-research):
  mean 10.7, min 3, max 28 (Gemini 2.5 mean was 6.01). 95% of fan-out
  queries had zero global search volume; only 1% overlapped.
- Nectiv, Gemini 3 via Grounding API, 2025-12-03, ~9,000 prompts, 70K+ rows
  (https://nectivdigital.com/blog/new-research-we-analyzed-60k-google-fan-out-queries):
  mean 9.06; 59% of prompts had 5-11, 24% had 12-19, max 28. The authors
  note this may not match AI Mode exactly.
- Seen in SEO blogs but not checked: "AI Mode does 8-12 sub-queries" and
  "ChatGPT fans out on 47% of answers". We found no primary source for
  either.

### Distribution by mode (synthesis, estimate)

- Quick answer (ChatGPT default, AI Overviews-style): 0 searches on most
  prompts (ChatGPT searched on 31% in 2025). When it does search: 2-3 in
  2025, 6-12 in 2026. Mean over all prompts is lower than the headline.
- Grounded/AI Mode style: mean ~9-11, 5-19 covers ~80%, tail to ~28.
- Deep research / Deep Search / shopping research: dozens to hundreds per
  task (vendor-confirmed as a range, never as a distribution).
- The trend is up fast: 2.5x to 3.5x year over year in both vendors.

## 2. How shopping agents reach retailer catalogs

- OpenAI ACP / Instant Checkout - confirmed (OpenAI developer docs,
  https://developers.openai.com/commerce/guides/key-concepts): discovery
  runs on a merchant *feed* (CSV/TSV/XML/JSON; daily snapshot plus updates
  as often as every 15 minutes). Merchant endpoints are called only for
  checkout sessions. So ACP discovery adds no search QPS to us.
- OpenAI strategy change - confirmed via trade press (Retail Insight
  Network, 2026-03,
  https://www.retail-insight-network.com/news/openai-shifts-chatgpt-shopping-plans-to-retailer-run-apps-report/):
  Instant Checkout is moving to retailer-run apps inside ChatGPT. Apps are
  built on MCP, so ChatGPT calls the retailer's server live during the chat
  (confirmed, https://developers.openai.com/apps-sdk).
- Target in ChatGPT - confirmed (Target, 2025-11-25,
  https://corporate.target.com/news-features/article/2025/11/target-chatgpt):
  Target app live in ChatGPT with multi-item baskets. Target did not
  describe the backend. If it uses the MCP app model, **every product
  question turns into live calls to Target search** - this is the path our
  5k QPS agent budget actually covers.
- Google UCP - confirmed (Google Developers Blog, 2026-01-11,
  https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/):
  open protocol with Shopify. Merchants publish `/.well-known/ucp`; the
  protocol runs over REST, MCP or A2A. Google's own implementation requires
  a Merchant Center feed. A March 2026 expansion added real-time catalog
  access, carts and identity linking (per trade press; not checked on a
  primary page). The UCP draft catalog spec (https://ucp.dev/draft/specification/shopping/catalog/)
  defines `search` (free text plus filters and context: location, currency)
  and a batch `lookup` by ID.
- Google Shopping Graph - confirmed (Google, May 2025, URL above): 50B+
  listings, 2B+ refreshed every hour. AI Mode shopping mostly reads Google's
  own index, not retailer APIs.
- Target on Google, Copilot and ChatGPT - confirmed (Target fact sheet,
  2026-06-18, https://corporate.target.com/press/fact-sheet/2026/06/conversational-ai):
  Target is live on all three; it uses UCP for Google AI Mode and Gemini.
- Shopify Global Catalog MCP - confirmed (https://shopify.dev/docs/agents/catalog/global-catalog):
  tools `search_catalog`, `lookup_catalog` (batch), `get_product`. It
  documents a "discover then evaluate" flow: 1 search, then a
  `get_product` call per candidate. Page size: default 10, max 50.
- Perplexity - confirmed (PayPal press release, 2025-11-25,
  https://newsroom.paypal-corp.com/2025-11-PayPal-and-Perplexity-Launch-Instant-Buy):
  Instant Buy uses PayPal merchants. Its Merchant Program runs on a feed
  (CSV/XML via API, SFTP or S3; per third-party guides).
- Microsoft Copilot Checkout - confirmed (PayPal press release,
  2026-01-08,
  https://newsroom.paypal-corp.com/2026-01-08-PayPal-Powers-Microsofts-Launch-of-Copilot-Checkout):
  catalogs arrive through PayPal store sync and Merchant Center feeds.
- Amazon Buy for Me - third-party (TechCrunch, 2025-04-03,
  https://techcrunch.com/2025/04/03/amazons-new-ai-agent-will-shop-third-party-stores-for-you/):
  an agent that browses brand sites and checks out on them (like scraping or
  browser automation), built on Bedrock with Nova and Claude. Beta; about
  500K items by the end of 2025 (not verified in a primary source).
- Pattern: discovery is mostly **feed-based** (OpenAI, Google, Perplexity,
  Microsoft). Live **API/MCP** calls appear in retailer apps and UCP catalog
  search. **Browsing and scraping** make up the rest (ChatGPT-User, shopping
  research, Buy for Me) and hit our web tier and search result pages, not a
  clean API.

## 3. Aggregate traffic evidence

- Cloudflare Radar 2025 Year in Review - confirmed (Cloudflare, published
  December 2025, data to 2025-12-02,
  https://blog.cloudflare.com/radar-2025-year-in-review/): "user action"
  crawling (fetches made for a live chatbot prompt) grew over 15x in 2025,
  and 21x from January to early December. Training crawling is still the
  largest: up to 32x user-action crawling at peak. Non-Google AI bots made
  up 4.2% of HTML requests; Googlebot 4.5%.
- Cloudflare crawl-to-refer - confirmed (2025-07-01,
  https://blog.cloudflare.com/ai-search-crawl-refer-ratio-on-radar/, and
  the Year in Review): Anthropic up to 500,000:1; OpenAI up to 3,700:1;
  Perplexity generally below 400:1; Google peaked near 30:1. Caveat: native
  apps send no referrer, which inflates these ratios.
- Cloudflare by purpose - confirmed (2025-08-28,
  https://blog.cloudflare.com/ai-crawler-traffic-by-purpose-and-industry/):
  training is about 80% of AI bot crawling; user action is under 5%.
- Akamai - confirmed (press release, 2026-07-15,
  https://www.akamai.com/newsroom/press-release/akamai-research-commerce-becomes-the-epicenter-for-ai-bot-attacks-and-agentic-fraud-in-2026):
  47.9% of all AI bot traffic (Jul-Dec 2025) hit the commerce vertical.
  Training crawlers are more than 70% of AI bot triggers in commerce. Note:
  this is commerce's *share of AI bots*; several blogs misread it as "half
  of commerce traffic is bots".
- Adobe - third-party but a panel-based primary (Adobe, 2026,
  https://business.adobe.com/blog/ai-traffic-surge-retail-sites-not-machine-readable):
  AI-referred visits to US retail sites grew 393% YoY in Q1 2026. These are
  human click-throughs, not agent queries.
- Target - confirmed (Target fact sheet, 2026-06-18, URL above):
  AI-driven traffic to Target grew 2,000% YoY in Q1 2026.
- Takeaway: user-action and agent traffic is small today but grew 15-20x in
  a year. Growth rate matters more for a 2-year plan than today's share.

## 4. Recommended planning multiplier

Definition: backend search-engine queries (search, filter or retrieve
calls to our catalog service) per agent-originated request that reaches
us live. Feed-served discovery never reaches us, so it counts as 0 and is
not in these numbers. All numbers are estimate (ours), based on sections 1
and 2.

### Low case: 2 per request

- Structured app/MCP call: 1 search with filters, plus 1 batch lookup for
  price and stock. This matches the Shopify discover/evaluate flow when the
  lookup is batched.

### Typical case: 5 per request (range 3-8)

- 2-3 query reformulations (the 2025 ChatGPT mode was 3; agents add
  synonyms, brands, price bands), plus 1-2 detail or availability lookups,
  plus about 1 pagination or retry.

### High case: 15 per request (tail 50+)

- Shopping research or deep research sessions that hit us directly: mean
  fan-out of 8-11 (2026 data), plus per-product detail calls done one at a
  time. Deep modes are documented as "dozens to hundreds"; cap them with
  quotas, do not size for them.

### What "10" means for capacity

- At 5k QPS agent budget: multiplier 5 gives ~1,000 agent requests/s;
  multiplier 10 gives ~500/s; multiplier 15 gives ~330/s. Size for 10 as the
  2-year ceiling (fan-out grew about 3x in one year), and design the API to
  hold the typical case at 5 or lower.

### API design choices that lower the multiplier

- Multi-query endpoint: accept an array of queries and filter sets in one
  call and run them server-side with shared retrieval. This turns N
  reformulations into 1 request (per-call cost stays about N, but you save
  connection, auth and ranking overhead, and you can de-dupe candidates).
- Batch lookup by ID (as in UCP `lookup` and Shopify `lookup_catalog`) so
  "evaluate 10 candidates" is 1 call, not 10.
- Rich structured filters and facets (price, brand, size, store
  availability, rating) in the response, so agents narrow the results
  instead of rephrasing. Return facet counts and "did you mean" hints.
- Larger pages (up to 50, as Shopify allows) with compact fields, so there
  are fewer pagination calls.
- Feeds first: publish complete, frequent feeds (ACP, Merchant Center/UCP,
  Perplexity, Microsoft) so most discovery happens on their index. Keep
  live calls for price, stock and cart.
- Caching: agent queries are long (6-7 words) and 95% have no search
  volume (Seer), so a raw query-string cache will rarely hit. Cache instead
  at the normalized level (parsed intent plus filters), the candidate
  retrieval stage, and the product-detail and availability level (short TTL).
- Separate lightweight price and stock endpoint so re-checks skip ranking.
- Per-agent quotas and token budgets (by user agent, API key or UCP
  identity), with 429 and Retry-After, and a lower priority class for
  deep-research traffic, so agent spikes cannot crowd out the 10k human
  QPS.
- Observability: log a session or conversation ID on agent calls to
  measure the real multiplier. Replace these estimates with measured data
  within one quarter.

## Gaps and caveats

- No vendor publishes a per-prompt distribution; all distributions above
  come from API-based SEO studies.
- Web-search fan-out is not retailer-catalog fan-out. We found no public
  measurement of calls per session against a retailer's MCP or UCP catalog.
- Several OpenAI and Perplexity pages returned 403 to our fetcher; those
  facts come from their search snippets and trade press.
