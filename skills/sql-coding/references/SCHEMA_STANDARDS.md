# SQL Schema Standards

Conventions for designing and altering database schemas.
Follow these when creating tables, writing migrations, or reviewing schema changes.

---

## Table Design Rules

### Naming
- Tables: `snake_case`, plural nouns — `users`, `order_items`, `api_keys`
- Never abbreviate — `user_permissions` not `usr_perms`
- Junction/join tables: `table_a_table_b` alphabetically — `role_users` not `user_roles`

### Every table must have
```sql
id          uuid primary key default gen_random_uuid(),
created_at  timestamptz not null default now(),
updated_at  timestamptz not null default now()
```

- Always use `uuid` for primary keys — never serial/integer for tables exposed via API
- Always use `timestamptz` (timezone-aware) not `timestamp`
- `updated_at` must be kept current via a trigger (see trigger template below)

### Column naming
- Foreign keys: `<singular_table_name>_id` — `user_id`, `plan_id`, `order_id`
- Booleans: prefix with `is_` or `has_` — `is_active`, `has_verified_email`
- Timestamps: suffix with `_at` — `created_at`, `deleted_at`, `last_login_at`
- Counts: suffix with `_count` — `order_count`, `retry_count`
- Amounts/money: suffix with `_cents` (store as integer) or use `numeric(12,2)`

### NULL policy
- Default to `NOT NULL` — add nullability only when the absence of a value is meaningful
- If a column can be empty, prefer empty string `''` over NULL for text
- Exception: `deleted_at` is always nullable (NULL = not deleted)

---

## Column Types

| Use case | Type | Notes |
|----------|------|-------|
| Primary key | `uuid` | Use `gen_random_uuid()` default |
| Foreign key | `uuid` | Match the referenced PK type |
| Short text | `text` | No length limit needed in PostgreSQL |
| Long text | `text` | Same — PostgreSQL handles storage |
| Boolean | `boolean` | Always `not null default false` |
| Integer count | `integer` | Use `bigint` if > 2B rows expected |
| Money/amount | `numeric(12,2)` | Never use `float` for money |
| JSON data | `jsonb` | Not `json` — jsonb is indexed and faster |
| Enum values | `text` with check constraint | Easier to alter than PostgreSQL enums |
| Timestamps | `timestamptz` | Never `timestamp` without timezone |
| IP address | `inet` | PostgreSQL native type |
| Email | `text` | Validate in application, not DB |

---

## Constraints

### Check constraints for enums
```sql
-- Prefer check constraints over PostgreSQL enum types
-- Reason: adding values to PG enums requires a table rewrite
alter table orders
add constraint chk_orders_status
check (status in ('pending', 'processing', 'completed', 'failed', 'refunded'));
```

### Unique constraints
```sql
-- Single column
alter table users add constraint uq_users_email unique (email);

-- Composite unique
alter table team_members
add constraint uq_team_members_team_user unique (team_id, user_id);

-- Partial unique (unique only among active records)
create unique index uq_users_email_active
on users(email)
where deleted_at is null;
```

### Foreign keys — always include ON DELETE behavior
```sql
-- Cascade: delete children when parent is deleted
user_id uuid not null references users(id) on delete cascade

-- Set null: orphan the child record
user_id uuid references users(id) on delete set null

-- Restrict (default): block parent deletion if children exist
user_id uuid not null references users(id) on delete restrict
```

---

## Indexes

### Index every foreign key column
```sql
-- Add after every foreign key constraint
create index idx_orders_user_id on orders(user_id);
create index idx_order_items_order_id on order_items(order_id);
```

### Index columns used in WHERE filters
```sql
-- Frequently filtered columns
create index idx_users_is_active on users(is_active) where is_active = true;
create index idx_orders_status on orders(status);
create index idx_users_created_at on users(created_at desc);
```

### Index columns used in ORDER BY
```sql
-- Pagination queries
create index idx_posts_published_at on posts(published_at desc)
where published_at is not null;
```

---

## updated_at Trigger

Every table with `updated_at` needs this trigger:

```sql
-- Create the function once per database
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Apply to each table
create trigger set_updated_at_users
before update on users
for each row execute function set_updated_at();
```

---

## Soft Delete Pattern

For tables that need audit history or recovery:

```sql
-- Add to any table needing soft delete
deleted_at timestamptz  -- null = active, timestamp = deleted

-- Always query with this filter
where deleted_at is null

-- Partial unique index respects soft delete
create unique index uq_users_email_active
on users(email)
where deleted_at is null;
```

---

## Schema Change Safety Rules

Before any ALTER TABLE in production:

1. **Adding a column** — safe if nullable or has a default
   ```sql
   -- Safe: nullable
   alter table users add column avatar_url text;

   -- Safe: has default (PostgreSQL 11+ doesn't rewrite the table)
   alter table users add column is_verified boolean not null default false;
   ```

2. **Dropping a column** — always do in two steps
   - Step 1: stop reading/writing the column in application code
   - Step 2: drop the column in next deployment

3. **Adding an index** — always use CONCURRENTLY to avoid table lock
   ```sql
   create index concurrently idx_users_email on users(email);
   ```

4. **Adding a NOT NULL constraint** — dangerous on large tables
   - Add as nullable first, backfill data, then add constraint
   ```sql
   -- Step 1: add nullable
   alter table orders add column processed_at timestamptz;
   -- Step 2: backfill
   update orders set processed_at = updated_at where processed_at is null;
   -- Step 3: add constraint
   alter table orders alter column processed_at set not null;
   ```

5. **Renaming a column** — always do in three steps
   - Step 1: add new column, dual-write
   - Step 2: backfill old → new, switch reads to new column
   - Step 3: drop old column