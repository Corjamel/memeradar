-- ============================================================================
-- TapParfum Portaal — CRM-uitbreiding: contacten, deals, taken (Fase 4)
-- ----------------------------------------------------------------------------
--  * contacten : contactpersonen bij een winkel (winkel + AM + kantoor)
--  * deals     : verkoopkansen met pijplijnfase — ALLEEN AM/kantoor (interne
--                sales-informatie; een partner ziet deals bewust niet)
--  * taken     : takenlijst per accountmanager, kantoor kan toewijzen
-- Draai NA 001..007. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

-- ============================= CONTACTEN ====================================
create table if not exists public.contacten (
  id                uuid primary key default gen_random_uuid(),
  tappunt_snelstart text not null references public.tappunten(snelstart) on delete cascade,
  naam              text not null,
  functie           text,
  tel               text,
  email             text,
  notitie           text,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create index if not exists contacten_tappunt_idx on public.contacten(tappunt_snelstart);
alter table public.contacten enable row level security;

drop trigger if exists tp_touch_contacten on public.contacten;
create trigger tp_touch_contacten before update on public.contacten
  for each row execute function public.tp_touch();

-- Winkel, AM van de winkel en kantoor zien/beheren de contacten.
drop policy if exists contacten_select on public.contacten;
create policy contacten_select on public.contacten
  for select to authenticated
  using (public.tp_is_staff()
         or public.tp_is_eigen_winkel(tappunt_snelstart)
         or public.tp_is_winkel_van_am(tappunt_snelstart));

drop policy if exists contacten_insert on public.contacten;
create policy contacten_insert on public.contacten
  for insert to authenticated
  with check (public.tp_is_staff()
         or public.tp_is_eigen_winkel(tappunt_snelstart)
         or public.tp_is_winkel_van_am(tappunt_snelstart));

drop policy if exists contacten_update on public.contacten;
create policy contacten_update on public.contacten
  for update to authenticated
  using (public.tp_is_staff()
         or public.tp_is_eigen_winkel(tappunt_snelstart)
         or public.tp_is_winkel_van_am(tappunt_snelstart))
  with check (public.tp_is_staff()
         or public.tp_is_eigen_winkel(tappunt_snelstart)
         or public.tp_is_winkel_van_am(tappunt_snelstart));

-- Verwijderen: kantoor of de AM (niet de partner — voorkomt per-ongeluk-wissen).
drop policy if exists contacten_delete on public.contacten;
create policy contacten_delete on public.contacten
  for delete to authenticated
  using (public.tp_is_staff() or public.tp_is_winkel_van_am(tappunt_snelstart));

-- Guard: een contact kan nooit naar een andere winkel worden verplaatst.
create or replace function public.tp_guard_vast_tappunt()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if public.tp_is_staff() then return new; end if;
  new.tappunt_snelstart := old.tappunt_snelstart;
  new.created_at        := old.created_at;
  return new;
end; $$;

drop trigger if exists tp_guard_contacten on public.contacten;
create trigger tp_guard_contacten before update on public.contacten
  for each row execute function public.tp_guard_vast_tappunt();

-- =============================== DEALS ======================================
create table if not exists public.deals (
  id                uuid primary key default gen_random_uuid(),
  tappunt_snelstart text not null references public.tappunten(snelstart) on delete cascade,
  titel             text not null,
  waarde            numeric not null default 0,
  fase              text not null default 'lead'
                    check (fase in ('lead','voorstel','onderhandeling','gewonnen','verloren')),
  verwacht          date,
  notitie           text,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create index if not exists deals_tappunt_idx on public.deals(tappunt_snelstart);
alter table public.deals enable row level security;

drop trigger if exists tp_touch_deals on public.deals;
create trigger tp_touch_deals before update on public.deals
  for each row execute function public.tp_touch();

-- ALLEEN kantoor en de AM van de winkel — partners zien deals niet.
drop policy if exists deals_rw on public.deals;
create policy deals_rw on public.deals
  for all to authenticated
  using (public.tp_is_staff() or public.tp_is_winkel_van_am(tappunt_snelstart))
  with check (public.tp_is_staff() or public.tp_is_winkel_van_am(tappunt_snelstart));

drop trigger if exists tp_guard_deals on public.deals;
create trigger tp_guard_deals before update on public.deals
  for each row execute function public.tp_guard_vast_tappunt();

-- =============================== TAKEN ======================================
create table if not exists public.taken (
  id                uuid primary key default gen_random_uuid(),
  titel             text not null,
  tappunt_snelstart text references public.tappunten(snelstart) on delete set null,
  am_id             uuid references public.accountmanagers(id) on delete cascade,
  deadline          date,
  klaar             boolean not null default false,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create index if not exists taken_am_idx on public.taken(am_id);
alter table public.taken enable row level security;

drop trigger if exists tp_touch_taken on public.taken;
create trigger tp_touch_taken before update on public.taken
  for each row execute function public.tp_touch();

-- Kantoor alles; een AM alleen zijn eigen taken.
drop policy if exists taken_rw on public.taken;
create policy taken_rw on public.taken
  for all to authenticated
  using (public.tp_is_staff() or am_id = public.tp_am_id())
  with check (public.tp_is_staff() or am_id = public.tp_am_id());

-- Guard: een AM kan een taak niet aan iemand anders (of niemand) hangen.
create or replace function public.tp_guard_taak()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if public.tp_is_staff() then return new; end if;
  new.am_id      := old.am_id;
  new.created_at := old.created_at;
  return new;
end; $$;

drop trigger if exists tp_guard_taken on public.taken;
create trigger tp_guard_taken before update on public.taken
  for each row execute function public.tp_guard_taak();

-- ============================================================================
-- KLAAR. Contacten bij de winkel, deals in de pijplijn (AM/kantoor), taken per
-- AM met kantoor-toewijzing. Alles server-afgedwongen.
-- ============================================================================
