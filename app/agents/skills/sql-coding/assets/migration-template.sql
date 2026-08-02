-- Migration: <short_description>
-- Created: <YYYY-MM-DD>
-- Author: <name>
--
-- Description:
--   <What this migration does and why>
--
-- Rollback: see DOWN section at bottom

-- ============================================================
-- UP
-- ============================================================

begin;

-- Example: create a new table
create table if not exists example_table (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references users(id) on delete cascade,
  name        text not null,
  is_active   boolean not null default true,
  metadata    jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Indexes (add for every column used in WHERE or JOIN)
create index if not exists idx_example_table_user_id
  on example_table(user_id);

create index if not exists idx_example_table_is_active
  on example_table(is_active)
  where is_active = true;  -- partial index — only indexes active rows

commit;


-- ============================================================
-- DOWN (rollback)
-- ============================================================

-- begin;
-- drop table if exists example_table;
-- commit;