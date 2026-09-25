# Search Vision

The strategic design for Target's next-generation product search: one search
system serving guests on Target apps and web, LLM assistants, search engines,
and agents, across a 20M-SKU catalog.

## Language

### Who and where

**Guest**:
A person shopping with Target, signed in or anonymous.
_Avoid_: Customer, user, shopper

**Channel**:
Where a search request originates: App/Web, LLM Assistant, Search Engine, or
Agent.
_Avoid_: Surface, source, client

**App/Web**:
The Channel for Guests searching directly in Target's apps and website.
_Avoid_: Owned channel, first-party

**LLM Assistant**:
The Channel for third-party chat products (ChatGPT, Perplexity, Gemini)
answering a Guest's shopping question with Target products.
_Avoid_: Chatbot, AI search

**Search Engine**:
The Channel for Guests arriving from Google or similar web search results.
_Avoid_: SEO (SEO is the practice, not the Channel)

**Agent**:
The Channel for software acting on someone's behalf that queries the catalog
directly, whether Target-internal or external.
_Avoid_: Bot, crawler (a crawler feeds Search Engine, not Agent)

### What search does

**Search Core**:
The retrieval, query understanding, and base relevance shared by every
Channel.
_Avoid_: Search engine (collides with the Channel), platform

**Channel Front Door**:
The per-Channel entry into the Search Core, owning that Channel's API shape,
quotas, and capacity.
_Avoid_: Adapter, gateway, stack

**Ranking Policy**:
The per-Channel choice of objective, personalization, ads, and result shape
applied on top of the base relevance.
_Avoid_: Channel model, ranker

**Search Box**:
The single App/Web text entry that accepts both keywords and natural
language.
_Avoid_: Search bar, query box

**Query Router**:
The decision, per Guest query, between Keyword Search and Conversational
Search, or a hand-off to Assistant Mode.
_Avoid_: Intent classifier, dispatcher

**Keyword Search**:
A single query answered with a ranked product list and no generated text.
_Avoid_: Classic search, lexical search

**Conversational Search**:
Multi-turn search where each turn returns a ranked product set with a short
grounded explanation and refinements.
_Avoid_: Chat search, AI search, NL search

**Guided Shopping**:
A multi-step shopping task (e.g. "stock a dorm for $300") answered with a
bundle of product sets.
_Avoid_: Complex search, planning

**Assistant Mode**:
The explicit App/Web experience a Guest enters for Guided Shopping.
_Avoid_: Chat mode, Ask Target, shopping assistant

**Conversation Memory**:
What a Conversational Search or Assistant Mode session remembers about the
Guest; session-scoped by default, cross-session only on Guest opt-in.
_Avoid_: History, profile

### Availability

**Fulfillment Context**:
The Guest's selected store or ZIP and fulfillment method (Drive Up, Order
Pickup, same-day delivery, shipping) that search ranks and filters against.
_Avoid_: Location, store context

### Ads

**Sponsored Slot**:
A position in results that may hold a paid Roundel placement.
_Avoid_: Ad slot, promoted result

**Relevance Floor**:
The minimum relevance a sponsored product must meet to fill a Sponsored
Slot.
_Avoid_: Ad threshold, quality gate

**Blending**:
Merging sponsored and organic products into one result list.
_Avoid_: Ad insertion, mixing

### Cost

**Cost per Incremental Order**:
LLM spend divided by the orders an LLM-powered experience adds over its
control, compared against contribution margin.
_Avoid_: Token cost, AI cost
