-- ============================================================================
-- TapParfum Portaal — Berichten (kantoor ↔ accountmanager)
-- ----------------------------------------------------------------------------
-- Vervangt de lokale 'berichten'-namespace uit de oude app. Die kon bewust NIET
-- via de wereld-leesbare central-tabel syncen; deze eigen tabel heeft daarom
-- strikte RLS: kantoor (staff) ziet/beheert alles, een AM ziet uitsluitend zijn
-- eigen berichten en mag alleen antwoorden (status/antwoord), niets herschrijven.
-- Draai NA 001..004. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

create table if not exists public.berichten (
  id          uuid primary key default gen_random_uuid(),
  aan_am      uuid not null references public.accountmanagers(id) on delete cascade,
  van         text not null default 'kantoor',
  type        text not null default 'vraag' check (type in ('vraag','taak')),
  txt         text not null,
  status      text not null default 'open' check (status in ('open','klaar')),
  antwoord    text,
  antwoord_at timestamptz,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists berichten_am_idx on public.berichten(aan_am);

alter table public.berichten enable row level security;

drop trigger if exists tp_touch_berichten on public.berichten;
create trigger tp_touch_berichten before update on public.berichten
  for each row execute function public.tp_touch();

-- Kantoor: volledig beheer.
drop policy if exists berichten_staff_all on public.berichten;
create policy berichten_staff_all on public.berichten
  for all to authenticated
  using (public.tp_is_staff())
  with check (public.tp_is_staff());

-- AM: alleen eigen berichten lezen…
drop policy if exists berichten_am_select on public.berichten;
create policy berichten_am_select on public.berichten
  for select to authenticated
  using (aan_am = public.tp_am_id());

-- …en beantwoorden (update op eigen berichten).
drop policy if exists berichten_am_update on public.berichten;
create policy berichten_am_update on public.berichten
  for update to authenticated
  using (aan_am = public.tp_am_id())
  with check (aan_am = public.tp_am_id());

-- Kolom-guard: een AM mag ALLEEN status/antwoord/antwoord_at wijzigen; de
-- oorspronkelijke vraag (txt/van/type/aan_am) blijft onaantastbaar.
create or replace function public.tp_guard_bericht()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if public.tp_is_staff() then return new; end if;
  new.aan_am     := old.aan_am;
  new.van        := old.van;
  new.type       := old.type;
  new.txt        := old.txt;
  new.created_at := old.created_at;
  return new;
end; $$;

drop trigger if exists tp_guard_berichten on public.berichten;
create trigger tp_guard_berichten
  before update on public.berichten
  for each row execute function public.tp_guard_bericht();

-- ============================================================================
-- KLAAR. Kantoor stuurt een vraag/taak aan een AM; de AM ziet hem in het
-- portaal en beantwoordt; kantoor ziet het antwoord. Alles server-afgedwongen.
-- ============================================================================
