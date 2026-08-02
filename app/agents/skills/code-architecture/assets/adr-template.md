# ADR-{NUMBER}: {Title}

**Date:** {YYYY-MM-DD}
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-{NUMBER}
**Deciders:** {names or roles}

---

## Context

<!--
Describe the situation that requires a decision.
What forces are at play? What constraints exist?
What is the problem being solved?

Be specific — vague context leads to vague decisions.
Example: "The UserService currently imports directly from the PostgresClient,
making it impossible to test user creation logic without a running database.
This slows down the test suite and makes CI unreliable."
-->

{Describe the context and problem here}

---

## Decision Drivers

<!--
List the criteria that matter for this decision.
Order them by importance.
-->

- {Most important criterion, e.g. "Testability of domain logic"}
- {Second criterion, e.g. "Minimal change to existing callers"}
- {Third criterion, e.g. "Consistent with existing patterns in the codebase"}
- {Fourth criterion, e.g. "Team familiarity with the approach"}

---

## Options Considered

### Option A: {Name}

{One paragraph describing this option and how it works}

**Pros:**
- {Advantage 1}
- {Advantage 2}

**Cons:**
- {Disadvantage 1}
- {Disadvantage 2}

---

### Option B: {Name}

{One paragraph describing this option and how it works}

**Pros:**
- {Advantage 1}
- {Advantage 2}

**Cons:**
- {Disadvantage 1}
- {Disadvantage 2}

---

### Option C: {Name} (if applicable)

{One paragraph describing this option and how it works}

**Pros:**
- {Advantage 1}

**Cons:**
- {Disadvantage 1}

---

## Decision

**We choose Option {A/B/C}: {Name}**

{One paragraph justifying the choice. Reference the decision drivers.
Be direct — state why this option wins against the alternatives.
Example: "We choose Option B (Clean Architecture with Ports) because testability
of domain logic is our highest priority criterion. Option A (Layered) would require
database fixtures in every domain test. Option B allows domain tests to run with
zero infrastructure."}

---

## Consequences

### Positive
- {What improves as a result}
- {What becomes easier}

### Negative
- {What becomes harder or more complex}
- {What technical debt is accepted}

### Neutral
- {What changes but is neither good nor bad}

---

## Implementation Notes

<!--
Concrete guidance for implementing this decision.
What files change? What is the migration path?
What must be true before this can be considered done?
-->

**Files to create:**
- `{path}` — {one-sentence description}
- `{path}` — {one-sentence description}

**Files to modify:**
- `{path}` — {what changes and why}

**Files unchanged:**
- {List of files explicitly confirmed as not needing changes}

**Definition of done:**
- [ ] {Concrete measurable outcome}
- [ ] All existing tests pass
- [ ] New tests cover the new structure
- [ ] No circular imports
- [ ] Domain layer has zero imports from infrastructure or API layers

---

## References

- {Link or reference to related ADR, document, or discussion}
- {Link to relevant pattern in PATTERNS.md}
