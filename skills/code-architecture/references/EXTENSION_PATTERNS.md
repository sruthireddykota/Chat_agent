# Extension Patterns

How to add new capabilities to an existing system without breaking it.
Use this reference when adding a significant feature to an existing codebase.

---

## The Core Rule

Adding a new feature should require:
- **Adding** new files and classes
- **Minimal edits** to existing files (wiring only — not logic changes)
- **Zero changes** to existing domain logic or interfaces

If adding a feature requires editing business logic in 5 existing files,
the architecture has a problem — not the feature.

---

## Extension Pattern 1 — New Implementation of Existing Interface

Use when: the feature is a new way of doing something the system already does.

**Example:** Adding a Redis cache alongside an existing Postgres repository.

```
Existing:
  domain/ports/user_repository.py  ← UserRepository Protocol (unchanged)
  infrastructure/postgres/user_repo.py  ← PostgresUserRepository (unchanged)

New files only:
  infrastructure/redis/user_cache.py   ← RedisUserRepository (new)
  infrastructure/composed/caching_user_repo.py  ← wraps postgres + redis (new)

Wiring change only:
  config/container.py  ← swap which implementation is injected (1 line change)
```

**Pattern:**
```python
# infrastructure/composed/caching_user_repo.py  ← NEW FILE
from domain.ports.user_repository import UserRepository
from domain.entities.user import User

class CachingUserRepository:
    """Wraps a primary repo with a cache layer. New file, zero changes to existing."""
    def __init__(self, primary: UserRepository, cache: CacheClient, ttl: int = 300):
        self.primary = primary
        self.cache = cache
        self.ttl = ttl

    def find_by_id(self, user_id: str) -> User | None:
        if cached := self.cache.get(f"user:{user_id}"):
            return cached
        user = self.primary.find_by_id(user_id)
        if user:
            self.cache.set(f"user:{user_id}", user, ttl=self.ttl)
        return user

    def save(self, user: User) -> None:
        self.primary.save(user)
        self.cache.delete(f"user:{user_id}")   # invalidate on write
```

---

## Extension Pattern 2 — New Use Case

Use when: the feature is a new action the system can perform.

**Example:** Adding "export user data" to a system that can already create and update users.

```
Existing:
  application/use_cases/create_user.py  (unchanged)
  application/use_cases/update_user.py  (unchanged)

New files only:
  application/use_cases/export_user_data.py   ← new use case
  application/dtos/export_request.py          ← new DTO
  domain/services/data_export_service.py      ← new domain logic if complex
  infrastructure/exporters/csv_exporter.py    ← new infrastructure
  api/routes/export_routes.py                 ← new route

Minimal wiring:
  api/router.py  ← include new router (1 line)
```

**Pattern:**
```python
# application/use_cases/export_user_data.py  ← NEW FILE
from domain.ports.user_repository import UserRepository
from domain.ports.exporters import DataExporter
from application.dtos.export_request import ExportUserDataDTO

class ExportUserDataUseCase:
    def __init__(self, repo: UserRepository, exporter: DataExporter):
        self.repo = repo
        self.exporter = exporter

    def execute(self, dto: ExportUserDataDTO) -> bytes:
        user = self.repo.find_by_id(dto.user_id)
        if not user:
            raise UserNotFoundError(dto.user_id)
        return self.exporter.export(user, format=dto.format)
```

---

## Extension Pattern 3 — New Event Handler

Use when: a new feature needs to react to something that already happens.

**Example:** Send a Slack notification when an order is fulfilled
(order fulfilment already exists and publishes `OrderFulfilled` event).

```
Existing:
  events/definitions.py  ← OrderFulfilled (unchanged)
  application/use_cases/fulfill_order.py  ← publishes OrderFulfilled (unchanged)

New files only:
  events/handlers/slack_order_notification.py  ← new handler
  infrastructure/slack/slack_client.py         ← new integration

Wiring:
  config/container.py  ← subscribe new handler to OrderFulfilled event (1 line)
```

**Pattern:**
```python
# events/handlers/slack_order_notification.py  ← NEW FILE
from events.definitions import OrderFulfilled

class SlackOrderNotificationHandler:
    def __init__(self, slack: SlackClient):
        self.slack = slack

    def handle(self, event: OrderFulfilled) -> None:
        self.slack.post(
            channel="#orders",
            message=f"Order {event.order_id} fulfilled for user {event.user_id}"
        )
```

---

## Extension Pattern 4 — New Port (Interface)

Use when: the feature requires a dependency that the domain doesn't currently have.

**Example:** Adding rate limiting to user creation — domain needs a RateLimiter.

```
New interface in domain:
  domain/ports/rate_limiter.py  ← NEW FILE

New implementation in infrastructure:
  infrastructure/redis/redis_rate_limiter.py  ← NEW FILE

Modified (minimally):
  application/use_cases/create_user.py  ← inject RateLimiter, add one check
  config/container.py  ← wire RedisRateLimiter to RateLimiter port
```

**Pattern:**
```python
# domain/ports/rate_limiter.py  ← NEW FILE
from typing import Protocol

class RateLimiter(Protocol):
    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        """Returns True if request is allowed, False if rate limit exceeded."""
        ...

# application/use_cases/create_user.py  ← MINIMAL EDIT
class CreateUserUseCase:
    def __init__(
        self,
        repo: UserRepository,
        notifier: Notifier,
        rate_limiter: RateLimiter,   # ← add parameter
    ): ...

    def execute(self, dto: CreateUserDTO) -> UserDTO:
        if not self.rate_limiter.check(dto.ip_address, limit=10, window_seconds=60):
            raise RateLimitExceededError()       # ← add check
        # rest of method unchanged
```

---

## Extension Pattern 5 — New Skill (for Agent/Tool systems)

Use when: adding a new capability domain to the coder agent.

```
New skill directory:
  skills/
    <new-skill>/
      SKILL.md              ← skill definition with entry point
      references/           ← reference documents
      assets/               ← templates
      scripts/              ← validation and generation scripts

No changes to:
  agents/Coder.py          ← universal skill protocol handles any new skill
  instructions             ← generic skill loading instructions handle any skill
```

**This is the extension pattern your codebase already uses well.**
The universal skill protocol in agent instructions means adding a skill
requires zero changes to any existing code.

---

## What to check before extending

Before adding any feature, verify these to avoid creating problems:

**1. Does the feature belong in an existing layer?**
- If it's pure logic → domain
- If it orchestrates domain + I/O → application use case
- If it's I/O → infrastructure
- If it's an entry point → api/adapters

**2. Does the feature create a new dependency?**
- If yes → define a new port in domain/ports first
- Then implement in infrastructure
- Then inject via container

**3. Does the feature modify an existing interface?**
- Adding optional parameters: OK with care
- Adding required parameters: breaking change — all callers must update
- Removing methods: breaking change — check all callers first
- Changing return type: breaking change — check all callers first

**4. Does the feature introduce a circular dependency?**
- Draw the dependency arrow before writing code
- If it points outward from domain → redesign
- If it creates a cycle → extract a shared interface

**5. Is the feature testable in isolation?**
- Can I write a unit test for the new use case with fake repositories?
- Can I test the new domain logic with plain function calls?
- If no → the design has hidden coupling, redesign before writing

---

## The delta checklist

Before starting implementation, produce this list:

```
New files:
  [ ] domain/ports/new_port.py
  [ ] application/use_cases/new_use_case.py
  [ ] infrastructure/new_impl.py
  [ ] api/routes/new_route.py

Modified files (wiring only):
  [ ] config/container.py  ← inject new implementation
  [ ] api/router.py        ← include new route

Unchanged files:
  [ ] all existing use cases
  [ ] all existing domain services
  [ ] all existing infrastructure implementations
```

If the "modified files" list contains domain logic or use case files (not just wiring),
revisit the design — the feature is likely coupled to existing logic in a way that
signals a missing abstraction.
