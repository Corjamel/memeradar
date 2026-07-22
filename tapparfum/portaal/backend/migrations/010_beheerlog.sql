-- ============================================================================
-- TapParfum Portaal — Audit-log voor beheeracties (PARITY #12)
-- ----------------------------------------------------------------------------
-- Elke beheeractie (AM uitgenodigd/verwijderd, winkel toegewezen/geblokkeerd,
-- instellingen gewijzigd, AVG-anonimisering) wordt vastgelegd: wie, wat, wanneer.
-- RLS: uitsluitend kantoor (staff) kan lezen én schrijven — net als in v71,
-- waar de beheerLog nooit het beheerpaneel verliet.
-- Draai NA 001..009. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

create table if not exists public.beheerlog (
  id  uuid primary key default gen_random_uuid(),
  at  timestamptz not null default now(),
  wie text,
  txt text not null
);
create index if not exists beheerlog_at_idx on public.beheerlog(at desc);

alter table public.beheerlog enable row level security;

drop policy if exists beheerlog_staff on public.beheerlog;
create policy beheerlog_staff on public.beheerlog
  for all to authenticated
  using (public.tp_is_staff())
  with check (public.tp_is_staff());

-- ============================================================================
-- KLAAR. Zichtbaar in het portaal onder Beheer -> Audit.
-- ============================================================================
