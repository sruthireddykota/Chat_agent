# Architecture Patterns Catalogue

Use this reference to select the right pattern for a given system.
Each pattern includes: intent, when to use, when NOT to use, structure, and trade-offs.

---

## Pattern 1 — Layered Architecture

**Intent:** Organise code into horizontal layers where each layer serves the one above it.

**When to use:**
- Small to medium applications with a single team
- CRUD-heavy systems with straightforward business logic
- When simplicity is more important than flexibility
- When the team is new to architecture patterns

**When NOT to use:**
- Complex domain logic with many business rules
- Systems that need to swap infrastructure (e.g. change DB engine)
- Systems requiring high testability of business logic

**Structure:**
```
src/
  presentation/     ← HTTP routes, CLI commands, serialisation
  service/          ← business logic (often anemic here)
  repository/       ← data access
  models/           ← data models (often shared across layers)
```

**Dependency direction:** presentation → service → repository

**Trade-offs:**
- ✅ Simple to understand, small surface area
- ✅ Fast to build for simple use cases
- ❌ Business logic easily leaks into presentation or repository
- ❌ Hard to test service layer without hitting the database
- ❌ Changing the database affects every layer

---

## Pattern 2 — Clean Architecture (Recommended default)

**Intent:** Organise code in concentric circles. Inner circles define abstractions.
Outer circles implement them. Dependencies always point inward.

**When to use:**
- Any system with non-trivial business logic
- Systems that must be highly testable
- Systems where the database or framework might change
- Medium to large applications

**When NOT to use:**
- Very simple CRUD APIs with no business logic (overkill)
- Scripts or one-off tools

**Structure:**
```
src/
  domain/
    entities/       ← core business objects (dataclasses, frozen)
    value_objects/  ← immutable typed values (OrderId, Email, Money)
    ports/          ← interfaces the domain requires (Protocols/ABCs)
    services/       ← pure domain logic, no I/O
    exceptions/     ← domain-specific exception types
  application/
    use_cases/      ← one file per use case, orchestrates domain + ports
    dtos/           ← data transfer objects for use case boundaries
  infrastructure/
    db/             ← repository implementations (postgres, mongo, etc.)
    http/           ← external API clients
    messaging/      ← queue producers/consumers
    cache/          ← cache implementations
  api/
    routes/         ← HTTP route handlers (FastAPI routers)
    schemas/        ← Pydantic request/response schemas
    dependencies/   ← FastAPI dependency injection
  config/
    settings.py     ← pydantic-settings, loaded once at startup
    container.py    ← dependency wiring (manual DI)
```

**Dependency direction:**
```
api → application → domain ← infrastructure
                      ↑
            (ports defined here)
            (never imports from outside this circle)
```

**Trade-offs:**
- ✅ Domain logic is pure and trivially testable
- ✅ Infrastructure is swappable without touching domain
- ✅ Use cases are explicit and discoverable
- ❌ More files and indirection than layered
- ❌ Steeper learning curve for new team members
- ❌ DI wiring can become complex in large systems

**Python interface pattern:**
```python
# domain/ports/repositories.py
from typing import Protocol
from domain.entities.user import User

class UserRepository(Protocol):
    def find_by_id(self, user_id: str) -> User | None: ...
    def save(self, user: User) -> None: ...

# infrastructure/db/postgres_user_repository.py
from domain.ports.repositories import UserRepository  # depends inward only
from domain.entities.user import User

class PostgresUserRepository:                         # implements protocol
    def find_by_id(self, user_id: str) -> User | None: ...
    def save(self, user: User) -> None: ...

# application/use_cases/create_user.py
from domain.ports.repositories import UserRepository  # depends on abstraction
from domain.services.user_domain import UserDomain

class CreateUserUseCase:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, dto: CreateUserDTO) -> UserDTO:
        user = UserDomain.create(dto.email, dto.name)
        self.repo.save(user)
        return UserDTO.from_entity(user)
```

---

## Pattern 3 — Hexagonal Architecture (Ports and Adapters)

**Intent:** Same as clean architecture but emphasises the explicit naming of
"ports" (interfaces) and "adapters" (implementations). Good when you have many
external integrations.

**When to use:**
- Systems with many external integrations (multiple DBs, queues, APIs)
- When the same domain must be driven by different entry points (HTTP + CLI + events)
- When you want to make integration points explicit and visible

**Structure:**
```
src/
  domain/           ← pure business logic
  ports/
    inbound/        ← interfaces the domain EXPOSES (use case interfaces)
    outbound/       ← interfaces the domain REQUIRES (repo, notifier, etc.)
  adapters/
    inbound/
      http/         ← FastAPI routes (drives the domain)
      cli/          ← CLI commands (drives the domain)
      events/       ← event consumers (drives the domain)
    outbound/
      postgres/     ← DB implementation of outbound ports
      redis/        ← cache implementation
      sendgrid/     ← email implementation
      s3/           ← file storage implementation
```

**Key insight:** Ports are named from the domain's perspective.
- Inbound port: "here is how you can drive me"
- Outbound port: "here is what I need from the outside world"

**Trade-offs:**
- ✅ Every integration point is explicitly named and visible
- ✅ Easy to add new drivers (HTTP → also add CLI, events)
- ✅ Easy to swap adapters (postgres → mysql, sendgrid → ses)
- ❌ More structural overhead than clean architecture
- ❌ Risk of over-engineering for simple systems

---

## Pattern 4 — Pipeline Architecture

**Intent:** Process data through a sequence of stages, each stage transforms
the output of the previous one.

**When to use:**
- Data processing, ETL, document parsing, ML preprocessing
- When steps are independent and composable
- When you need to insert, remove, or reorder processing steps
- Systems like your RAG pipeline (parse → chunk → embed → store)

**Structure:**
```
src/
  pipeline/
    stages/
      __init__.py
      parse.py        ← Stage 1: raw input → structured data
      chunk.py        ← Stage 2: structured data → chunks
      embed.py        ← Stage 3: chunks → vectors
      store.py        ← Stage 4: vectors → persisted
    runner.py         ← orchestrates stages, handles errors
    models.py         ← data contracts between stages
    base.py           ← Stage protocol/ABC
```

**Python implementation:**
```python
# pipeline/base.py
from typing import Protocol, TypeVar

Input = TypeVar("Input")
Output = TypeVar("Output")

class Stage(Protocol[Input, Output]):
    def process(self, data: Input) -> Output: ...
    def can_handle(self, data: Input) -> bool: ...

# pipeline/runner.py
class PipelineRunner:
    def __init__(self, stages: list[Stage]):
        self.stages = stages

    def run(self, input_data):
        result = input_data
        for stage in self.stages:
            result = stage.process(result)
        return result
```

**Trade-offs:**
- ✅ Easy to add, remove, or reorder stages
- ✅ Each stage is independently testable
- ✅ Progress can be checkpointed between stages
- ❌ Data contracts between stages must be carefully managed
- ❌ Error handling across stages requires explicit design
- ❌ Not suitable for request/response systems

---

## Pattern 5 — Event-Driven Architecture

**Intent:** Components communicate by publishing and subscribing to events.
No component knows about others directly.

**When to use:**
- Systems where actions trigger side effects across multiple components
- When you need to decouple producers from consumers
- Audit logging, notifications, cache invalidation
- Systems with high write volumes where consistency can be eventual

**When NOT to use:**
- Simple request/response flows
- When strong consistency is required
- Small systems where the indirection adds no value

**Structure:**
```
src/
  events/
    definitions.py   ← event dataclasses (immutable)
    bus.py           ← event bus interface (Protocol)
    handlers/        ← one file per handler
  domain/
    services/        ← publish events, never subscribe
  infrastructure/
    events/
      in_memory_bus.py  ← for testing
      redis_bus.py      ← for production
```

**Python implementation:**
```python
# events/definitions.py
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class UserCreated:
    user_id: str
    email: str
    occurred_at: datetime

@dataclass(frozen=True)
class OrderFulfilled:
    order_id: str
    user_id: str
    occurred_at: datetime

# events/bus.py
from typing import Protocol, Callable, Type, TypeVar

E = TypeVar("E")

class EventBus(Protocol):
    def publish(self, event: object) -> None: ...
    def subscribe(self, event_type: Type[E], handler: Callable[[E], None]) -> None: ...

# events/handlers/send_welcome_email.py
from events.definitions import UserCreated

class SendWelcomeEmailHandler:
    def __init__(self, mailer: Mailer):
        self.mailer = mailer

    def handle(self, event: UserCreated) -> None:
        self.mailer.send_welcome(event.email)
```

**Trade-offs:**
- ✅ Loose coupling — producers don't know about consumers
- ✅ Easy to add new side effects without touching existing code
- ✅ Event log is an audit trail
- ❌ Hard to trace request flows (use correlation IDs)
- ❌ Eventual consistency requires careful error handling
- ❌ Testing requires wiring up bus + handlers together

---

## Pattern 6 — Agent/Tool Architecture (relevant to this codebase)

**Intent:** An orchestrator (agent) receives goals and selects tools to achieve them.
Tools are isolated units of capability with explicit inputs and outputs.

**When to use:**
- AI agent systems where the model drives execution
- When capabilities need to be composable and independently testable
- When tools need approval, logging, or rate limiting applied uniformly

**Structure:**
```
src/
  agent/
    orchestrator.py    ← agent loop, tool selection, message management
    instructions.py    ← system prompt builder
    context.py         ← session and history management
  tools/
    base.py            ← Tool protocol/ABC with standard signature
    filesystem.py      ← file I/O tools
    shell.py           ← command execution tools
    web_search.py      ← search tools
  skills/
    <skill-name>/
      SKILL.md         ← skill definition loaded into context
      scripts/         ← executable validation/generation scripts
      references/      ← reference documents read on demand
      assets/          ← templates and examples
  middleware/
    approval.py        ← tool call approval gate
    logging.py         ← structured tool call logging
    rate_limit.py      ← per-tool rate limiting
```

**Tool contract:**
```python
# tools/base.py
from typing import Protocol, Any

class Tool(Protocol):
    name: str
    description: str

    async def execute(self, **kwargs: Any) -> str: ...
    def validate_args(self, **kwargs: Any) -> bool: ...
```

**Trade-offs:**
- ✅ Tools are independently testable and replaceable
- ✅ Middleware (logging, approval) applied uniformly
- ✅ Skills allow context injection without bloating instructions
- ❌ Agent loop is non-deterministic — harder to test end-to-end
- ❌ Tool proliferation without discipline leads to confusion

---

## Pattern selection guide

Answer these questions to select the right pattern:

| Question | Answer → Pattern |
|---|---|
| Mostly CRUD, no complex logic? | Layered |
| Complex domain logic, must be testable? | Clean Architecture |
| Many external integrations? | Hexagonal |
| Processing data through sequential steps? | Pipeline |
| Actions triggering multiple side effects? | Event-Driven |
| AI agent driving tool use? | Agent/Tool |
| Complex system with multiple concerns? | Combine patterns |

**Combining patterns is normal.** A real system often uses:
- Clean Architecture for the domain
- Pipeline for a specific data processing feature
- Event-Driven for cross-cutting concerns (audit, notifications)
- Agent/Tool for AI-driven workflows
