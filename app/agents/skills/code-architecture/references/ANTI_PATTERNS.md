# Architecture Anti-Patterns

These are the most common design mistakes. Recognise them quickly and know how to fix them.
Each anti-pattern includes: name, symptoms, root cause, and the fix.

---

## 1. God Class / God Module

**Symptoms:**
- A single class or module with 500+ lines
- A file that imports from every other module in the project
- A class with methods that span database calls, business logic, email sending, and formatting
- Every new feature requires editing the same file

**Root cause:** Missing decomposition — the designer didn't identify separate responsibilities.

**Common names that signal this:** `utils.py`, `helpers.py`, `manager.py`, `service.py` (singular)

**Fix:**
1. List every responsibility the module has
2. Group related responsibilities together
3. Extract each group into its own module with a specific name
4. Define an interface at the boundary

```python
# BEFORE: god class
class UserManager:
    def create_user(self): ...        # domain
    def validate_email(self): ...     # domain
    def save_to_postgres(self): ...   # infrastructure
    def send_welcome_email(self): ... # infrastructure
    def format_json_response(self): ... # presentation
    def log_audit_event(self): ...    # cross-cutting

# AFTER: decomposed
class UserDomainService:    # domain logic only
class UserRepository:       # persistence only
class UserNotifier:         # notifications only
class UserSerializer:       # presentation only
# audit logging → middleware, not a class at all
```

---

## 2. Circular Imports

**Symptoms:**
- `ImportError: cannot import name X from partially initialized module Y`
- Two modules that import from each other
- A module map that forms a cycle: A → B → C → A

**Root cause:** Missing abstraction at the boundary between two modules.
When A and B need each other, they are coupled in both directions — meaning neither
can be understood or tested without the other.

**Fix:**
1. Identify what each module needs from the other
2. Extract that need into an interface in a third module
3. Both A and B depend on the interface — not on each other

```python
# BEFORE: circular
# user_service.py
from order_service import OrderService   # ← imports order

# order_service.py
from user_service import UserService     # ← imports user — CYCLE

# AFTER: extract shared interface
# domain/ports.py  ← new module, no imports from either
class UserReader(Protocol):
    def find_by_id(self, id: str) -> User: ...

# user_service.py — depends on port, not on order_service
# order_service.py — depends on UserReader port, not on user_service
```

**Detection:**
```bash
# Run this to detect circular imports in your project
python -c "
import sys, importlib
# or use the validate_architecture.py script in this skill
"
```

---

## 3. Leaky Abstraction

**Symptoms:**
- Domain code importing SQLAlchemy models, FastAPI objects, or Redis clients
- HTTP status codes appearing in business logic
- Database column names referenced in domain entities
- Framework-specific exceptions raised from domain services

**Root cause:** The domain layer is not properly isolated.
Infrastructure details have leaked through the abstraction boundary.

**Fix:** Define a clean interface at every layer boundary.
The domain must only know about its own types.

```python
# BEFORE: leaky domain
# domain/user_service.py
from sqlalchemy.orm import Session          # ← infrastructure leak
from fastapi import HTTPException           # ← framework leak

class UserService:
    def create_user(self, db: Session, ...):  # ← domain takes a DB session
        raise HTTPException(status_code=409)  # ← domain raises HTTP error

# AFTER: clean domain
# domain/user_service.py
from domain.ports import UserRepository     # ← domain's own interface
from domain.exceptions import UserAlreadyExistsError  # ← domain's own exception

class UserService:
    def __init__(self, repo: UserRepository): ...
    def create_user(self, ...) -> User:
        raise UserAlreadyExistsError(email)  # ← domain exception only
```

---

## 4. Anemic Domain Model

**Symptoms:**
- Domain entities are plain data containers with no methods
- All business logic lives in "service" classes that manipulate entities
- Entity fields are all public and mutable
- You can construct an entity in an invalid state

**Root cause:** Treating domain objects as DTOs. The domain has no behaviour —
it's just a data structure that services manipulate.

**Fix:** Move business logic into the entity. Entities should enforce their own invariants.

```python
# BEFORE: anemic
@dataclass
class Order:
    items: list
    status: str      # can be anything — "WHATEVER" is valid
    total: float     # can be negative

class OrderService:
    def add_item(self, order: Order, item): ...     # logic outside entity
    def calculate_total(self, order: Order): ...    # logic outside entity
    def confirm_order(self, order: Order): ...      # logic outside entity

# AFTER: rich domain model
@dataclass
class Order:
    _items: tuple[LineItem, ...]
    _status: OrderStatus      # Enum — only valid statuses possible
    _id: OrderId

    def add_item(self, item: LineItem) -> "Order":
        if self._status != OrderStatus.DRAFT:
            raise OrderNotEditableError(self._id)
        return replace(self, items=(*self._items, item))  # immutable update

    def confirm(self) -> "Order":
        if not self._items:
            raise EmptyOrderError(self._id)
        return replace(self, status=OrderStatus.CONFIRMED)

    @property
    def total(self) -> Money:
        return sum(item.subtotal for item in self._items)
```

---

## 5. Hidden Side Effects

**Symptoms:**
- Functions that look like queries but modify state
- Functions that send emails, write files, or call APIs as a side effect of a get/find operation
- Tests that pass in isolation but fail when run together
- Global variables that accumulate state between calls

**Root cause:** Side effects are not visible from the function signature.
The caller cannot know what the function will do beyond its return value.

**Fix:** Make side effects explicit. Functions that cause side effects must be named
and structured to make this obvious.

```python
# BEFORE: hidden side effect
def get_user(user_id: str) -> User:
    user = db.query(user_id)
    audit_log.write(f"user {user_id} accessed")  # ← hidden side effect
    user.last_accessed = datetime.now()           # ← hidden mutation
    db.commit()                                   # ← hidden write
    return user

# AFTER: explicit
def find_user(user_id: str) -> User:             # pure query
    return db.query(user_id)

def record_user_access(user_id: str) -> None:    # explicit side effect
    audit_log.write(f"user {user_id} accessed")
    db.execute("UPDATE users SET last_accessed = NOW() WHERE id = ?", user_id)

# caller sees both operations explicitly
user = find_user(user_id)
record_user_access(user_id)
```

---

## 6. Deep Inheritance

**Symptoms:**
- Class hierarchies more than 2 levels deep
- Subclasses that override parent methods with completely different behaviour
- Using inheritance to share utility code (not to model is-a relationships)
- Difficulty understanding a class without reading all its ancestors

**Root cause:** Inheritance is being used for code reuse instead of for
modelling genuine is-a relationships.

**Fix:** Prefer composition over inheritance. Use Protocols for interfaces.
Use mixins only for narrow, stateless cross-cutting concerns.

```python
# BEFORE: deep inheritance for code reuse
class Base:
    def connect(self): ...
    def log(self): ...

class Repository(Base):
    def query(self): ...

class UserRepository(Repository):
    def find_user(self): ...

class CachingUserRepository(UserRepository):  # 3 levels deep
    def find_user(self): ...  # overrides parent completely

# AFTER: composition
class UserRepository:
    def __init__(self, db: DatabaseClient, cache: CacheClient, logger: Logger):
        self.db = db
        self.cache = cache
        self.logger = logger

    def find_by_id(self, user_id: str) -> User | None:
        if cached := self.cache.get(user_id):
            return cached
        user = self.db.query(user_id)
        self.cache.set(user_id, user)
        return user
```

---

## 7. Premature Abstraction

**Symptoms:**
- Interfaces with only one implementation
- Abstract base classes wrapping a single concrete class
- Generic frameworks built before the second use case exists
- "We might need this later" code

**Root cause:** Abstracting before the variation is understood.
Good abstractions emerge from real duplication — they cannot be designed in advance.

**Fix:** Follow the Rule of Three.
Duplicate once. Abstract when you have three concrete examples.
Wait until you understand the variation before naming the abstraction.

```python
# BEFORE: premature abstraction
class AbstractEmailSender(ABC):       # only one implementation exists
    @abstractmethod
    def send(self, to: str, body: str) -> None: ...

class ConcreteEmailSender(AbstractEmailSender):
    def send(self, to: str, body: str) -> None:
        sendgrid.send(to, body)

# AFTER: just the concrete class until a second implementation is needed
class EmailSender:
    def send(self, to: str, body: str) -> None:
        sendgrid.send(to, body)
# When you add SES, THEN extract the Protocol
```

---

## 8. Configuration Sprawl

**Symptoms:**
- `os.environ.get(...)` calls scattered across many modules
- Different modules reading the same env variable with different defaults
- No single place to see all configuration a system requires
- Tests that fail because an env variable isn't set

**Fix:** Centralise all configuration in a single settings module loaded at startup.
Use pydantic-settings for validation and type safety.

```python
# config/settings.py — single source of truth
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str
    mongo_uri: str
    coder_base_path: str = "/workspace/filemanager"
    max_messages: int = 8
    allow_sudo: bool = False
    allow_delete: bool = False

    class Config:
        env_file = ".env"

settings = Settings()   # loaded once, validated at startup

# Every module receives settings via injection — never calls os.environ directly
```

---

## Quick diagnosis table

| Symptom | Anti-pattern | Fix |
|---|---|---|
| One file imports everything | God module | Decompose by responsibility |
| `ImportError` on circular import | Circular import | Extract shared interface |
| Domain imports SQLAlchemy/FastAPI | Leaky abstraction | Define domain ports |
| Entities with no methods | Anemic domain | Move logic into entities |
| Tests interfere with each other | Hidden side effects | Make side effects explicit |
| Class hierarchy 3+ levels | Deep inheritance | Use composition |
| Interface with one impl | Premature abstraction | Wait for Rule of Three |
| `os.environ` everywhere | Config sprawl | Centralise in Settings |
