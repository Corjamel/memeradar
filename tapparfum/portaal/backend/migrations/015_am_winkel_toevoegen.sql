-- ============================================================================
-- TapParfum Portaal — accountmanager mag winkels toevoegen (eigen portefeuille)
-- ----------------------------------------------------------------------------
-- v71 liet een accountmanager zelf klanten aanmaken (addClient). In de cloud
-- stond winkel-toevoegen per ongeluk alleen voor kantoor open. Deze migratie
-- geeft een AM het recht om een winkel toe te voegen — maar ALLEEN in zijn eigen
-- portefeuille. Een BEFORE INSERT-guard forceert am_id op de ingelogde AM, dus
-- een AM kan nooit een winkel in andermans portefeuille (of geblokkeerd, of
-- gekoppeld aan een account) aanmaken. Partners blijven volledig geweerd.
--
--   kantoor  -> voegt winkels toe (bestaande staff-policy)
--   AM       -> voegt winkels toe in EIGEN portefeuille (deze migratie)
--   partner  -> mag niets toevoegen
--
-- Draai NA 001..014. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

-- Extra INSERT-policy (permissief; OR met de bestaande staff-policy):
-- een AM mag invoegen zolang am_id zijn eigen portefeuille is. De guard
-- hieronder zet am_id sowieso goed, dus dit is defensie in de diepte.
drop policy if exists tappunt_am_insert on public.tappunten;
create policy tappunt_am_insert on public.tappunten
  for insert to authenticated
  with check (am_id = public.tp_am_id());

-- BEFORE INSERT-guard: voor NIET-staff (dus een AM; een partner komt niet door
-- de policy) forceren we de beschermde velden aan de bron.
create or replace function public.tp_guard_tappunt_insert()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if public.tp_is_staff() then
    return new;                         -- kantoor mag alles zetten (incl. toewijzing)
  end if;
  -- Accountmanager: winkel belandt in ZIJN portefeuille, niet geblokkeerd,
  -- nog niet aan een partner-account gekoppeld.
  new.am_id        := public.tp_am_id();
  new.geblokkeerd  := false;
  new.auth_user_id := null;
  return new;
end $$;

drop trigger if exists tp_guard_tappunt_insert on public.tappunten;
create trigger tp_guard_tappunt_insert
  before insert on public.tappunten
  for each row execute function public.tp_guard_tappunt_insert();

-- ============================================================================
-- KLAAR. Een AM kan nu winkels toevoegen — uitsluitend in de eigen portefeuille;
-- am_id wordt server-side afgedwongen (geen kruis-toevoegingen, geen spoofing).
-- ============================================================================
