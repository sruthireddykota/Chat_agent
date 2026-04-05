# Module Map: {System Name}

**Pattern:** {Layered | Clean Architecture | Hexagonal | Pipeline | Event-Driven | Agent/Tool}
**Date:** {YYYY-MM-DD}
**Status:** {Draft | Current | Outdated}

---

## Dependency Direction

```
{Draw the dependency arrow here}

Example for Clean Architecture:
  api/ → application/ → domain/ ← infrastructure/
                            ↑
                   (interfaces defined here)
                   (zero imports from outside)
```

---

## Layer Map

### Domain Layer
*No imports from application, infrastructure, or api layers.*

| Module | File | Responsibility |
|--------|------|----------------|
| {EntityName} | `domain/entities/{name}.py` | {One sentence} |
| {ValueObject} | `domain/value_objects/{name}.py` | {One sentence} |
| {PortName} | `domain/ports/{name}.py` | {One sentence — what interface this defines} |
| {DomainService} | `domain/services/{name}.py` | {One sentence — pure logic only} |
| {ExceptionName} | `domain/exceptions.py` | {One sentence} |

### Application Layer
*Imports from domain only. Orchestrates use cases.*

| Module | File | Responsibility |
|--------|------|----------------|
| {UseCaseName} | `application/use_cases/{name}.py` | {One sentence — what action this performs} |
| {DTOName} | `application/dtos/{name}.py` | {One sentence} |

### Infrastructure Layer
*Implements domain ports. Imports from domain (ports and entities) only.*

| Module | File | Implements |
|--------|------|------------|
| {RepoImpl} | `infrastructure/db/{name}.py` | `domain/ports/{port}.py` |
| {ClientImpl} | `infrastructure/http/{name}.py` | `domain/ports/{port}.py` |
| {CacheImpl} | `infrastructure/cache/{name}.py` | `domain/ports/{port}.py` |

### API Layer
*Entry points only. Imports from application (use cases + DTOs) only.*

| Module | File | Responsibility |
|--------|------|----------------|
| {RouterName} | `api/routes/{name}.py` | {One sentence} |
| {SchemaName} | `api/schemas/{name}.py` | {One sentence} |
| {DepName} | `api/dependencies/{name}.py` | {One sentence} |

### Configuration
| Module | File | Responsibility |
|--------|------|----------------|
| Settings | `config/settings.py` | All environment variables, validated at startup |
| Container | `config/container.py` | Dependency wiring — creates and injects all instances |

---

## Interface Contracts

Document every boundary between layers.

### {PortName} (domain/ports/{name}.py)

**Direction:** Domain defines → Infrastructure implements

```python
class {PortName}(Protocol):
    def {method_name}(self, {args}) -> {return_type}: ...
    def {method_name}(self, {args}) -> {return_type}: ...
```

**Implementations:**
- `infrastructure/{impl}.py` — {when/why this impl is used}
- `infrastructure/{fake_impl}.py` — used in tests only

---

## Dependency Graph

```
{Draw full dependency graph here}

Example:
  api/routes/user_routes.py
      ↓ imports
  application/use_cases/create_user.py
      ↓ imports
  domain/ports/user_repository.py   ← interface only
  domain/entities/user.py
  domain/services/user_domain.py

  infrastructure/postgres_user_repo.py
      ↓ imports (implementing the port)
  domain/ports/user_repository.py
  domain/entities/user.py

  config/container.py
      → creates PostgresUserRepository
      → injects into CreateUserUseCase
      → injects into UserRoutes
```

---

## What is testable in isolation

| Component | Test type | Requires |
|-----------|-----------|----------|
| Domain entities | Unit | Nothing — plain Python |
| Domain services | Unit | Nothing — plain Python |
| Use cases | Unit | Fake implementations of domain ports |
| Infrastructure | Integration | Real or embedded DB/service |
| API routes | Integration | FastAPI TestClient + fake use cases |

---

## Known violations / Technical debt

| Location | Violation | Severity | Planned fix |
|----------|-----------|----------|-------------|
| {file} | {description of violation} | Critical/Major/Minor | {ADR or ticket} |

---

## Change log

| Date | Change | Author |
|------|--------|--------|
| {date} | Initial module map | {name} |
| {date} | Added {feature} | {name} |
