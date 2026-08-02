#!/usr/bin/env python3
"""
lint_check.py

Reads Python code from stdin and checks it against coding standards.
Uses only stdlib — no external linters required.

Checks:
  - Missing type hints on function signatures
  - Missing docstrings on public functions/classes
  - Bare except clauses
  - Mutable default arguments
  - Function length (> 100 lines)
  - Wildcard imports
  - Use of os.path (prefer pathlib)

Usage:
    echo "<python code>" | python3 lint_check.py
    python3 lint_check.py < myfile.py
"""
import sys
import ast
import re
from dataclasses import dataclass


@dataclass
class Issue:
    severity: str   # MUST | SHOULD | CONSIDER
    line: int
    message: str


def check_code(source: str) -> list[Issue]:
    issues: list[Issue] = []

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [Issue(severity="MUST", line=e.lineno or 0, message=f"Syntax error: {e.msg}")]

    lines = source.splitlines()

    for node in ast.walk(tree):

        # Missing type hints
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            if not func_name.startswith("_"):
                args = node.args
                all_args = args.args + args.posonlyargs + args.kwonlyargs
                untyped = [a.arg for a in all_args if a.annotation is None and a.arg != "self"]
                if untyped:
                    issues.append(Issue(
                        severity="MUST",
                        line=node.lineno,
                        message=f"Function '{func_name}' has untyped parameters: {', '.join(untyped)}"
                    ))
                if node.returns is None and func_name != "__init__":
                    issues.append(Issue(
                        severity="MUST",
                        line=node.lineno,
                        message=f"Function '{func_name}' is missing a return type annotation"
                    ))

            # Missing docstrings on public functions
            if not func_name.startswith("_"):
                if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                    issues.append(Issue(
                        severity="SHOULD",
                        line=node.lineno,
                        message=f"Function '{func_name}' is missing a docstring"
                    ))

            # Function length
            func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
            if func_lines > 100:
                issues.append(Issue(
                    severity="CONSIDER",
                    line=node.lineno,
                    message=f"Function '{func_name}' is {func_lines} lines — consider splitting (max 100)"
                ))

            # Mutable default arguments
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    issues.append(Issue(
                        severity="MUST",
                        line=node.lineno,
                        message=f"Function '{func_name}' has a mutable default argument — use None and set inside body"
                    ))

        # Missing docstrings on public classes
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                    issues.append(Issue(
                        severity="SHOULD",
                        line=node.lineno,
                        message=f"Class '{node.name}' is missing a docstring"
                    ))

        # Bare except
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append(Issue(
                    severity="MUST",
                    line=node.lineno,
                    message="Bare 'except:' clause — catch a specific exception instead"
                ))

        # Wildcard imports
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    issues.append(Issue(
                        severity="MUST",
                        line=node.lineno,
                        message=f"Wildcard import from '{node.module}' — import specific names instead"
                    ))

    # os.path usage (prefer pathlib) — raw line scan
    for i, line in enumerate(lines, start=1):
        if "os.path" in line and not line.strip().startswith("#"):
            issues.append(Issue(
                severity="CONSIDER",
                line=i,
                message="os.path detected — prefer pathlib.Path for file operations"
            ))

    return sorted(issues, key=lambda x: (x.line, x.severity))


def print_report(issues: list[Issue]) -> None:
    if not issues:
        print("✓ No issues found.")
        return

    must   = [i for i in issues if i.severity == "MUST"]
    should = [i for i in issues if i.severity == "SHOULD"]
    consider = [i for i in issues if i.severity == "CONSIDER"]

    print(f"\nLINT REPORT — {len(issues)} issue(s) found\n")

    if must:
        print(f"MUST FIX ({len(must)})")
        print("-" * 40)
        for issue in must:
            print(f"  Line {issue.line:>4}: {issue.message}")
        print()

    if should:
        print(f"SHOULD FIX ({len(should)})")
        print("-" * 40)
        for issue in should:
            print(f"  Line {issue.line:>4}: {issue.message}")
        print()

    if consider:
        print(f"CONSIDER ({len(consider)})")
        print("-" * 40)
        for issue in consider:
            print(f"  Line {issue.line:>4}: {issue.message}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=None,
                        help="code to lint")
    parsed, _ = parser.parse_known_args()

    if parsed.input:
        source = parsed.input
    elif not sys.stdin.isatty():
        source = sys.stdin.read()
    else:
        print("Usage: provide --input '<code>' or pipe via stdin")
        sys.exit(1)

    issues = check_code(source)
    print_report(issues)
    sys.exit(1 if any(i.severity == "MUST" for i in issues) else 0)