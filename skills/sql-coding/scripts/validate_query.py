#!/usr/bin/env python3
"""
validate_query.py

Reads a SQL query from stdin and checks it against safety and style rules.
Uses stdlib only — no database connection required.

Checks:
  - UPDATE/DELETE without WHERE clause (dangerous)
  - SELECT * usage
  - SQL injection risk patterns (string concatenation signs)
  - Missing table aliases in multi-table queries
  - Subquery nesting depth
  - Unparameterized literals that look like user input

Usage:
    echo "<sql query>" | python3 validate_query.py
    python3 validate_query.py < query.sql
"""
import sys
import re
from dataclasses import dataclass


@dataclass
class Issue:
    severity: str   # MUST | SHOULD | CONSIDER
    line: int
    message: str


def normalize(sql: str) -> str:
    """Lowercase and collapse whitespace for pattern matching."""
    return re.sub(r'\s+', ' ', sql.lower().strip())


def count_tables(sql: str) -> int:
    """Rough estimate of how many tables are referenced."""
    norm = normalize(sql)
    joins = len(re.findall(r'\bjoin\b', norm))
    return joins + 1


def check_query(sql: str) -> list[Issue]:
    issues: list[Issue] = []
    lines = sql.splitlines()
    norm = normalize(sql)

    # UPDATE without WHERE
    if re.search(r'\bupdate\b', norm):
        if not re.search(r'\bwhere\b', norm):
            issues.append(Issue(
                severity="MUST",
                line=1,
                message="UPDATE statement has no WHERE clause — this will update every row"
            ))

    # DELETE without WHERE
    if re.search(r'\bdelete\b', norm):
        if not re.search(r'\bwhere\b', norm):
            issues.append(Issue(
                severity="MUST",
                line=1,
                message="DELETE statement has no WHERE clause — this will delete every row"
            ))

    # SELECT *
    if re.search(r'select\s+\*', norm):
        issues.append(Issue(
            severity="SHOULD",
            line=1,
            message="SELECT * found — list columns explicitly for production queries"
        ))

    # String concatenation that looks like SQL injection risk
    for i, line in enumerate(lines, start=1):
        if re.search(r'["\']?\s*\+\s*["\']?\s*(user|input|param|query|search|name|email)', line.lower()):
            issues.append(Issue(
                severity="MUST",
                line=i,
                message="Possible string concatenation into SQL — use parameterized queries (%s / ? / $1)"
            ))

    # Deeply nested subqueries
    depth = 0
    max_depth = 0
    for char in sql:
        if char == '(':
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == ')':
            depth -= 1
    if max_depth > 3:
        issues.append(Issue(
            severity="SHOULD",
            line=1,
            message=f"Query has deep nesting (depth ~{max_depth}) — refactor with CTEs for readability"
        ))

    # Missing aliases in multi-table query
    table_count = count_tables(sql)
    if table_count > 1:
        # Check if any columns are referenced without a table prefix
        unaliased = re.findall(r'(?<!\w\.)(?<!\bfrom\s)(?<!\bjoin\s)\b([a-z_]+)\b(?=\s*[=,\)])', norm)
        # Rough heuristic — flag if no aliases detected at all
        alias_pattern = re.search(r'\b(from|join)\s+\w+\s+(\w+)\b', norm)
        if not alias_pattern:
            issues.append(Issue(
                severity="SHOULD",
                line=1,
                message=f"Multi-table query ({table_count} tables) detected — add table aliases for clarity"
            ))

    # UPPERCASE keywords (style)
    uppercase_keywords = re.findall(r'\b(SELECT|FROM|WHERE|JOIN|UPDATE|DELETE|INSERT|GROUP|ORDER|HAVING)\b', sql)
    if uppercase_keywords:
        issues.append(Issue(
            severity="CONSIDER",
            line=1,
            message=f"Uppercase SQL keywords found ({', '.join(set(uppercase_keywords))}) — prefer lowercase per style guide"
        ))

    # OR in WHERE without parentheses (logic error risk)
    if re.search(r'\bwhere\b.+\band\b.+\bor\b', norm) or re.search(r'\bwhere\b.+\bor\b.+\band\b', norm):
        if not re.search(r'\(.*\bor\b.*\)', norm):
            issues.append(Issue(
                severity="MUST",
                line=1,
                message="AND + OR in WHERE clause without parentheses — add parens to make precedence explicit"
            ))

    return sorted(issues, key=lambda x: (x.severity != "MUST", x.severity != "SHOULD", x.line))


def print_report(issues: list[Issue], sql: str) -> None:
    print("\nSQL VALIDATION REPORT")
    print("=" * 50)

    if not issues:
        print("✓ No issues found.\n")
        return

    must   = [i for i in issues if i.severity == "MUST"]
    should = [i for i in issues if i.severity == "SHOULD"]
    consider = [i for i in issues if i.severity == "CONSIDER"]

    print(f"Found {len(issues)} issue(s)\n")

    if must:
        print(f"MUST FIX ({len(must)})")
        print("-" * 40)
        for issue in must:
            print(f"  Line {issue.line}: {issue.message}")
        print()

    if should:
        print(f"SHOULD FIX ({len(should)})")
        print("-" * 40)
        for issue in should:
            print(f"  Line {issue.line}: {issue.message}")
        print()

    if consider:
        print(f"CONSIDER ({len(consider)})")
        print("-" * 40)
        for issue in consider:
            print(f"  Line {issue.line}: {issue.message}")
        print()
        
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=None,
                        help="SQL query text to validate")
    parsed, _ = parser.parse_known_args()

    if parsed.input:
        sql = parsed.input
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        sql = open(sys.argv[1]).read()
    elif not sys.stdin.isatty():
        sql = sys.stdin.read()
    else:
        print("Usage: provide --input '<sql>' or pipe via stdin")
        sys.exit(1)

    issues = check_query(sql)
    print_report(issues, sql)
    sys.exit(1 if any(i.severity == "MUST" for i in issues) else 0)