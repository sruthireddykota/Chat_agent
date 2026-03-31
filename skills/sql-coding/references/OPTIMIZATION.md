# SQL Optimization Guide

Systematic approach to making slow queries faster.
Work through these steps in order — most gains come from steps 1-3.

---

## Step 1 — Run EXPLAIN ANALYZE first

Never optimize blind. Always get the query plan first:

```sql
explain (analyze, buffers, format text)
select ...;
```

Key things to look for in the output:
- **Seq Scan** on a large table → missing index
- **Nested Loop** with high rows estimate → join order or index problem
- **Hash Join** with high memory → consider work_mem setting
- **actual rows** much higher than **estimated rows** → stale statistics, run ANALYZE
- **Buffers: shared hit** vs **read** → cache miss ratio

---

## Step 2 — Index the right columns

### Add indexes for columns in WHERE clauses
```sql
-- Slow: sequential scan on large table
select * from orders where status = 'pending';

-- Fix: index on the filter column
create index idx_orders_status on orders(status);

-- Better: partial index if filtering a minority of rows
create index idx_orders_pending on orders(status)
where status = 'pending';
```

### Add indexes for JOIN columns
```sql
-- Every foreign key should have an index
create index idx_orders_user_id on orders(user_id);
```

### Composite indexes — column order matters
Put the most selective column first, then the sort/range column:
```sql
-- Query: where status = 'active' order by created_at desc
create index idx_users_status_created
on users(status, created_at desc);
```

### Covering indexes — include all queried columns
Avoids table heap access entirely:
```sql
-- Query selects only these columns
create index idx_users_email_name
on users(email)
include (name, created_at);
```

---

## Step 3 — Rewrite common slow patterns

### Replace SELECT * with explicit columns
```sql
-- Slow: fetches all columns including large text/jsonb fields
select * from users where id = $1;

-- Fast: only fetch what you need
select id, email, name from users where id = $1;
```

### Replace correlated subqueries with JOINs
```sql
-- Slow: runs subquery once per row
select u.id, u.email,
  (select count(*) from orders where user_id = u.id) as order_count
from users u;

-- Fast: single join + aggregate
select u.id, u.email, count(o.id) as order_count
from users u
left join orders o on o.user_id = u.id
group by u.id, u.email;
```

### Replace EXISTS subquery with JOIN where appropriate
```sql
-- Acceptable for existence check
select id from users u
where exists (
  select 1 from subscriptions s
  where s.user_id = u.id and s.status = 'active'
);

-- Often faster as a join for large tables
select distinct u.id
from users u
join subscriptions s on s.user_id = u.id
where s.status = 'active';
```

### Use CTEs to avoid repeated subqueries
```sql
-- Slow: same subquery computed multiple times
select *
from orders
where user_id in (select id from users where plan = 'pro')
  and amount > (select avg(amount) from orders where user_id in (select id from users where plan = 'pro'));

-- Fast: compute once
with pro_users as (
  select id from users where plan = 'pro'
),
avg_amount as (
  select avg(o.amount) as val
  from orders o
  join pro_users pu on pu.id = o.user_id
)
select o.*
from orders o
join pro_users pu on pu.id = o.user_id
cross join avg_amount a
where o.amount > a.val;
```

### Paginate large result sets
```sql
-- Slow for deep pages: offset 10000 still scans 10000 rows
select id, name from users order by created_at desc limit 20 offset 10000;

-- Fast: keyset pagination
select id, name, created_at
from users
where created_at < :last_seen_created_at
order by created_at desc
limit 20;
```

---

## Step 4 — Optimize aggregations

### Filter before aggregating
```sql
-- Slow: aggregates all rows then filters
select user_id, count(*)
from orders
group by user_id
having user_id in (select id from users where plan = 'pro');

-- Fast: filter first
select o.user_id, count(*)
from orders o
join users u on u.id = o.user_id
where u.plan = 'pro'
group by o.user_id;
```

### Use conditional aggregation instead of multiple queries
```sql
-- One pass instead of three queries
select
  count(*) as total,
  count(*) filter (where status = 'completed') as completed,
  count(*) filter (where status = 'failed') as failed,
  avg(amount) filter (where status = 'completed') as avg_completed_amount
from orders
where created_at >= now() - interval '30 days';
```

---

## Step 5 — Table-level optimizations

### Update stale statistics
```sql
analyze users;
analyze orders;
-- or all tables
analyze;
```

### Check table bloat
```sql
select
  relname as table_name,
  n_dead_tup as dead_rows,
  n_live_tup as live_rows,
  round(n_dead_tup::numeric / nullif(n_live_tup + n_dead_tup, 0) * 100, 1) as dead_pct
from pg_stat_user_tables
order by dead_pct desc nulls last;
```

If dead_pct > 20%, run:
```sql
vacuum analyze table_name;
```

### Check index usage
```sql
-- Find unused indexes (candidates for removal)
select
  schemaname,
  tablename,
  indexname,
  idx_scan as times_used
from pg_stat_user_indexes
where idx_scan = 0
order by tablename;
```

---

## Quick reference — optimization checklist

- [ ] EXPLAIN ANALYZE run — identified slow node
- [ ] Indexes exist on all WHERE and JOIN columns
- [ ] No SELECT * in production queries
- [ ] No correlated subqueries — replaced with JOINs or CTEs
- [ ] Pagination uses keyset not offset (for pages > 10)
- [ ] Aggregations filter before grouping
- [ ] Statistics are fresh (ANALYZE run recently)
- [ ] Dead tuple ratio < 20% (VACUUM if needed)