# SQL Query Patterns

Common patterns the coder agent should use when writing SQL.

---

## Pagination

```sql
-- Offset pagination (simple, less performant at scale)
select id, name, created_at
from users
order by created_at desc
limit 20 offset 40;

-- Keyset pagination (performant at scale — use for large tables)
select id, name, created_at
from users
where created_at < :last_seen_created_at
  or (created_at = :last_seen_created_at and id < :last_seen_id)
order by created_at desc, id desc
limit 20;
```

---

## Upsert (insert or update)

```sql
-- PostgreSQL
insert into user_settings (user_id, theme, notifications_enabled)
values (:user_id, :theme, :notifications_enabled)
on conflict (user_id)
do update set
  theme = excluded.theme,
  notifications_enabled = excluded.notifications_enabled,
  updated_at = now();
```

---

## Aggregation with filter

```sql
-- Count with conditional (avoid subquery)
select
  count(*) as total,
  count(*) filter (where is_active = true) as active_count,
  count(*) filter (where created_at > now() - interval '7 days') as new_this_week
from users;
```

---

## Running totals / window functions

```sql
select
  date_trunc('day', created_at) as day,
  count(*) as daily_signups,
  sum(count(*)) over (order by date_trunc('day', created_at)) as cumulative_signups
from users
group by day
order by day;
```

---

## Find duplicates

```sql
select email, count(*) as occurrences
from users
group by email
having count(*) > 1
order by occurrences desc;
```

---

## Soft delete pattern

```sql
-- Mark as deleted (never actually delete)
update users
set deleted_at = now()
where id = :user_id
  and deleted_at is null;

-- Query excluding deleted
select id, email
from users
where deleted_at is null;
```

---

## Bulk insert from values

```sql
insert into tags (name, slug, created_at)
values
  ('Python', 'python', now()),
  ('SQL', 'sql', now()),
  ('Async', 'async', now())
on conflict (slug) do nothing;
```

---

## Latest record per group

```sql
-- Get the most recent order per user
with ranked_orders as (
  select
    *,
    row_number() over (partition by user_id order by created_at desc) as rn
  from orders
)
select user_id, id as order_id, total, created_at
from ranked_orders
where rn = 1;
```

---

## Existence check (performant)

```sql
-- Prefer EXISTS over COUNT for existence checks
select exists (
  select 1
  from subscriptions
  where user_id = :user_id
    and status = 'active'
    and expires_at > now()
) as has_active_subscription;
```