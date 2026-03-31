---
name: sql-coding
description: Write, debug, review, and optimize SQL queries. Use when asked to write SELECT, INSERT, UPDATE, or DELETE queries; design or modify database schemas; fix SQL errors; optimize slow queries; or write migrations. Covers PostgreSQL and standard SQL patterns.
license: MIT
compatibility: Requires python3. Scripts use stdlib only.
metadata:
  author: agent-framework
  version: "1.0"
---

## Purpose

Produce correct, readable, and performant SQL that follows consistent conventions.
Handle the full SQL lifecycle: write → debug → review → optimize.

## When to load this skill

Load when:
- Asked to write any SQL query — SELECT, INSERT, UPDATE, DELETE, CTEs
- Asked to design or modify a database schema or table
- Given a SQL error to fix
- Asked to optimize a slow query
- Asked to write a database migration
- Asked about indexing, joins, or query planning

## Instructions

### Step 1 — Identify the task type

Determine which of these you are doing:
- **Write** — producing a new query from a description
- **Debug** — fixing a SQL error
- **Review** — improving existing working SQL
- **Optimize** — making a slow query faster
- **Schema** — designing or altering tables

Each has a different workflow below.

---

### Writing new queries

1. Load SQL standards first:
   `read_skill_resource("sql-coding/references/SQL_STANDARDS.md")`

2. Check if a relevant pattern exists:
   `read_skill_resource("sql-coding/references/QUERY_PATTERNS.md")`

3. Follow the standards — formatting, aliasing, and safety rules are mandatory.

4. Structure your output as:
   - The query in a fenced ```sql block
   - A short plain-English explanation of what it does
   - Any indexes that should exist for this query to be performant

---

### Debugging SQL errors

1. Load the error reference:
   `read_skill_resource("sql-coding/references/ERROR_PATTERNS.md")`

2. Run the query validator:
   `run_skill_script("sql-coding/scripts/validate_query.py", input=<sql text>)`

3. Return:
   - What the error means (one sentence)
   - Fixed query in a fenced ```sql block
   - Why it failed (2-3 sentences)

---

### Reviewing SQL

1. Load SQL standards:
   `read_skill_resource("sql-coding/references/SQL_STANDARDS.md")`

2. Run the query validator:
   `run_skill_script("sql-coding/scripts/validate_query.py", input=<sql text>)`

3. Return feedback grouped by severity:
   - **Must fix** — correctness issues, SQL injection risks, missing WHERE on UPDATE/DELETE
   - **Should fix** — formatting, aliasing, SELECT * usage
   - **Consider** — indexing hints, CTE refactoring, performance notes

---

### Optimizing slow queries

1. Load the optimization guide:
   `read_skill_resource("sql-coding/references/OPTIMIZATION.md")`

2. Analyze the query structure — look for:
   - Missing indexes on JOIN or WHERE columns
   - SELECT * instead of specific columns
   - Subqueries that could be CTEs or joins
   - N+1 patterns in application code generating the SQL

3. Return:
   - Optimized query in a fenced ```sql block
   - List of indexes to add with exact CREATE INDEX statements
   - Explanation of what changed and why

---

### Schema design

1. Load the schema standards:
   `read_skill_resource("sql-coding/references/SCHEMA_STANDARDS.md")`

2. Load the migration template:
   `read_skill_resource("sql-coding/assets/migration-template.sql")`

3. Return:
   - CREATE TABLE statements in a fenced ```sql block
   - Migration script using the template
   - Index recommendations

---

## Output rules

- Always use lowercase SQL keywords (select, from, where — not SELECT FROM WHERE)
- Always alias tables in multi-table queries
- Never write UPDATE or DELETE without a WHERE clause
- Always use explicit column lists — never SELECT *  in production queries
- Use CTEs (WITH ...) for complex subqueries — never nested subqueries more than 1 level deep
- Parameterize values — never concatenate user input into SQL strings