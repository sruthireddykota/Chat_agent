# Research Brief Format

This document defines the required schema for all research brief outputs.
The researcher agent must conform to this format exactly.

---

## Schema

```
RESEARCH BRIEF
==============
Question:       [The original research question or task. Max 200 chars.]
Date:           [ISO 8601 date. e.g. 2025-03-15]
Confidence:     [Float 0.0–1.0. See scoring guide below.]

SUMMARY
-------
[2–4 sentence plain-language summary of the key finding. Max 400 chars.
Write this as if handing it to a developer who has 10 seconds to read it.]

KEY FINDINGS
------------
1. [Finding. Include the source label in brackets. e.g. "Rate limits reset every 60s [src-1]"]
2. [Finding.]
3. [Finding.]
[3–7 findings. Each max 150 chars.]

GAPS & UNCERTAINTIES
--------------------
- [What you could not find, what was conflicting, what needs verification.]
[At least one entry. Write "None identified." only if truly comprehensive.]

RECOMMENDED NEXT STEPS
-----------------------
- [Concrete action for the downstream agent. e.g. "Implement retry logic with exponential backoff"]
[1–3 steps. Be specific enough that a coder agent can act without re-researching.]

SOURCES
-------
[src-1] Title: [source title or description]
        URL/Ref: [url, doc name, or API endpoint]
        Fetched: [date or "N/A"]
        Reliability: [high | medium | low]

[src-2] ...
```

---

## Confidence Scoring Guide

| Score | Meaning |
|-------|---------|
| 0.9–1.0 | Multiple high-reliability sources agree. Official docs or primary sources. |
| 0.7–0.8 | 2+ sources agree, at least one authoritative. Minor gaps. |
| 0.5–0.6 | Single source or sources partially conflict. Proceed with caution. |
| 0.3–0.4 | Sparse data. Significant gaps. Findings are tentative. |
| 0.1–0.2 | Very little found. Brief is mostly gaps. Do not build on this without more research. |

---

## Example Brief

```research-brief
RESEARCH BRIEF
==============
Question:       What are the rate limits for the GitHub REST API for authenticated requests?
Date:           2025-03-15
Confidence:     0.92

SUMMARY
-------
Authenticated GitHub REST API requests allow 5,000 requests per hour per user token.
Certain endpoints (search, GraphQL) have separate, lower limits. Headers on every
response report remaining quota and reset time.

KEY FINDINGS
------------
1. Core REST API: 5,000 req/hr per authenticated user [src-1]
2. Search API: 30 req/min authenticated, 10 req/min unauthenticated [src-1]
3. Rate limit headers: X-RateLimit-Remaining, X-RateLimit-Reset on all responses [src-1]
4. GitHub Apps get 5,000 req/hr per installation (scales with org size) [src-2]
5. Secondary rate limits apply to concurrent requests and heavy mutations [src-1]

GAPS & UNCERTAINTIES
--------------------
- Secondary rate limit exact thresholds are not publicly documented
- Enterprise Server limits may differ — not checked

RECOMMENDED NEXT STEPS
-----------------------
- Implement header-based rate limit tracking (X-RateLimit-Remaining)
- Add retry logic: wait until X-RateLimit-Reset timestamp on 429 response
- Separate search requests into a distinct client with its own throttle (30 req/min)

SOURCES
-------
[src-1] Title: GitHub REST API rate limits
        URL/Ref: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
        Fetched: 2025-03-15
        Reliability: high

[src-2] Title: Rate limits for GitHub Apps
        URL/Ref: https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/rate-limits-for-github-apps
        Fetched: 2025-03-15
        Reliability: high
```