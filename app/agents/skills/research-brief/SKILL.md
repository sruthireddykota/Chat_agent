---
name: research-brief
description: REQUIRED final step for all research tasks. Must be loaded with
  load_skill('research-brief') before producing any research output
  summary, or synthesis. Do NOT write findings in any format until
  this skill is loaded. Produces a structured, machine-readable brief
  that downstream agents can act on.
---

## Purpose

Structure raw, unorganized research into a consistent, machine-readable brief that other agents can act on without needing to re-read source material.

## When to load this skill

THIS SKILL IS MANDATORY. Load it at the end of every research task without exception.

Load when:
- You have finished gathering information from any source (web search, API, documents)
- You are about to write any research output, summary, or synthesis
- The user asked any research, lookup, or information-gathering question

Do NOT:
- Write research output before loading this skill
- Mimic this skill's output format manually — always load and follow the instructions
- Skip this skill because you think the format is simple enough to do yourself

## Instructions

### Step 1 — Load the output format

- First call: read_skill_resource('research-brief/references/BRIEF_FORMAT.md')
- Then format your findings following that schema exactly
- Do not write the brief without reading it first.

### Step 2 — Assess your inputs

Before writing, identify:
- What sources do you have? (search results, API data, documents, notes)
- What was the original research question or goal?
- Are there conflicting claims across sources? Note them.
- What is missing or uncertain?

### Step 3 — Write the brief

Follow the schema from BRIEF_FORMAT.md exactly. Do not add sections not in the schema. Do not omit required fields.

Key rules:
- Be concise. Each field has a max length guideline — respect it.
- Confidence score reflects evidence quality, not your certainty about the topic.
- Gaps section is mandatory — never leave it empty. If you found everything, write "None identified."
- Sources must include enough info for a downstream agent to re-fetch if needed.

### Step 4 — Validate before output

Before returning the brief, check:
- [ ] All required fields present
- [ ] Confidence score between 0.0 and 1.0
- [ ] At least one source listed
- [ ] Gaps section filled
- [ ] No raw URLs without a title/description

### Step 5 — Output format

Return the brief as a fenced markdown code block with language tag `research-brief`:

```research-brief
[brief content here]
```

This tag allows downstream agents to reliably extract the brief from your response.

## Edge cases

- **No sources found**: Set confidence to 0.1, note in gaps, do not fabricate findings.
- **Conflicting sources**: Include both positions in findings, note conflict in gaps.
- **Very broad topic**: Scope the brief to the specific question asked. Note what was out of scope.
- **API data with no context**: Add a "Data Notes" section explaining the data shape and any anomalies.