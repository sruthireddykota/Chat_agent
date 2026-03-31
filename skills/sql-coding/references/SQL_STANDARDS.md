# SQL Coding Standards

## Formatting
- Lowercase keywords: `select`, `from`, `where`, `join`, `on`, `group by`, `order by`
- One clause per line for queries longer than 3 lines
- Indent continuation lines by 2 spaces

```sql
-- Correct
select
  u.id,
  u.email,
  count(o.id) as order_count
from users u
left join orders o on o.user_id = u.id
where u.created_at >= '2024-01-01'
group by u.id, u.email
order by order_count desc;

-- Wrong
SELECT u.id, u.email, COUNT(o.id) AS order_count FROM users u LEFT JOIN orders o ON o.user_id = u.id WHERE u.created_at >= '2024-01-01' GROUP BY u.id, u.email ORDER BY order_count DESC;
```

## Aliasing
- Always alias tables in multi-table queries — use short meaningful aliases
- Always alias aggregations and computed columns
- Never use single-letter aliases except `u` for users, `o` for orders (common conventions)

```sql
-- Correct
select
  u.id,
  u.email,
  p.name as plan_name
from users u
join plans p on p.id = u.plan_id

-- Wrong
select
  a.id,
  a.email,
  b.name
from users a
join plans b on b.id = a.plan_id
```

## Column Selection
- Never use `SELECT *` in production queries
- Always list columns explicitly
- Exception: exploratory one-off queries only — never in application code

## WHERE Clause Safety
- Never write `UPDATE` or `DELETE` without a `WHERE` clause
- For bulk operations, always test with `SELECT` first using the same `WHERE`

```sql
-- Safe pattern: test first
select count(*) from orders where status = 'pending' and created_at < now() - interval '90 days';

-- Then run
update orders
set status = 'expired'
where status = 'pending'
  and created_at < now() - interval '90 days';
```

## CTEs vs Subqueries
- Use CTEs (`WITH`) for any subquery referenced more than once
- Use CTEs to name and isolate complex logic
- Never nest subqueries more than 1 level deep

```sql
-- Correct: CTE
with active_users as (
  select id, email
  from users
  where last_login_at > now() - interval '30 days'
),
user_orders as (
  select user_id, count(*) as order_count
  from orders
  group by user_id
)
select
  u.email,
  coalesce(o.order_count, 0) as orders
from active_users u
left join user_orders o on o.user_id = u.id;
```

## Parameterization
- Never concatenate user input into SQL — always use parameterized queries
- Use `%s` (psycopg2), `?` (sqlite3), or `$1` (asyncpg) placeholders

```python
# Correct
cursor.execute("select * from users where email = %s", (email,))

# Wrong — SQL injection risk
cursor.execute(f"select * from users where email = '{email}'")
```

## Naming Conventions
- Tables: `snake_case`, plural nouns (`users`, `order_items`)
- Columns: `snake_case` (`created_at`, `user_id`, `is_active`)
- Primary keys: always named `id`
- Foreign keys: `<referenced_table_singular>_id` (`user_id`, `plan_id`)
- Boolean columns: prefix with `is_` or `has_` (`is_active`, `has_verified_email`)
- Timestamps: suffix with `_at` (`created_at`, `updated_at`, `deleted_at`)

## NULL Handling
- Use `IS NULL` / `IS NOT NULL` — never `= NULL`
- Use `COALESCE()` to provide defaults for nullable columns
- Consider `NOT NULL` constraints by default — add nullability only when needed