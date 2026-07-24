-- ============================================================================
-- TapParfum Portaal — AM-locaties (ritten & werkdag-stempels, permanent archief)
-- ----------------------------------------------------------------------------
-- Losse locatie-STEMPELS van een accountmanager: start werkdag, stop werkdag en
-- een check-in bij een winkelbezoek. Bewust GEEN doorlopende GPS-tracking — de
-- app legt alleen een punt vast op een expliciete handeling van de AM (v71:
-- "bewijs op het moment dat het telt"). De AM heeft daarnaast een eigen aan/uit-
-- knop (client-side) om het loggen te pauzeren.
--
-- Toegang (de echte grens is RLS, niet de UI):
--   accountmanager -> leest + plaatst ALLEEN zijn eigen stempels
--   kantoor (staff)-> leest ALLES (overzicht) en mag als enige verwijderen
--   partner        -> geen toegang
--
-- Bewaren: permanent archief. Geen automatische opschoning; de AM kan niets
-- wissen (zo blijft de bewijswaarde intact). Alleen kantoor kan verwijderen —
-- zodat een AVG-verwijderverzoek (AM uit dienst, foutieve stempel) wél kan.
--
-- Anti-spoofing: een BEFORE INSERT-guard zet am_id server-side op de ingelogde
-- AM; niemand kan dus een stempel op naam van een collega schrijven, ook niet
-- via de rauwe API. Draai NA 001..013. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

create table if not exists public.am_locaties (
  id                uuid primary key default gen_random_uuid(),
  am_id             uuid not null references public.accountmanagers(id) on delete cascade,
  type              text not null check (type in ('start', 'stop', 'bezoek')),
  tappunt_snelstart text,                       -- bij een bezoek: welke winkel
  lat               double precision,
  lng               double precision,
  acc               integer,                     -- nauwkeurigheid in meters
  loc               text,                        -- straat/plaats (reverse-geocode)
  at                timestamptz not null default now(),
  created_at        timestamptz not null default now()
);
create index if not exists am_locaties_am_idx on public.am_locaties(am_id, at desc);

alter table public.am_locaties enable row level security;

-- Lezen: kantoor alles; AM alleen zijn eigen spoor. (Partner matcht niets.)
drop policy if exists am_locaties_select on public.am_locaties;
create policy am_locaties_select on public.am_locaties
  for select to authenticated
  using (public.tp_is_staff() or am_id = public.tp_am_id());

-- Plaatsen: alleen een accountmanager, en alleen in het eigen spoor. De guard
-- hieronder dwingt am_id sowieso af aan de bron.
drop policy if exists am_locaties_insert on public.am_locaties;
create policy am_locaties_insert on public.am_locaties
  for insert to authenticated
  with check (am_id = public.tp_am_id());

-- Wijzigen: stempels zijn onveranderlijk — geen enkele update-policy.

-- Verwijderen: uitsluitend kantoor (permanent archief; AVG-verzoek blijft mogelijk).
drop policy if exists am_locaties_delete on public.am_locaties;
create policy am_locaties_delete on public.am_locaties
  for delete to authenticated
  using (public.tp_is_staff());

-- Anti-spoofing-guard: dwingt am_id af op de ingelogde accountmanager.
create or replace function public.tp_guard_am_locatie()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_am uuid;
begin
  v_am := public.tp_am_id();
  if v_am is null then
    raise exception 'Alleen een accountmanager kan een locatiestempel plaatsen';
  end if;
  new.am_id := v_am;                     -- nooit de door de client meegegeven waarde
  return new;
end; $$;

drop trigger if exists tp_guard_am_locatie on public.am_locaties;
create trigger tp_guard_am_locatie
  before insert on public.am_locaties
  for each row execute function public.tp_guard_am_locatie();

-- ============================================================================
-- KLAAR. Permanent locatie-archief per AM — kantoor ziet alles, AM eigen spoor,
-- partner niets; alleen kantoor kan wissen.
-- ============================================================================
