# Refactor Patterns

Safe, incremental steps for restructuring existing code without breaking behaviour.
Never attempt a big-bang rewrite. Always move in small, verified steps.

---

## Core Rule: The Strangler Fig

Always refactor by growing the new structure alongside the old one,
then migrating callers one by one, then deleting the old code.
Never delete before the replacement is working.

```
Phase 1: New structure exists alongside old (both work)
Phase 2: Callers migrated to new structure one at a time
Phase 3: Old structure deleted
```

---

## Refactor 1 — Extract Interface from Concrete Class

**When to use:** A class is used directly by many callers, making it impossible to test
those callers without instantiating the real class (and all its dependencies).

**Steps:**
```python
# Step 1: Define the Protocol based on what callers actually use
# (only the methods callers call — not every method the class has)
# domain/ports/email_sender.py
from typing import Protocol

class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...

# Step 2: Confirm the existing class satisfies the Protocol (no changes needed
# to the class — Python Protocols use structural subtyping)
# infrastructure/sendgrid_email_sender.py
class SendGridEmailSender:  # already satisfies EmailSender Protocol
    def send(self, to: str, subject: str, body: str) -> None: ...

# Step 3: Update callers to accept the Protocol, not the concrete class
# application/use_cases/create_user.py
# BEFORE: def __init__(self, sender: SendGridEmailSender):
# AFTER:
def __init__(self, sender: EmailSender):   # ← depends on abstraction now
    self.sender = sender

# Step 4: Update wiring in container.py (1 line — no logic changes)
# Step 5: Write tests using a fake implementation
class FakeEmailSender:
    def __init__(self):
        self.sent: list[dict] = []
    def send(self, to, subject, body):
        self.sent.append({"to": to, "subject": subject, "body": body})
```

---

## Refactor 2 — Extract Module from God Class

**When to use:** A single class or module has grown too large with multiple responsibilities.

**Steps:**
```python
# Step 1: List every responsibility in the class
# UserService does: validation, DB access, email, formatting

# Step 2: Group methods by responsibility
# Group A (domain logic): validate_email, check_duplicate, create_user_entity
# Group B (persistence):  save_user, find_user, delete_user
# Group C (notification): send_welcome_email, send_reset_email
# Group D (formatting):   to_dict, to_json, from_dict

# Step 3: Create new modules — one per group
# domain/user_domain.py     ← Group A
# infrastructure/user_repo.py  ← Group B
# infrastructure/user_notifier.py  ← Group C
# api/user_schema.py        ← Group D

# Step 4: Move methods one group at a time — keeping the original class working
# (temporarily delegate from old class to new class)
class UserService:  # temporarily delegates
    def __init__(self):
        self.repo = UserRepository()    # new class
        self.notifier = UserNotifier()  # new class

    def save_user(self, user):
        return self.repo.save(user)     # delegates to new class

# Step 5: Update callers to use new classes directly (one caller at a time)
# Step 6: Delete delegation methods and eventually the god class
```

---

## Refactor 3 — Break Circular Import

**When to use:** Two modules import from each other, causing ImportError
or making the dependency graph impossible to reason about.

**Steps:**
```python
# Problem:
# user_service.py imports OrderService
# order_service.py imports UserService

# Step 1: Identify exactly what each module needs from the other
# user_service needs: order_service.get_order_count(user_id)
# order_service needs: user_service.find_user(user_id)

# Step 2: Define interfaces for what each needs in a shared module
# domain/ports.py (new file — depends on nothing)
from typing import Protocol

class OrderCounter(Protocol):
    def count_for_user(self, user_id: str) -> int: ...

class UserFinder(Protocol):
    def find_by_id(self, user_id: str) -> User | None: ...

# Step 3: Update each module to depend on the Protocol, not on each other
# user_service.py
from domain.ports import OrderCounter  # ← replaces: from order_service import OrderService

class UserService:
    def __init__(self, order_counter: OrderCounter): ...

# order_service.py
from domain.ports import UserFinder  # ← replaces: from user_service import UserService

class OrderService:
    def __init__(self, user_finder: UserFinder): ...

# Step 4: Wire up in container.py
# UserService gets OrderService injected as OrderCounter
# OrderService gets UserService injected as UserFinder
# No circular imports — both depend on domain/ports.py which depends on nothing
```

---

## Refactor 4 — Push I/O to the Boundary

**When to use:** Business logic is mixed with database calls or HTTP calls,
making it impossible to test the logic without hitting real infrastructure.

**Steps:**
```python
# BEFORE: logic and I/O mixed
class ReportService:
    def generate_monthly_report(self, month: int, year: int) -> Report:
        # I/O
        orders = db.execute("SELECT * FROM orders WHERE month = ?", month, year)
        # Logic
        total = sum(o.amount for o in orders if o.status == "fulfilled")
        avg = total / len(orders) if orders else 0
        # More I/O
        db.execute("INSERT INTO reports ...", total, avg)
        # More logic
        return Report(total=total, average=avg, month=month, year=year)

# Step 1: Extract pure logic into a separate function
def calculate_report_metrics(orders: list[Order]) -> ReportMetrics:
    """Pure function — no I/O, takes data, returns data."""
    fulfilled = [o for o in orders if o.status == "fulfilled"]
    total = sum(o.amount for o in fulfilled)
    avg = total / len(fulfilled) if fulfilled else Decimal(0)
    return ReportMetrics(total=total, average=avg, count=len(fulfilled))

# Step 2: Extract I/O into repository methods
class ReportRepository:
    def find_orders_for_month(self, month: int, year: int) -> list[Order]: ...
    def save_report(self, report: Report) -> None: ...

# Step 3: Orchestrate in use case — I/O then logic then I/O
class GenerateMonthlyReportUseCase:
    def execute(self, month: int, year: int) -> Report:
        orders = self.repo.find_orders_for_month(month, year)  # I/O
        metrics = calculate_report_metrics(orders)             # pure logic
        report = Report(metrics=metrics, month=month, year=year)
        self.repo.save_report(report)                          # I/O
        return report
```

---

## Refactor 5 — Replace Inheritance with Composition

**When to use:** A class hierarchy has grown beyond 2 levels, or subclasses are
overriding parent behaviour in unexpected ways.

**Steps:**
```python
# BEFORE: deep inheritance
class BaseRepository:
    def connect(self): ...
    def log(self): ...

class PostgresRepository(BaseRepository):
    def query(self): ...

class UserRepository(PostgresRepository):  # 2 levels deep
    def find_user(self): ...

class CachingUserRepository(UserRepository):  # 3 levels deep — too deep
    def find_user(self): ...   # overrides completely

# Step 1: Identify what each level actually provides
# BaseRepository: connection + logging (cross-cutting)
# PostgresRepository: raw query execution
# UserRepository: user-specific queries
# CachingUserRepository: caching wrapper

# Step 2: Extract each as an independent component
class DatabaseClient:   # was BaseRepository
    def execute(self, query: str, *args): ...

class Logger:
    def info(self, message: str): ...

class UserRepository:   # flat — uses composition
    def __init__(self, db: DatabaseClient, logger: Logger):
        self.db = db
        self.logger = logger

    def find_by_id(self, user_id: str) -> User | None:
        self.logger.info(f"finding user {user_id}")
        return self.db.execute("SELECT ...", user_id)

class CachingUserRepository:  # wraps UserRepository — no inheritance
    def __init__(self, primary: UserRepository, cache: CacheClient):
        self.primary = primary
        self.cache = cache

    def find_by_id(self, user_id: str) -> User | None:
        if cached := self.cache.get(user_id):
            return cached
        return self.primary.find_by_id(user_id)
```

---

## Safe refactoring rules

Follow these to avoid breaking things during a refactor:

1. **One change at a time.** Extract one responsibility per commit.
   Never refactor and add features in the same change.

2. **Tests before refactor.** Write tests for the current behaviour first.
   If tests don't exist, write them before touching the code.
   The tests are your safety net — they verify the refactor didn't break behaviour.

3. **Compile (or import) after every step.** In Python, run:
   ```bash
   python -c "import src.<module>"
   ```
   after each step to catch import errors early.

4. **Run tests after every step.** Don't wait until the refactor is complete.

5. **Never rename and move in the same step.**
   First move (keep the name), then rename in a separate step.

6. **Keep the old interface during migration.**
   When moving a class, keep the original import working using a deprecation shim:
   ```python
   # old_location.py — temporary shim
   from new_location import UserService  # re-export for backward compat
   import warnings
   warnings.warn("Import from new_location instead", DeprecationWarning)
   ```

7. **Delete old code only after all callers are migrated.**
   Search for all references before deleting.
