---
name: code-architecture
description: >
  Design, reason about, and produce well-structured software architectures for Python projects.
  Use when asked to design a system, plan a project structure, break down a complex feature into
  modules, decide between architectural patterns, review an existing design, or produce any
  architectural artifact — diagrams, ADRs, module maps, interface contracts, or dependency graphs.
  Covers layered architecture, clean architecture, hexagonal, event-driven, pipeline, and
  microservice patterns with concrete Python implementations.
compatibility: Python 3.10+. Scripts use stdlib only.
metadata:
  author: agent-framework
  version: "1.0"
---

## Skill entry point

When this skill is loaded, always execute in this order:
1. Read `references/ARCHITECTURE_PRINCIPLES.md` — mandatory before designing anything
2. Identify the task type from ## Instructions below
3. Read the task-specific reference document listed in that workflow
4. Produce a written plan BEFORE writing any code or files
5. Validate the design using `scripts/validate_architecture.py` before returning

## Dependencies

None. Scripts use stdlib only — no install needed.

---

## Purpose

Produce software architectures that are:
- **Correct** — solves the actual problem described, not a simpler version of it
- **Modular** — components have single responsibilities and clear boundaries
- **Evolvable** — easy to extend without rewriting existing code
- **Testable** — every layer can be tested in isolation
- **Explicit** — dependencies flow in one direction and are declared, not hidden

Handle the full architecture lifecycle: analyse → decompose → design → validate → document.

---

## When to load this skill

Load when:
- Asked to design a system, service, or application from scratch
- Asked to break a complex feature into modules or components
- Asked to decide between two or more architectural approaches
- Asked to review or improve an existing project structure
- Given a requirements description and asked "how should I build this"
- Asked to produce an ADR (Architecture Decision Record)
- A task involves 3 or more files — always plan structure before writing

Do NOT load when:
- The task is a single function or small utility (use python-coding skill instead)
- The task is purely SQL schema (use sql-coding skill instead)
- The request is "fix this bug" with no structural change involved

---

## Instructions

### Step 1 — Identify the task type

Determine which of these you are doing:

- **Greenfield** — designing a new system from scratch
- **Feature** — adding a significant new capability to an existing system
- **Refactor** — restructuring existing code without changing behaviour
- **Review** — evaluating an existing architecture and recommending improvements
- **Decision** — choosing between two or more architectural options
- **Documentation** — producing architectural artifacts for an existing system

Each has a different workflow below.

---

### Greenfield — designing a new system

1. Load architecture principles:
   `read_skill_resource("code-architecture/references/ARCHITECTURE_PRINCIPLES.md")`

2. Load pattern catalogue:
   `read_skill_resource("code-architecture/references/PATTERNS.md")`

3. **Analyse requirements** — answer these before touching structure:
   - What is the primary responsibility of this system?
   - What are the inputs, outputs, and side effects?
   - What changes frequently vs what is stable?
   - What must be testable in isolation?
   - What external systems does it depend on?

4. **Choose a pattern** from `PATTERNS.md` that fits the answers above.
   State your choice and justify it in one paragraph before proceeding.

5. **Decompose into layers and modules** — produce a written module map:
   ```
   src/
     <domain>/        ← pure business logic, no I/O
     <application>/   ← orchestrates domain, owns use cases
     <infrastructure>/← I/O implementations (DB, HTTP, files)
     <api>/           ← entry points (CLI, HTTP routes, events)
   ```
   Name every module and write one sentence describing its responsibility.

6. **Define interfaces** — for every boundary between layers, define the contract:
   - What does the caller pass in?
   - What does it get back?
   - What exceptions can it raise?

7. **Identify dependency direction** — draw or describe the dependency graph.
   Dependencies must only point inward (toward domain). Never outward.

8. **Write the architecture plan** using the ADR template:
   `read_skill_resource("code-architecture/assets/adr-template.md")`

9. **Validate the design**:
   `run_skill_script("code-architecture", "scripts/validate_architecture.py",
   args={"input": "<paste the module map and dependency list>"})`

10. Only after validation passes — produce scaffold files.

---

### Feature — adding to an existing system

1. Load architecture principles:
   `read_skill_resource("code-architecture/references/ARCHITECTURE_PRINCIPLES.md")`

2. Load extension patterns:
   `read_skill_resource("code-architecture/references/EXTENSION_PATTERNS.md")`

3. **Map the existing structure** — list every existing module that the feature touches.

4. **Identify the integration points** — where does the new code plug in?
   - New module in existing layer, or new layer?
   - New interface, or implementation of existing interface?
   - Does it change any existing module's public API?

5. **Check for violation risks**:
   - Does this feature create a circular dependency?
   - Does it mix responsibilities that should stay separate?
   - Does it introduce an external dependency into the domain layer?

6. **Plan the delta** — list only what changes, what is new, what stays the same.

7. Validate:
   `run_skill_script("code-architecture", "scripts/validate_architecture.py",
   args={"input": "<existing structure + planned changes>"})`

---

### Refactor — restructuring existing code

1. Load architecture principles:
   `read_skill_resource("code-architecture/references/ARCHITECTURE_PRINCIPLES.md")`

2. Load refactor patterns:
   `read_skill_resource("code-architecture/references/REFACTOR_PATTERNS.md")`

3. **Diagnose first** — identify which specific violations are present:
   - God classes or god modules (doing too many things)
   - Circular imports
   - Domain logic leaking into I/O layers
   - Untestable code (hidden side effects, global state)
   - Missing abstractions at boundaries

4. **Produce a before/after map** — show current structure and target structure side by side.

5. **Plan the migration sequence** — small safe steps, each leaving the system working:
   - Step 1: extract interface
   - Step 2: move implementation behind interface
   - Step 3: update callers
   - Never attempt to move everything at once

6. Validate the target structure:
   `run_skill_script("code-architecture", "scripts/validate_architecture.py",
   args={"input": "<target structure>"})`

---

### Review — evaluating an existing architecture

1. Load architecture principles:
   `read_skill_resource("code-architecture/references/ARCHITECTURE_PRINCIPLES.md")`

2. Load anti-patterns reference:
   `read_skill_resource("code-architecture/references/ANTI_PATTERNS.md")`

3. **Evaluate against each principle** — for every principle in ARCHITECTURE_PRINCIPLES.md,
   state whether the current architecture satisfies it, partially satisfies it, or violates it.

4. **Classify findings by severity**:
   - **Critical** — prevents testing, causes circular deps, mixes I/O with logic
   - **Major** — unclear responsibilities, implicit coupling, missing interfaces
   - **Minor** — naming, organisation, documentation gaps

5. **Produce recommendations** ordered by highest impact first.
   For each: state the problem, the solution, and the effort estimate (small/medium/large).

---

### Decision — choosing between architectural options

1. Load architecture principles:
   `read_skill_resource("code-architecture/references/ARCHITECTURE_PRINCIPLES.md")`

2. Load pattern catalogue:
   `read_skill_resource("code-architecture/references/PATTERNS.md")`

3. **Define the decision criteria** — what matters for this specific system:
   - Simplicity vs flexibility
   - Performance vs maintainability
   - Team size and experience
   - Expected rate of change
   - Testing requirements

4. **Evaluate each option against each criterion** — use a decision matrix:
   ```
   Option A: layered architecture
     Simplicity:      HIGH  — straightforward to understand
     Testability:     MEDIUM — domain mixed with infra
     Evolvability:    LOW   — changing infra requires touching domain

   Option B: clean/hexagonal architecture
     Simplicity:      MEDIUM — more files, clearer boundaries
     Testability:     HIGH  — domain fully isolated
     Evolvability:    HIGH  — swap infra without touching domain
   ```

5. **State a clear recommendation** with justification. Do not hedge — make a call.

---

### Documentation — producing architectural artifacts

1. Load the documentation templates:
   `read_skill_resource("code-architecture/assets/adr-template.md")`
   `read_skill_resource("code-architecture/assets/module-map-template.md")`

2. Choose the artifact type needed:
   - **ADR** — for a significant decision already made or being made
   - **Module map** — for describing current or target structure
   - **Interface contract** — for documenting a boundary between components
   - **Dependency graph** — for showing what depends on what

3. Produce the artifact using the relevant template.

---

## Output rules

- Always produce a written plan or analysis BEFORE any code or file structure
- Never start writing files without first stating the architecture in prose
- Always name every module and give it a one-sentence responsibility description
- Always show dependency direction explicitly — who depends on whom
- Never propose circular dependencies — if they appear, redesign
- Use Python dataclasses, Protocols, and ABCs to define interfaces — not dicts
- Keep domain layer free of: database clients, HTTP clients, file I/O, framework imports
- Always identify what is testable in isolation and what requires mocks
- State trade-offs honestly — every pattern has costs, name them
- If the requirements are ambiguous, state your assumptions explicitly before designing