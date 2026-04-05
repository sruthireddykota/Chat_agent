#!/usr/bin/env python3
"""
validate_architecture.py

Validates a described architecture against core principles.
Accepts a text description of modules and dependencies and checks for:
  - Missing responsibility descriptions
  - Circular dependency declarations
  - Domain layer violations (imports from infrastructure/api)
  - God module indicators (too many responsibilities)
  - Missing interface definitions at boundaries
  - Anemic domain model indicators

Usage (via run_skill_script):
  run_skill_script("code-architecture", "scripts/validate_architecture.py",
    args={"input": "<module map or dependency description>"})

Input format (paste as the 'input' arg):
  Describe your modules and their dependencies in plain text or structured format.
  The more detail the better — include layer names, module names, what each does,
  and what each imports from.

  Example input:
    Layer: domain
      Module: user.py — represents a user entity with email and name
      Module: user_service.py — validates and creates users, imports from postgres.py

    Layer: infrastructure
      Module: postgres.py — handles database connections and queries

  The validator will flag: user_service.py (domain) imports from postgres.py (infrastructure)
"""

import sys
import re
from dataclasses import dataclass, field


@dataclass
class ValidationIssue:
    severity: str   # CRITICAL | MAJOR | MINOR
    rule: str
    location: str
    message: str
    suggestion: str


@dataclass
class ArchitectureReport:
    issues: list[ValidationIssue] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)

    def add_issue(self, severity, rule, location, message, suggestion):
        self.issues.append(ValidationIssue(severity, rule, location, message, suggestion))

    def add_pass(self, rule):
        self.passed.append(rule)

    @property
    def critical_count(self):
        return sum(1 for i in self.issues if i.severity == "CRITICAL")

    @property
    def major_count(self):
        return sum(1 for i in self.issues if i.severity == "MAJOR")

    @property
    def minor_count(self):
        return sum(1 for i in self.issues if i.severity == "MINOR")


# ── Layer definitions ─────────────────────────────────────────────────────────

INNER_LAYERS = {"domain", "core", "entities", "ports", "value_objects"}
OUTER_LAYERS = {"infrastructure", "infra", "db", "database", "http", "external"}
FRAMEWORK_LAYERS = {"api", "routes", "presentation", "controllers", "views"}
APP_LAYERS = {"application", "use_cases", "usecases", "services"}

DOMAIN_FORBIDDEN_IMPORTS = [
    "sqlalchemy", "postgres", "postgresql", "mysql", "mongodb", "mongo",
    "redis", "elasticsearch", "fastapi", "flask", "django", "starlette",
    "httpx", "requests", "aiohttp", "boto3", "azure", "google.cloud",
    "celery", "dramatiq", "kafka", "rabbitmq", "pika", "os.environ",
    "subprocess", "socket",
]

GOD_MODULE_INDICATORS = [
    "utils", "helpers", "misc", "common", "shared", "base",
    "manager", "handler", "processor",
]

# ── Validators ────────────────────────────────────────────────────────────────

def check_domain_isolation(text: str, report: ArchitectureReport):
    """Domain must not import from infrastructure, API, or frameworks."""
    lines = text.lower().split("\n")

    in_domain_section = False
    in_infra_section = False
    domain_violations = []

    for i, line in enumerate(lines, 1):
        # Detect domain section start
        if any(layer in line for layer in INNER_LAYERS):
            if "layer:" in line or "section:" in line or line.strip().startswith("#"):
                in_domain_section = True
                in_infra_section = False

        # Detect infrastructure/api section start — stop checking as domain
        if any(f"{layer}:" in line or f"{layer} layer" in line
               for layer in (OUTER_LAYERS | FRAMEWORK_LAYERS | APP_LAYERS)):
            in_domain_section = False
            in_infra_section = True

        # Only check lines that are in domain context AND reference an import
        # Skip lines that are themselves infrastructure module declarations
        if in_domain_section and not in_infra_section:
            is_infra_declaration = any(
                infra_word in line for infra_word in
                ["infrastructure/", "infra/", "postgres_", "mysql_", "redis_", "mongo_"]
            ) and any(
                decl in line for decl in ["module:", "class:", "file:", "implements"]
            )
            # Must have explicit import language — not just a name mention
            if not is_infra_declaration and ("import" in line or "depends on" in line):
                for forbidden in DOMAIN_FORBIDDEN_IMPORTS:
                    if forbidden in line:
                        domain_violations.append((i, forbidden, line.strip()))

    if domain_violations:
        for line_num, forbidden, line_text in domain_violations:
            report.add_issue(
                severity="CRITICAL",
                rule="Domain Isolation",
                location=f"line {line_num}",
                message=f"Domain layer references '{forbidden}' — infrastructure/framework detail in domain.",
                suggestion=(
                    f"Define a Protocol in domain/ports/ that abstracts what the domain needs. "
                    f"Move the {forbidden} implementation to infrastructure/. "
                    f"Inject it via the port interface."
                )
            )
    else:
        report.add_pass("Domain Isolation")


def check_circular_dependencies(text: str, report: ArchitectureReport):
    """Detect declared circular dependencies."""
    # Look for patterns like "A imports B" and "B imports A"
    import_pattern = re.compile(
        r"(\w[\w_/\.]+)\s+(?:imports?|depends? on|uses?)\s+(\w[\w_/\.]+)",
        re.IGNORECASE
    )

    edges = []
    for match in import_pattern.finditer(text):
        source = match.group(1).lower().strip()
        target = match.group(2).lower().strip()
        if source != target:
            edges.append((source, target))

    # Check for direct cycles A→B and B→A
    cycles_found = []
    for source, target in edges:
        if (target, source) in edges:
            pair = tuple(sorted([source, target]))
            if pair not in cycles_found:
                cycles_found.append(pair)
                report.add_issue(
                    severity="CRITICAL",
                    rule="No Circular Dependencies",
                    location=f"{source} ↔ {target}",
                    message=f"Circular dependency detected: {source} and {target} depend on each other.",
                    suggestion=(
                        f"Extract the shared interface into a third module (e.g. domain/ports/). "
                        f"Both {source} and {target} should depend on the interface, not on each other."
                    )
                )

    # Check for indirect cycles (A→B→C→A)
    def find_path(graph, start, end, visited=None):
        if visited is None:
            visited = set()
        if start == end and visited:
            return True
        if start in visited:
            return False
        visited.add(start)
        for _, target in [(s, t) for s, t in graph if s == start]:
            if find_path(graph, target, end, visited.copy()):
                return True
        return False

    for source, target in edges:
        if (source, target) not in [(a, b) for a, b in cycles_found]:
            if find_path(edges, target, source):
                report.add_issue(
                    severity="CRITICAL",
                    rule="No Circular Dependencies",
                    location=f"{source} → ... → {target} → {source}",
                    message=f"Indirect circular dependency: {source} eventually depends on itself via {target}.",
                    suggestion=(
                        "Map the full dependency chain and find the weakest link to break. "
                        "Extract an interface at that point and invert the dependency."
                    )
                )

    if not cycles_found:
        report.add_pass("No Circular Dependencies")


def check_single_responsibility(text: str, report: ArchitectureReport):
    """Flag modules with multiple apparent responsibilities."""
    module_pattern = re.compile(
        r"(?:module|class|file)[\s:]+(\w[\w_\.]+)[^\n]*\n([^\n]+)",
        re.IGNORECASE
    )

    multi_responsibility_words = [
        " and ", " also ", " additionally ", " plus ", " as well as ",
        ", handles ", ", manages ", ", processes ",
    ]

    for match in module_pattern.finditer(text):
        module_name = match.group(1)
        description = match.group(2).lower()

        violations = [word for word in multi_responsibility_words if word in description]
        if violations:
            report.add_issue(
                severity="MAJOR",
                rule="Single Responsibility",
                location=module_name,
                message=f"Module description suggests multiple responsibilities: '{match.group(2).strip()}'",
                suggestion=(
                    f"Split {module_name} into separate modules, one per responsibility. "
                    "Each module description should contain no 'and' or 'also'."
                )
            )

    # Check for god module names
    text_lower = text.lower()
    for indicator in GOD_MODULE_INDICATORS:
        pattern = rf"\b{indicator}\.py\b|\b{indicator}/\b"
        if re.search(pattern, text_lower):
            report.add_issue(
                severity="MINOR",
                rule="Single Responsibility",
                location=indicator,
                message=f"Module name '{indicator}' is a common god module indicator.",
                suggestion=(
                    f"Rename '{indicator}' to describe its specific responsibility. "
                    "If it truly contains multiple utilities, split it into focused modules."
                )
            )


def check_dependency_direction(text: str, report: ArchitectureReport):
    """Check that dependencies point inward (outer → inner, never inner → outer)."""
    violations = []

    # Patterns indicating wrong direction
    wrong_direction_patterns = [
        (r"domain.*import.*infrastructure", "domain imports from infrastructure"),
        (r"domain.*import.*api", "domain imports from api layer"),
        (r"domain.*import.*route", "domain imports from route layer"),
        (r"domain.*import.*controller", "domain imports from controller"),
        (r"entity.*import.*repository", "entity imports from repository"),
        (r"domain.*import.*fastapi", "domain imports from FastAPI"),
        (r"domain.*import.*flask", "domain imports from Flask"),
        (r"core.*import.*infra", "core imports from infrastructure"),
    ]

    text_lower = text.lower()
    for pattern, description in wrong_direction_patterns:
        if re.search(pattern, text_lower):
            violations.append(description)

    for v in violations:
        report.add_issue(
            severity="CRITICAL",
            rule="Dependency Direction",
            location="dependency graph",
            message=f"Wrong dependency direction detected: {v}.",
            suggestion=(
                "Dependencies must only point inward: api → application → domain. "
                "Infrastructure implements domain interfaces — it imports from domain, not vice versa. "
                "Define a Protocol in domain/ports/ and inject the implementation."
            )
        )

    if not violations:
        report.add_pass("Dependency Direction")


def check_interface_definitions(text: str, report: ArchitectureReport):
    """Check that boundaries between layers have defined interfaces."""
    has_ports = any(word in text.lower() for word in [
        "protocol", "abc", "abstractmethod", "interface", "port", "ports/",
        "domain/ports", "abstract base"
    ])

    has_multiple_layers = sum(
        1 for layer_set in [INNER_LAYERS, OUTER_LAYERS, APP_LAYERS, FRAMEWORK_LAYERS]
        if any(layer in text.lower() for layer in layer_set)
    )

    if has_multiple_layers >= 2 and not has_ports:
        report.add_issue(
            severity="MAJOR",
            rule="Interface Definitions",
            location="architecture boundaries",
            message="Multiple layers detected but no interface definitions (Protocol/ABC) found.",
            suggestion=(
                "Define a Protocol or ABC for every boundary between layers. "
                "Place interfaces in domain/ports/ — this is what infrastructure implements "
                "and what the application layer depends on. "
                "Example: class UserRepository(Protocol): def find_by_id(self, id: str) -> User | None: ..."
            )
        )
    elif has_ports:
        report.add_pass("Interface Definitions")


def check_testability(text: str, report: ArchitectureReport):
    """Check for patterns that indicate testability problems."""
    text_lower = text.lower()

    issues = []

    if "global" in text_lower and ("state" in text_lower or "variable" in text_lower):
        issues.append("Global state detected — functions depending on global state cannot be unit tested.")

    if "singleton" in text_lower:
        issues.append("Singleton pattern — singletons are often untestable without modification.")

    if re.search(r"os\.environ.*(?:domain|service|logic|business)", text_lower):
        issues.append("os.environ accessed in domain/service layer — inject config values instead.")

    if re.search(r"(?:datetime|time)\.now\(\).*(?:domain|service|entity)", text_lower):
        issues.append("datetime.now() in domain — inject a Clock interface to make time testable.")

    for issue in issues:
        report.add_issue(
            severity="MAJOR",
            rule="Testability",
            location="design",
            message=issue,
            suggestion=(
                "Pass dependencies (including time, randomness, config) via constructor injection. "
                "Pure functions and injected dependencies make every component independently testable."
            )
        )

    if not issues:
        report.add_pass("Testability")


def check_anemic_domain(text: str, report: ArchitectureReport):
    """Flag signs of an anemic domain model."""
    text_lower = text.lower()

    # Anemic signals: entities described as data-only, all logic in services
    anemic_signals = [
        (r"entity.*(?:only|just).*(?:data|fields|attributes)", "Entity described as data-only"),
        (r"model.*no.*(?:method|logic|behaviour|behavior)", "Model with no behaviour"),
        (r"all.*(?:business logic|logic).*(?:in service|in manager)", "All logic in service layer"),
        (r"entity.*(?:dto|data transfer|plain data)", "Entity treated as DTO"),
    ]

    for pattern, description in anemic_signals:
        if re.search(pattern, text_lower):
            report.add_issue(
                severity="MAJOR",
                rule="Rich Domain Model",
                location="domain entities",
                message=f"Anemic domain indicator: {description}.",
                suggestion=(
                    "Move business logic into domain entities. "
                    "Entities should enforce their own invariants and contain domain behaviour. "
                    "Use @dataclass(frozen=True) and __post_init__ for validation. "
                    "Favour methods that return new state over mutating setters."
                )
            )


# ── Report formatter ─────────────────────────────────────────────────────────

def format_report(report: ArchitectureReport, input_length: int) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("ARCHITECTURE VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append(f"Input analysed: {input_length} characters")
    lines.append(f"Issues found:   {len(report.issues)} "
                 f"({report.critical_count} critical, "
                 f"{report.major_count} major, "
                 f"{report.minor_count} minor)")
    lines.append(f"Rules passed:   {len(report.passed)}")
    lines.append("")

    if report.issues:
        # Critical first
        for severity in ["CRITICAL", "MAJOR", "MINOR"]:
            severity_issues = [i for i in report.issues if i.severity == severity]
            if severity_issues:
                lines.append(f"── {severity} ({'MUST FIX' if severity == 'CRITICAL' else 'SHOULD FIX' if severity == 'MAJOR' else 'CONSIDER'}) ──")
                for issue in severity_issues:
                    lines.append(f"\n  Rule:     {issue.rule}")
                    lines.append(f"  Location: {issue.location}")
                    lines.append(f"  Problem:  {issue.message}")
                    lines.append(f"  Fix:      {issue.suggestion}")
                lines.append("")

    if report.passed:
        lines.append("── PASSED ──")
        for rule in report.passed:
            lines.append(f"  ✓ {rule}")
        lines.append("")

    lines.append("=" * 60)

    if report.critical_count > 0:
        lines.append("VERDICT: FAIL — Fix all CRITICAL issues before proceeding.")
    elif report.major_count > 0:
        lines.append("VERDICT: CONDITIONAL PASS — Address MAJOR issues before finalising.")
    elif report.minor_count > 0:
        lines.append("VERDICT: PASS — Minor improvements recommended.")
    else:
        lines.append("VERDICT: PASS — Architecture satisfies all checked principles.")

    lines.append("=" * 60)

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    input_text = ""

    # Accept input from args dict (run_skill_script passes as 'input' key)
    if len(sys.argv) > 1:
        import json
        try:
            args = json.loads(sys.argv[1])
            input_text = args.get("input", "")
        except (json.JSONDecodeError, KeyError):
            input_text = " ".join(sys.argv[1:])

    if not input_text:
        print("No input provided. Pass your module map or architecture description as 'input'.")
        print("Example: run_skill_script('code-architecture', 'scripts/validate_architecture.py',")
        print("         args={'input': 'domain/user.py imports from infrastructure/postgres.py'})")
        sys.exit(1)

    report = ArchitectureReport()

    # Run all validators
    check_domain_isolation(input_text, report)
    check_circular_dependencies(input_text, report)
    check_single_responsibility(input_text, report)
    check_dependency_direction(input_text, report)
    check_interface_definitions(input_text, report)
    check_testability(input_text, report)
    check_anemic_domain(input_text, report)

    print(format_report(report, len(input_text)))

    # Exit code: 1 if critical issues, 0 otherwise
    sys.exit(1 if report.critical_count > 0 else 0)


if __name__ == "__main__":
    main()
