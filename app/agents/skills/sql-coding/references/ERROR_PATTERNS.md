# SQL Error Patterns

Quick reference for classifying and fixing common SQL errors.
Used by the agent after running validate_query.py.

---

## syntax error at or near "X"
**Database:** PostgreSQL
**Root cause:** Invalid SQL syntax — missing keyword, extra comma, unclosed parenthesis, or wrong clause order.
**Fix pattern:**
- Extra comma before FROM or WHERE: remove trailing comma in SELECT list
- Unclosed parenthesis: count opening vs closing parens
- Wrong clause order: SELECT → FROM → JOIN → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT

```sql
-- Wrong: trailing comma
select id, name, from users

-- Correct
select id, name from users
```

---

## column "X" does not exist
**Database:** PostgreSQL
**Root cause:** Column name typo, wrong table alias, or column doesn't exist in the queried table.
**First check:**
1. Verify the exact column name with `\d table_name` or `information_schema.columns`
2. Check if the column belongs to a joined table and needs an alias prefix
3. Check for case sensitivity — PostgreSQL lowercases unquoted identifiers

```sql
-- Wrong: missing alias prefix in multi-table query
select name from users u join orders o on o.user_id = u.id

-- Correct: ambiguous 'name' needs prefix
select u.name from users u join orders o on o.user_id = u.id
```

---

## relation "X" does not exist
**Database:** PostgreSQL
**Root cause:** Table name typo, wrong schema, or table doesn't exist in the current database.
**Fix pattern:**
- Check schema: `select table_name from information_schema.tables where table_name = 'X'`
- If in a non-public schema: use `schema_name.table_name` or set `search_path`

---

## operator does not exist: X = Y
**Database:** PostgreSQL
**Root cause:** Type mismatch — comparing a string to an integer, UUID to text, etc.
**Fix pattern:** Cast explicitly:

```sql
-- Wrong: comparing uuid column to string literal
where id = '123'

-- Correct
where id = '123'::uuid
-- or
where id::text = '123'
```

---

## NULL comparison errors
**Pattern:** Query returns unexpected results when filtering NULLs
**Root cause:** Using `= NULL` instead of `IS NULL`
**Fix:**

```sql
-- Wrong — always returns empty result
where deleted_at = NULL

-- Correct
where deleted_at is null
```

---

## duplicate key value violates unique constraint
**Root cause:** INSERT trying to add a row with a value that already exists in a UNIQUE or PRIMARY KEY column.
**Fix pattern:** Use upsert (INSERT ... ON CONFLICT) or check existence first:

```sql
insert into users (email, name)
values (:email, :name)
on conflict (email)
do update set name = excluded.name;
```

---

## foreign key constraint violation
**Root cause:** Inserting a row that references a non-existent row in the parent table, or deleting a parent row that has child rows.
**Fix pattern:**
- On insert: ensure the referenced row exists first
- On delete: use CASCADE or set NULL, or delete children first

```sql
-- Add cascade to the constraint
alter table orders
add constraint fk_user
foreign key (user_id) references users(id)
on delete cascade;
```

---

## division by zero
**Root cause:** Dividing by a column or expression that can be zero.
**Fix:** Use NULLIF to convert zero to NULL:

```sql
-- Wrong
select total_revenue / total_orders as avg_order_value

-- Correct
select total_revenue / nullif(total_orders, 0) as avg_order_value
```

---

## could not determine data type of parameter $N
**Database:** PostgreSQL
**Root cause:** Parameterized query where PostgreSQL can't infer the type from context.
**Fix:** Add explicit cast to the parameter:

```sql
-- Wrong
where created_at > $1

-- Correct
where created_at > $1::timestamptz
```

---

## ERROR: each UNION query must have the same number of columns
**Root cause:** UNION queries have different column counts.
**Fix:** Add NULL placeholders to make column counts match:

```sql
select id, name, email from users
union all
select id, name, null::text from admins  -- pad missing column with NULL
```

---

## deadlock detected
**Root cause:** Two transactions locking the same rows in different orders.
**Fix pattern:**
- Always lock rows in the same order across transactions
- Use `SELECT ... FOR UPDATE SKIP LOCKED` for queue-style processing
- Keep transactions short — don't do external calls inside a transaction

---

## statement timeout / query cancelled
**Root cause:** Query exceeded the configured timeout.
**Fix pattern:**
- Add indexes on columns in WHERE and JOIN clauses
- Replace correlated subqueries with CTEs or joins
- Use EXPLAIN ANALYZE to find the slow node
- Consider pagination for large result sets