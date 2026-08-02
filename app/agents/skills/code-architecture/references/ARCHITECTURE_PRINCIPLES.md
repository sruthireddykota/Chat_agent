# Architecture Principles

These principles apply to every design decision. Evaluate every proposed structure
against all of them before proceeding.

---

## 1. Single Responsibility

Every module, class, and function has exactly one reason to change.

**What this means in practice:**
- A module that handles both business logic AND database calls violates this
- A class that formats output AND validates input violates this
- If you struggle to write a one-sentence description of a module, it has too many responsibilities

**How to check:**
- Write one sentence describing the module's responsibility
- If the sentence contains "and", split the module
- If the sentence contains "or", the module has conditional responsibilities — split it

**Python example — violation:**
```python
# BAD: UserService does everything
class UserService:
    def create_user(self, data): ...       # business logic
    def save_to_db(self, user): ...        # database I/O
    def send_welcome_email(self, user): ... # external API
    def format_user_response(self, user): ... # serialisation
```

**Python example — correct:**
```python
# GOOD: each class has one job
class UserDomain:          # pure business logic
class UserRepository:      # database I/O only
class EmailNotifier:       # email sending only
class UserSerializer:      # serialisation only
```

---

## 2. Dependency Inversion

High-level modules must not depend on low-level modules.
Both must depend on abstractions. Abstractions must not depend on details.

**What this means in practice:**
- Domain layer defines interfaces (Protocols/ABCs)
- Infrastructure layer implements those interfaces
- Domain never imports from infrastructure
- Application layer wires them together

**Dependency direction rule — memorise this:**
```
API → Application → Domain ← Infrastructure
                      ↑
              (defines interfaces)
              (never imports from outside)
```

**Python example — violation:**
```python
# BAD: domain imports from infrastructure
# domain/user.py
from infrastructure.postgres import PostgresClient   # ← VIOLATION

class UserService:
    def __init__(self):
        self.db = PostgresClient()  # domain knows about postgres
```

**Python example — correct:**
```python
# domain/ports.py  ← interfaces live in domain
from typing import Protocol

class UserRepository(Protocol):
    def save(self, user: User) -> None: ...
    def find_by_id(self, user_id: str) -> User | None: ...

# domain/user_service.py  ← depends only on the protocol
class UserService:
    def __init__(self, repo: UserRepository):  # ← injected, not imported
        self.repo = repo

# infrastructure/postgres_user_repo.py  ← implements the protocol
class PostgresUserRepository:
    def save(self, user: User) -> None: ...
    def find_by_id(self, user_id: str) -> User | None: ...
```

---

## 3. Explicit Dependencies

Every dependency a module needs must be passed in — never fetched from globals,
singletons, or environment variables inside business logic.

**What this means in practice:**
- No `import settings` inside domain classes
- No `get_db()` calls inside service methods
- No global state that functions mutate
- Constructor injection is the default pattern

**Violation signals:**
- `os.environ.get(...)` inside a domain class
- `from config import settings` inside a service
- Module-level variables that accumulate state
- `global` keyword inside functions

**Python example — correct:**
```python
# Settings resolved at the boundary (main.py or DI container)
# and injected downward — never fetched inside domain
class ReportService:
    def __init__(
        self,
        repo: ReportRepository,
        notifier: Notifier,
        max_rows: int,          # ← config value injected, not fetched
    ):
        self.repo = repo
        self.notifier = notifier
        self.max_rows = max_rows
```

---

## 4. Separation of I/O and Logic

Pure logic (computation, validation, transformation) must be separated from I/O
(database, HTTP, filesystem, clock, random).

**Why this matters:**
- Pure functions are trivially testable — no mocks needed
- I/O functions require test doubles, which are expensive to maintain
- Mixing them means you can never test logic without I/O

**The rule:**
- Functions that compute return values and take no I/O arguments are pure — keep them that way
- Functions that do I/O should do ONLY I/O, no logic
- The application layer orchestrates: call I/O to get data → call logic → call I/O to persist

**Python example:**
```python
# GOOD: pure logic function — zero I/O, trivially testable
def calculate_discount(price: Decimal, membership: MembershipTier) -> Decimal:
    if membership == MembershipTier.PREMIUM:
        return price * Decimal("0.20")
    return price * Decimal("0.10")

# GOOD: I/O function — only fetches/persists, no logic
class OrderRepository:
    def find_pending(self) -> list[Order]: ...
    def mark_fulfilled(self, order_id: str) -> None: ...

# GOOD: application layer orchestrates both
class FulfillOrderUseCase:
    def execute(self, order_id: str) -> None:
        order = self.repo.find_pending_by_id(order_id)  # I/O
        discount = calculate_discount(order.price, order.membership)  # pure logic
        order.apply_discount(discount)                   # pure logic
        self.repo.save(order)                            # I/O
        self.notifier.send_confirmation(order)           # I/O
```

---

## 5. Interface Segregation

Define small, focused interfaces rather than large ones.
Callers should not depend on methods they do not use.

**What this means in practice:**
- A repository with 15 methods is almost always too large
- Split by use case: `ReadUserRepository`, `WriteUserRepository`
- Each use case depends only on the interface it needs

**Python example:**
```python
# BAD: fat interface — every caller gets everything
class UserRepository(Protocol):
    def find_by_id(self, id: str) -> User: ...
    def find_by_email(self, email: str) -> User: ...
    def find_all(self) -> list[User]: ...
    def save(self, user: User) -> None: ...
    def delete(self, id: str) -> None: ...
    def bulk_import(self, users: list[User]) -> int: ...
    def export_csv(self) -> str: ...   # ← why is this in a repo?

# GOOD: split by purpose
class UserReader(Protocol):
    def find_by_id(self, id: str) -> User | None: ...
    def find_by_email(self, email: str) -> User | None: ...

class UserWriter(Protocol):
    def save(self, user: User) -> None: ...
    def delete(self, id: str) -> None: ...

class UserBulkOps(Protocol):
    def bulk_import(self, users: list[User]) -> int: ...
```

---

## 6. Open/Closed Principle

Modules should be open for extension, closed for modification.
Adding a new behaviour should not require editing existing code.

**What this means in practice:**
- Use Protocols/ABCs so new implementations can be added without changing callers
- Use strategy pattern for behaviour that varies
- Avoid long if/elif chains based on type — use polymorphism instead

**Violation signal:**
```python
# BAD: every new payment type requires editing this function
def process_payment(method: str, amount: Decimal):
    if method == "stripe":
        ...
    elif method == "paypal":
        ...
    elif method == "crypto":   # ← new type = edit existing code
        ...
```

**Correct:**
```python
# GOOD: new payment type = new class, no edits to existing code
class PaymentProcessor(Protocol):
    def charge(self, amount: Decimal) -> PaymentResult: ...

class StripeProcessor:
    def charge(self, amount: Decimal) -> PaymentResult: ...

class PayPalProcessor:
    def charge(self, amount: Decimal) -> PaymentResult: ...

# caller never changes when new processor is added
def process_payment(processor: PaymentProcessor, amount: Decimal):
    return processor.charge(amount)
```

---

## 7. Fail Fast and Explicitly

Validate at boundaries. Never let invalid data propagate deep into the system.
Errors must be specific and actionable.

**What this means in practice:**
- Validate and parse input at the entry point (API layer or use case boundary)
- Domain objects must be impossible to construct in an invalid state
- Use specific exception types — never raise `Exception("something went wrong")`
- Log with context — what operation, what input, what failed

**Python example:**
```python
# BAD: invalid state can exist
class Order:
    def __init__(self):
        self.items = []
        self.status = None   # ← None is not a valid status

# GOOD: invalid state is impossible
from dataclasses import dataclass
from enum import Enum, auto

class OrderStatus(Enum):
    PENDING = auto()
    CONFIRMED = auto()
    FULFILLED = auto()

@dataclass(frozen=True)
class Order:
    id: OrderId
    items: tuple[LineItem, ...]  # immutable — can't be emptied after creation
    status: OrderStatus          # can't be None — Enum enforces valid values

    def __post_init__(self):
        if not self.items:
            raise ValueError("Order must have at least one item")
```

---

## 8. Testability as a Design Constraint

If a component is hard to test, the design is wrong — not the tests.
Testability is a first-class architectural concern, not an afterthought.

**What this means in practice:**
- Every layer must be independently testable
- Domain logic tests: no mocks, no fixtures, no I/O
- Application layer tests: mock the I/O boundaries only
- Infrastructure tests: test against real or embedded instances, not mocked

**Testability checklist — check before finalising any design:**
- [ ] Can I test domain logic with plain function calls and assertions?
- [ ] Can I test use cases by injecting fake repositories?
- [ ] Can I test infrastructure in isolation from business logic?
- [ ] Does any test require more than 5 lines of setup? If yes, the design has hidden coupling.

---

## Summary checklist

Before finalising any architecture, verify:

- [ ] Every module has a one-sentence responsibility (no "and")
- [ ] Dependencies point inward only — domain has no imports from infra or API
- [ ] All dependencies are injected — no globals, singletons, or env fetches in logic
- [ ] I/O and logic are in separate functions/classes
- [ ] Interfaces are small and focused — no fat protocols
- [ ] New behaviour can be added without editing existing modules
- [ ] Invalid states are impossible to construct
- [ ] Every layer is independently testable
