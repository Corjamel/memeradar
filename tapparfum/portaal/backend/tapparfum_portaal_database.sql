-- ============================================================================
-- TapParfum Portaal — COMPLETE DATABASE-INSTALLATIE (alles-in-één, v7)
-- Plak dit VOLLEDIG in Supabase -> SQL Editor -> Run. Veilig om opnieuw te
-- draaien (idempotent). Bevat migraties 001 t/m 014 (nieuw: AM-locaties —
-- ritten & werkdag-stempels, permanent archief; kantoor alles, AM eigen).
-- ============================================================================

-- ################### 001_core.sql ###################

-- ============================================================================
-- TapParfum Portal — Supabase schema (Fase 1)
-- Plak dit volledig in Supabase → SQL Editor → Run.
-- Ontwerp:
--   * snelstartcode = leidende, unieke sleutel per winkel (tappunt)
--   * Supabase Auth regelt wachtwoorden + automatische reset-mail (partners)
--   * geneste velden (verkopen, signalen, setup, forms, logboek, ...) als jsonb
--   * Row Level Security: een partner ziet/bewerkt alleen zijn eigen winkel;
--     kantoor/AM-medewerkers (rol 'staff') zien het hele netwerk
-- Idempotent: veilig om opnieuw te draaien.
-- Gevalideerd tegen PostgreSQL 16 (schema + RLS + RPC + triggers, exit 0).
-- ============================================================================

-- ---- Uitbreidingen -------------------------------------------------------
create extension if not exists "pgcrypto";

-- ---- Rol-helper ----------------------------------------------------------
-- De rol staat in de JWT (app_metadata.role): 'staff' voor kantoor/AM,
-- standaard 'partner' voor winkels. Zet 'staff' via Supabase → Authentication.
create or replace function public.tp_role()
returns text language sql stable as $$
  select coalesce(
    nullif(current_setting('request.jwt.claims', true), '')::jsonb
      -> 'app_metadata' ->> 'role',
    'partner'
  );
$$;

create or replace function public.tp_is_staff()
returns boolean language sql stable as $$
  select public.tp_role() = 'staff';
$$;

-- ---- Accountmanagers -----------------------------------------------------
create table if not exists public.accountmanagers (
  id          uuid primary key default gen_random_uuid(),
  naam        text not null unique,
  auth_user_id uuid references auth.users on delete set null,
  created_at  timestamptz not null default now()
);

-- ---- Tappunten (winkels) — snelstart is LEIDEND --------------------------
create table if not exists public.tappunten (
  id           uuid primary key default gen_random_uuid(),
  snelstart    text not null unique,                       -- LEIDENDE SLEUTEL
  am_id        uuid references public.accountmanagers(id) on delete set null,
  auth_user_id uuid references auth.users on delete set null, -- gekoppeld na 1e login
  name         text not null,
  email        text,
  geblokkeerd  boolean not null default false,
  data         jsonb  not null default '{}'::jsonb,        -- alle overige velden
  updated_at   timestamptz not null default now(),
  created_at   timestamptz not null default now()
);
create index if not exists tappunten_am_idx    on public.tappunten(am_id);
create index if not exists tappunten_user_idx  on public.tappunten(auth_user_id);
create unique index if not exists tappunten_snelstart_lower_idx
  on public.tappunten(lower(snelstart));

-- ---- Centrale (netwerkbrede) config --------------------------------------
-- ns = namespace: 'acties','producten','berichten','brand','regels',
--      'flesMaten','margeFactor','shopUrl','b2bApi','teksten', ...
create table if not exists public.central (
  ns         text primary key,
  data       jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

-- ---- updated_at automatisch bijwerken ------------------------------------
create or replace function public.tp_touch()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end; $$;

drop trigger if exists tp_touch_tappunten on public.tappunten;
create trigger tp_touch_tappunten before update on public.tappunten
  for each row execute function public.tp_touch();

drop trigger if exists tp_touch_central on public.central;
create trigger tp_touch_central before update on public.central
  for each row execute function public.tp_touch();

-- ============================================================================
-- Row Level Security
-- ============================================================================
alter table public.accountmanagers enable row level security;
alter table public.tappunten       enable row level security;
alter table public.central         enable row level security;

-- --- Tappunten ---
-- Partner: alleen de eigen winkel (gekoppeld aan zijn auth-account).
drop policy if exists tappunt_partner_select on public.tappunten;
create policy tappunt_partner_select on public.tappunten
  for select to authenticated
  using (auth_user_id = auth.uid() or public.tp_is_staff());

drop policy if exists tappunt_partner_update on public.tappunten;
create policy tappunt_partner_update on public.tappunten
  for update to authenticated
  using (auth_user_id = auth.uid() or public.tp_is_staff())
  with check (auth_user_id = auth.uid() or public.tp_is_staff());

-- Staff (kantoor/AM) mag toevoegen en verwijderen; partners niet.
drop policy if exists tappunt_staff_insert on public.tappunten;
create policy tappunt_staff_insert on public.tappunten
  for insert to authenticated
  with check (public.tp_is_staff());

drop policy if exists tappunt_staff_delete on public.tappunten;
create policy tappunt_staff_delete on public.tappunten
  for delete to authenticated
  using (public.tp_is_staff());

-- Koppeling bij eerste login: een partner mag zijn nog-ongekoppelde winkel
-- aan zijn eigen account koppelen mits hij de juiste snelstartcode kent.
-- (De app doet dit via de beveiligde RPC hieronder, niet via directe update.)

-- --- Accountmanagers ---
drop policy if exists am_staff_all on public.accountmanagers;
create policy am_staff_all on public.accountmanagers
  for all to authenticated
  using (public.tp_is_staff())
  with check (public.tp_is_staff());

drop policy if exists am_self_select on public.accountmanagers;
create policy am_self_select on public.accountmanagers
  for select to authenticated
  using (auth_user_id = auth.uid() or public.tp_is_staff());

-- --- Central ---
-- Iedereen die is ingelogd mag centrale config LEZEN (acties/producten/merk);
-- alleen staff mag schrijven.
drop policy if exists central_read on public.central;
create policy central_read on public.central
  for select to authenticated using (true);

drop policy if exists central_staff_write on public.central;
create policy central_staff_write on public.central
  for all to authenticated
  using (public.tp_is_staff())
  with check (public.tp_is_staff());

-- ============================================================================
-- RPC: eerste login koppelt account aan winkel via de snelstartcode
-- De partner registreert zich (Supabase Auth: e-mail + wachtwoord), en roept
-- daarna deze functie aan met zijn snelstartcode. De functie koppelt zijn
-- auth-account aan het bijbehorende, nog-ongekoppelde tappunt.
-- ============================================================================
create or replace function public.claim_tappunt(p_snelstart text, p_user text)
returns public.tappunten
language plpgsql security definer set search_path = public as $$
declare row public.tappunten;
begin
  select * into row from public.tappunten
   where lower(snelstart) = lower(trim(p_snelstart)) limit 1;
  if not found then raise exception 'Geen winkel met deze snelstartcode.'; end if;
  if row.geblokkeerd then raise exception 'Deze toegang is geblokkeerd.'; end if;
  if row.auth_user_id is not null and row.auth_user_id <> auth.uid() then
    raise exception 'Voor deze winkel bestaat al een account.';
  end if;
  update public.tappunten
     set auth_user_id = auth.uid(),
         data = jsonb_set(coalesce(data,'{}'::jsonb), '{gebruikersnaam}', to_jsonb(coalesce(p_user, name)))
   where id = row.id
   returning * into row;
  return row;
end; $$;

revoke all on function public.claim_tappunt(text,text) from public;
grant execute on function public.claim_tappunt(text,text) to authenticated;

-- ============================================================================
-- KLAAR. Volgende stap: zet in Authentication → Providers → Email:
--   * "Confirm email" aan (zodat reset/verify-mails werken)
-- En maak je eerste kantoor-account 'staff' (zie setup.md).
-- ============================================================================

-- ################### 002_am_isolatie.sql ###################

-- ============================================================================
-- TapParfum Portal — Accountmanager-isolatie (Fase 2b)
-- Elke accountmanager ziet/bewerkt ALLEEN zijn eigen tappunten; kantoor (rol
-- 'staff') blijft het hele netwerk zien. Partners zien alleen hun eigen winkel.
-- Draai dit NÁ schema.sql. Idempotent: veilig om opnieuw te draaien.
-- Gevalideerd tegen PostgreSQL 16.
-- ============================================================================

-- Welke accountmanager is de ingelogde gebruiker? (NULL als hij geen AM is)
create or replace function public.tp_am_id()
returns uuid language sql stable security definer set search_path = public as $$
  select id from public.accountmanagers where auth_user_id = auth.uid() limit 1;
$$;

create or replace function public.tp_is_am()
returns boolean language sql stable as $$
  select public.tp_am_id() is not null;
$$;

-- ---- Tappunten: AM mag uitsluitend zijn eigen winkels ----------------------
-- (Bestaande partner- en staff-policies blijven staan; permissive policies
--  worden met OR gecombineerd, dus dit voegt AM-toegang toe zonder de rest te
--  breken.)
drop policy if exists tappunt_am_select on public.tappunten;
create policy tappunt_am_select on public.tappunten
  for select to authenticated
  using (am_id = public.tp_am_id());

drop policy if exists tappunt_am_update on public.tappunten;
create policy tappunt_am_update on public.tappunten
  for update to authenticated
  using (am_id = public.tp_am_id())
  with check (am_id = public.tp_am_id());

drop policy if exists tappunt_am_insert on public.tappunten;
create policy tappunt_am_insert on public.tappunten
  for insert to authenticated
  with check (am_id = public.tp_am_id());

drop policy if exists tappunt_am_delete on public.tappunten;
create policy tappunt_am_delete on public.tappunten
  for delete to authenticated
  using (am_id = public.tp_am_id());

-- ---- Accountmanagers mogen elkaar niet zien --------------------------------
-- (am_self_select in schema.sql regelt al: eigen rij of staff. Niets extra nodig.)

-- ============================================================================
-- Een AM-account aanmaken + koppelen (doe je als beheerder, éénmalig per AM)
-- ----------------------------------------------------------------------------
-- STAP 1 (in de UI): Authentication > Users > Add user -> e-mail + wachtwoord,
--         zet "Auto Confirm User" aan.
-- STAP 2 (hieronder, vervang naam + e-mail) -> koppelt de login aan een AM:
--
--   insert into public.accountmanagers (naam, auth_user_id)
--   select 'Marian', id from auth.users where lower(email) = 'marian@voorbeeld.nl'
--   on conflict (naam) do update set auth_user_id = excluded.auth_user_id;
--
-- STAP 3 (optioneel) -> bestaande winkels aan die AM hangen (op snelstartcode):
--
--   update public.tappunten set am_id = (select id from public.accountmanagers
--     where lower(naam) = 'marian')
--   where lower(snelstart) in ('kl-10','kl-20');
--
-- Kantoor/AM zetten (rol 'staff' is ALLEEN voor kantoor, niet voor AM's):
--   -- staff = kantoor; AM's krijgen GEEN staff-rol, hun toegang loopt via
--   -- de accountmanagers-koppeling hierboven.
-- ============================================================================

-- ################### 003_storage.sql ###################

-- ============================================================================
-- TapParfum Portal — Documenten via Supabase Storage (Fase 2c)
-- Privé bucket 'tp-docs' + toegangsregels: een partner ziet/upload alleen in de
-- map van zijn eigen winkel, een AM in die van zijn winkels, kantoor (staff) overal.
-- Bestandspad = "<snelstartcode>/<tijd>_<naam>". Draai dit NÁ schema.sql + schema_am.sql.
-- Idempotent. (Storage-RLS is Supabase-specifiek; draai in de SQL Editor.)
-- ============================================================================

-- 1) Privé bucket
insert into storage.buckets (id, name, public)
values ('tp-docs', 'tp-docs', false)
on conflict (id) do nothing;

-- Helper: hoort de ingelogde gebruiker bij de winkel van dit bestandspad?
-- (eerste mapnaam = snelstartcode)
create or replace function public.tp_mag_bij_pad(objectname text)
returns boolean language sql stable security definer set search_path = public as $$
  select public.tp_is_staff() or exists (
    select 1 from public.tappunten tp
     where lower(tp.snelstart) = lower(split_part(objectname, '/', 1))
       and (tp.auth_user_id = auth.uid() or tp.am_id = public.tp_am_id())
  );
$$;

-- 2) Toegangsregels op de objecten in deze bucket
drop policy if exists tpdocs_select on storage.objects;
create policy tpdocs_select on storage.objects
  for select to authenticated
  using (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name));

drop policy if exists tpdocs_insert on storage.objects;
create policy tpdocs_insert on storage.objects
  for insert to authenticated
  with check (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name));

drop policy if exists tpdocs_update on storage.objects;
create policy tpdocs_update on storage.objects
  for update to authenticated
  using (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name))
  with check (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name));

drop policy if exists tpdocs_delete on storage.objects;
create policy tpdocs_delete on storage.objects
  for delete to authenticated
  using (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name));

-- ============================================================================
-- KLAAR. In het portaal: partner/AM/kantoor -> tappunt-dashboard -> 📎 Documenten.
-- Zonder cloud-sessie werkt het lokaal (kleine bestanden); ingelogd via de cloud
-- gaan bestanden naar deze bucket en worden ze met tijdelijke (signed) links
-- geopend — nooit publiek toegankelijk.
-- ============================================================================

-- ################### 004_kolom_guard.sql ###################

-- ============================================================================
-- TapParfum Portal — Kolom-bescherming beschermde velden (Fase 1 hardening)
-- ----------------------------------------------------------------------------
-- PROBLEEM dat dit dicht: Row Level Security bepaalt WELKE rij iemand mag
-- bijwerken, maar niet WELKE kolommen. Een partner mag zijn eigen winkelrij
-- updaten (tappunt_partner_update) — en kon daardoor in díe rij ook
-- `geblokkeerd` terugzetten naar false (zichzelf DEBLOKKEREN), of `am_id` /
-- `snelstart` wijzigen. Dat hoort alleen kantoor (rol 'staff') te mogen.
--
-- OPLOSSING: een BEFORE UPDATE-trigger die voor NIET-staff de beschermde velden
-- terugzet op hun oude waarde. Legitieme opslag (waarbij die velden tóch al
-- gelijk zijn) verandert niets; alleen echte manipulatie wordt stil genegeerd.
-- `auth_user_id` mag eenmalig van NULL -> account (eerste koppeling via
-- claim_tappunt), maar daarna nooit meer wijzigen.
--
-- Draai dit NÁ schema.sql (+ schema_am.sql). Idempotent. Gevalideerd op PG16.
-- ============================================================================

create or replace function public.tp_guard_protected()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  -- Kantoor (staff) mag alles.
  if public.tp_is_staff() then
    return new;
  end if;

  -- Niet-staff (partner of accountmanager): beschermde velden blijven ongewijzigd.
  new.geblokkeerd := old.geblokkeerd;   -- niemand deblokkeert zichzelf
  new.snelstart   := old.snelstart;     -- code wijzigen is kantoorwerk
  new.am_id       := old.am_id;         -- toewijzing aan een AM is kantoorwerk

  -- auth_user_id: alleen de eerste koppeling (NULL -> account) toestaan; een
  -- reeds gekoppeld account kan niet worden overgenomen of losgekoppeld.
  if old.auth_user_id is not null then
    new.auth_user_id := old.auth_user_id;
  end if;

  return new;
end; $$;

drop trigger if exists tp_guard_tappunten on public.tappunten;
create trigger tp_guard_tappunten
  before update on public.tappunten
  for each row execute function public.tp_guard_protected();

-- ============================================================================
-- KLAAR. Na deze trigger kan een partner/AM zijn eigen winkeldata gewoon
-- opslaan, maar `geblokkeerd`, `snelstart` en `am_id` zijn voortaan alleen door
-- kantoor te wijzigen — ook als iemand de aanvraag met DevTools manipuleert.
-- ============================================================================

-- ################### 005_berichten.sql ###################

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

-- ################### 006_agenda.sql ###################

-- ============================================================================
-- TapParfum Portaal — Agenda (bezoeken plannen, accepteren/afwijzen)
-- ----------------------------------------------------------------------------
-- Een AM (of kantoor) stelt een bezoek voor aan een winkel; de partner
-- accepteert of wijst af; de AM rondt af. RLS: kantoor alles, AM alleen zijn
-- eigen bezoeken, partner alleen de bezoeken van zijn eigen winkel. Een
-- kolom-guard zorgt dat een partner uitsluitend de status (accepteren/afwijzen)
-- en een notitie kan zetten — nooit datum, winkel of AM.
-- Draai NA 001..005. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

create table if not exists public.agenda (
  id                uuid primary key default gen_random_uuid(),
  tappunt_snelstart text not null references public.tappunten(snelstart) on delete cascade,
  am_id             uuid references public.accountmanagers(id) on delete set null,
  datum             date not null,
  tijd              text,
  type              text not null default 'bezoek' check (type in ('bezoek','telefoon')),
  status            text not null default 'voorgesteld'
                    check (status in ('voorgesteld','geaccepteerd','afgewezen','afgerond')),
  notitie           text,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create index if not exists agenda_tappunt_idx on public.agenda(tappunt_snelstart);
create index if not exists agenda_am_idx      on public.agenda(am_id);

alter table public.agenda enable row level security;

drop trigger if exists tp_touch_agenda on public.agenda;
create trigger tp_touch_agenda before update on public.agenda
  for each row execute function public.tp_touch();

-- Hoort dit agenda-item bij de winkel van de ingelogde partner?
create or replace function public.tp_is_eigen_winkel(p_snelstart text)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.tappunten tp
                  where tp.snelstart = p_snelstart and tp.auth_user_id = auth.uid());
$$;

-- Lezen: kantoor alles; AM eigen bezoeken; partner bezoeken van eigen winkel.
drop policy if exists agenda_select on public.agenda;
create policy agenda_select on public.agenda
  for select to authenticated
  using (public.tp_is_staff()
         or am_id = public.tp_am_id()
         or public.tp_is_eigen_winkel(tappunt_snelstart));

-- Plannen: kantoor of de AM zelf.
drop policy if exists agenda_insert on public.agenda;
create policy agenda_insert on public.agenda
  for insert to authenticated
  with check (public.tp_is_staff() or am_id = public.tp_am_id());

-- Bijwerken: kantoor, de AM zelf, of de partner van de winkel (kolom-guard
-- beperkt wat de partner mag).
drop policy if exists agenda_update on public.agenda;
create policy agenda_update on public.agenda
  for update to authenticated
  using (public.tp_is_staff()
         or am_id = public.tp_am_id()
         or public.tp_is_eigen_winkel(tappunt_snelstart))
  with check (public.tp_is_staff()
         or am_id = public.tp_am_id()
         or public.tp_is_eigen_winkel(tappunt_snelstart));

-- Verwijderen: kantoor of de AM zelf.
drop policy if exists agenda_delete on public.agenda;
create policy agenda_delete on public.agenda
  for delete to authenticated
  using (public.tp_is_staff() or am_id = public.tp_am_id());

-- Kolom-guard:
--  * AM: mag alles van zijn eigen item wijzigen, behalve winkel/AM-koppeling.
--  * Partner: mag ALLEEN status (naar geaccepteerd/afgewezen) en notitie zetten.
create or replace function public.tp_guard_agenda()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if public.tp_is_staff() then return new; end if;

  -- koppeling ligt voor iedereen behalve kantoor vast
  new.tappunt_snelstart := old.tappunt_snelstart;
  new.am_id             := old.am_id;
  new.created_at        := old.created_at;

  if public.tp_am_id() is not null and old.am_id = public.tp_am_id() then
    return new;                       -- de AM zelf: rest mag
  end if;

  -- partner: alleen status + notitie, en status alleen accepteren/afwijzen
  new.datum := old.datum;
  new.tijd  := old.tijd;
  new.type  := old.type;
  if new.status is distinct from old.status
     and new.status not in ('geaccepteerd','afgewezen') then
    new.status := old.status;
  end if;
  return new;
end; $$;

drop trigger if exists tp_guard_agenda on public.agenda;
create trigger tp_guard_agenda
  before update on public.agenda
  for each row execute function public.tp_guard_agenda();

-- ============================================================================
-- KLAAR. AM plant -> partner ziet het voorstel en accepteert/wijst af -> AM
-- rondt af. Alles server-afgedwongen.
-- ============================================================================

-- ################### 007_winkelvragen.sql ###################

-- ============================================================================
-- TapParfum Portaal — Winkelvragen (partner -> accountmanager/kantoor)
-- ----------------------------------------------------------------------------
-- Een partner meldt een vraag, probleem of retour vanuit zijn winkel; de AM
-- van die winkel (of kantoor) beantwoordt. Sluit de communicatie-driehoek:
--   kantoor <-> AM  = berichten (005)
--   partner -> AM/kantoor = winkelvragen (dit bestand)
-- RLS: partner ziet/maakt alleen vragen van zijn eigen winkel; de AM ziet en
-- beantwoordt de vragen van zíjn winkels; kantoor alles. De kolom-guard zorgt
-- dat een antwoorder nooit de oorspronkelijke vraag herschrijft.
-- Draai NA 001..006. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

create table if not exists public.winkelvragen (
  id                uuid primary key default gen_random_uuid(),
  tappunt_snelstart text not null references public.tappunten(snelstart) on delete cascade,
  type              text not null default 'vraag' check (type in ('vraag','probleem','retour')),
  txt               text not null,
  status            text not null default 'open' check (status in ('open','beantwoord')),
  antwoord          text,
  antwoord_door     text,
  antwoord_at       timestamptz,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create index if not exists winkelvragen_tappunt_idx on public.winkelvragen(tappunt_snelstart);

alter table public.winkelvragen enable row level security;

drop trigger if exists tp_touch_winkelvragen on public.winkelvragen;
create trigger tp_touch_winkelvragen before update on public.winkelvragen
  for each row execute function public.tp_touch();

-- Is de ingelogde AM de accountmanager van deze winkel?
create or replace function public.tp_is_winkel_van_am(p_snelstart text)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.tappunten tp
                  where tp.snelstart = p_snelstart
                    and tp.am_id is not null
                    and tp.am_id = public.tp_am_id());
$$;

-- Lezen: kantoor alles; partner eigen winkel; AM zijn winkels.
drop policy if exists winkelvragen_select on public.winkelvragen;
create policy winkelvragen_select on public.winkelvragen
  for select to authenticated
  using (public.tp_is_staff()
         or public.tp_is_eigen_winkel(tappunt_snelstart)
         or public.tp_is_winkel_van_am(tappunt_snelstart));

-- Insturen: de partner van de winkel (of kantoor).
drop policy if exists winkelvragen_insert on public.winkelvragen;
create policy winkelvragen_insert on public.winkelvragen
  for insert to authenticated
  with check (public.tp_is_staff()
         or public.tp_is_eigen_winkel(tappunt_snelstart));

-- Beantwoorden: kantoor of de AM van de winkel — bewust NIET de partner zelf.
drop policy if exists winkelvragen_update on public.winkelvragen;
create policy winkelvragen_update on public.winkelvragen
  for update to authenticated
  using (public.tp_is_staff() or public.tp_is_winkel_van_am(tappunt_snelstart))
  with check (public.tp_is_staff() or public.tp_is_winkel_van_am(tappunt_snelstart));

-- Verwijderen: alleen kantoor.
drop policy if exists winkelvragen_delete on public.winkelvragen;
create policy winkelvragen_delete on public.winkelvragen
  for delete to authenticated
  using (public.tp_is_staff());

-- Kolom-guard: wie antwoordt (AM), kan de oorspronkelijke vraag niet aanraken.
create or replace function public.tp_guard_winkelvraag()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if public.tp_is_staff() then return new; end if;
  new.tappunt_snelstart := old.tappunt_snelstart;
  new.type              := old.type;
  new.txt               := old.txt;
  new.created_at        := old.created_at;
  return new;
end; $$;

drop trigger if exists tp_guard_winkelvragen on public.winkelvragen;
create trigger tp_guard_winkelvragen
  before update on public.winkelvragen
  for each row execute function public.tp_guard_winkelvraag();

-- ============================================================================
-- KLAAR. Partner meldt -> AM/kantoor beantwoordt -> partner ziet het antwoord.
-- ============================================================================

-- ################### 008_crm.sql ###################

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

-- ################### 009_beheer_am.sql ###################

-- ============================================================================
-- TapParfum Portaal — Beheer: accountmanagers uitnodigen per e-mail
-- ----------------------------------------------------------------------------
-- Kantoor voegt een AM toe met naam + e-mailadres (uitnodiging). De AM maakt
-- daarna zelf zijn login aan op het portaal; bij zijn eerste login koppelt
-- tp_koppel_am() zijn account automatisch aan de juiste AM-rij — uitsluitend
-- als zijn ingelogde e-mailadres exact overeenkomt met de uitnodiging.
-- Draai NA 001..008. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

alter table public.accountmanagers add column if not exists email text;
create unique index if not exists accountmanagers_email_idx
  on public.accountmanagers (lower(email)) where email is not null;

-- Koppel de ingelogde gebruiker aan zijn AM-uitnodiging (op e-mail).
-- security definer: leest auth.users en schrijft de koppeling, maar ALLEEN
-- voor het eigen account en alleen als de rij nog vrij is (of al van hem is).
create or replace function public.tp_koppel_am()
returns uuid language plpgsql security definer set search_path = public as $$
declare gekoppeld uuid; em text;
begin
  select lower(u.email) into em from auth.users u where u.id = auth.uid();
  if em is null or em = '' then return null; end if;
  update public.accountmanagers
     set auth_user_id = auth.uid()
   where lower(email) = em
     and (auth_user_id is null or auth_user_id = auth.uid())
   returning id into gekoppeld;
  return gekoppeld;
end; $$;

revoke all on function public.tp_koppel_am() from public;
grant execute on function public.tp_koppel_am() to authenticated;

-- ============================================================================
-- KLAAR. Kantoor: Beheer -> AM toevoegen (naam + e-mail). De AM: portaal ->
-- 'Eerste keer' -> accountmanager -> account aanmaken met dat e-mailadres.
-- ============================================================================

-- ################### 010_beheerlog.sql ###################

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

-- ============================================================================
-- TapParfum Portaal — Bewijsfoto bij winkelvragen (PARITY #8)
-- ----------------------------------------------------------------------------
-- Een partner kan bij een retour/probleem een foto meesturen. De foto zelf
-- staat privé in de 'tp-docs'-bucket (migratie 003) onder de map van de eigen
-- winkel — de bestaande Storage-RLS dekt hem dus al af. Hier alleen de
-- verwijzing (pad) op de melding + guard-uitbreiding: een antwoorder kan de
-- oorspronkelijke foto nooit vervangen of wissen.
-- Draai NA 001..010. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

alter table public.winkelvragen add column if not exists foto_pad text;

-- Kolom-guard uitbreiden: foto_pad hoort bij de oorspronkelijke melding.
create or replace function public.tp_guard_winkelvraag()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if public.tp_is_staff() then return new; end if;
  new.tappunt_snelstart := old.tappunt_snelstart;
  new.type              := old.type;
  new.txt               := old.txt;
  new.foto_pad          := old.foto_pad;
  new.created_at        := old.created_at;
  return new;
end; $$;

-- ============================================================================
-- KLAAR. Partner voegt bij het melden optioneel een foto toe; AM/kantoor opent
-- hem via een tijdelijke (signed) link.
-- ============================================================================

-- ============================================================================
-- TapParfum Portaal — Gevoelige central-namespaces afschermen (security fix)
-- ----------------------------------------------------------------------------
-- De central-tabel was volledig leesbaar voor elke ingelogde gebruiker
-- (`using (true)`). Daar staat naast onschuldige netwerkconfig (acties,
-- producten, flesMaten, margeFactor, shopUrl…) ook gevoelige data in:
--   * kantoorRechten — de rechten-matrix, gesleuteld op het e-mailadres van
--     elk kantoor-account (een directory van interne mailadressen + rechten);
--   * b2bApi — straks de koppel-instellingen/credentials van het B2B-portaal.
-- Een willekeurige partner kon die met één `select *` uitlezen. Deze migratie
-- sluit precies die namespaces af — al het andere blijft leesbaar zodat winkels
-- hun eigen niveau/kassa/prijzen blijven zien. Staff (kantoor) leest alles.
-- Draai NA 001..011. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

-- Publiek leesbaar: alle config BEHALVE de gevoelige namespaces.
drop policy if exists central_read on public.central;
create policy central_read on public.central
  for select to authenticated
  using (ns not in ('kantoorRechten', 'b2bApi'));

-- Staff leest álles (ook de gevoelige namespaces) — meerdere permissieve
-- SELECT-policies worden met OR gecombineerd, dus dit verruimt alleen voor staff.
drop policy if exists central_read_staff on public.central;
create policy central_read_staff on public.central
  for select to authenticated
  using (public.tp_is_staff());

-- ============================================================================
-- KLAAR. Partner/AM: alle config behalve kantoorRechten/b2bApi. Kantoor: alles.
-- Schrijven blijft staff-only (central_staff_write, migratie 001).
-- ============================================================================

-- ################### 013_community.sql ###################

-- ============================================================================
-- TapParfum Portaal — Community (besloten tijdlijn per AM-portefeuille)
-- ----------------------------------------------------------------------------
-- v71 (r.3382) legt de keuze vast: de community is BESLOTEN PER accountmanager-
-- portefeuille. Partners van verschillende accountmanagers zien elkaars posts
-- en winkelnamen NIET. Dat is precies de "geen datalek"-eis: een post leeft in
-- één portefeuille (am_id) en is alleen zichtbaar binnen die portefeuille.
--
--   partner  -> leest + plaatst in de portefeuille van zíjn winkel
--   AM       -> leest + plaatst (als accountmanager) in zíjn portefeuille
--   kantoor  -> leest alles (moderatie) + mag verwijderen
--
-- Anti-spoofing: een BEFORE INSERT-guard zet am_id/author/role server-side op
-- basis van wie je bent — een partner kan dus geen post in een andere
-- portefeuille of onder een valse naam plaatsen, ook niet via de rauwe API.
-- Draai NA 001..012. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

create table if not exists public.community (
  id         uuid primary key default gen_random_uuid(),
  am_id      uuid not null references public.accountmanagers(id) on delete cascade,
  author     text not null,
  role       text not null default 'partner' check (role in ('partner', 'am', 'hq')),
  txt        text not null,
  created_at timestamptz not null default now()
);
create index if not exists community_am_idx on public.community(am_id, created_at desc);

alter table public.community enable row level security;

-- De portefeuille (am_id) van de winkel van de ingelogde partner (NULL als de
-- gebruiker geen gekoppelde winkel heeft, bv. een AM of kantoor).
create or replace function public.tp_partner_am_id()
returns uuid language sql stable security definer set search_path = public as $$
  select am_id from public.tappunten
   where auth_user_id = auth.uid() and am_id is not null
   limit 1;
$$;

-- Lezen: kantoor alles; AM zijn portefeuille; partner de portefeuille van zijn
-- winkel. am_id is NOT NULL, dus een NULL-portefeuille matcht bewust niets.
drop policy if exists community_select on public.community;
create policy community_select on public.community
  for select to authenticated
  using (public.tp_is_staff()
         or am_id = public.tp_am_id()
         or am_id = public.tp_partner_am_id());

-- Plaatsen: kantoor overal; AM in eigen portefeuille; partner in de portefeuille
-- van zijn winkel. De guard hieronder maakt de kolommen alsnog waterdicht.
drop policy if exists community_insert on public.community;
create policy community_insert on public.community
  for insert to authenticated
  with check (public.tp_is_staff()
         or am_id = public.tp_am_id()
         or am_id = public.tp_partner_am_id());

-- Wijzigen: niemand herschrijft posts (alleen kantoor, voor correctie).
drop policy if exists community_update on public.community;
create policy community_update on public.community
  for update to authenticated
  using (public.tp_is_staff())
  with check (public.tp_is_staff());

-- Verwijderen (moderatie): alleen kantoor.
drop policy if exists community_delete on public.community;
create policy community_delete on public.community
  for delete to authenticated
  using (public.tp_is_staff());

-- Anti-spoofing-guard: dwingt portefeuille, auteur en rol af aan de bron.
create or replace function public.tp_guard_community()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_am uuid; v_naam text; v_winkel record;
begin
  -- Kantoor mag bewust vrij plaatsen (HQ-mededeling in een gekozen portefeuille).
  if public.tp_is_staff() then
    if new.role is null then new.role := 'hq'; end if;
    return new;
  end if;
  -- Accountmanager: post leeft in zijn eigen portefeuille, onder zijn naam.
  v_am := public.tp_am_id();
  if v_am is not null then
    select naam into v_naam from public.accountmanagers where id = v_am;
    new.am_id  := v_am;
    new.author := coalesce(v_naam, 'Accountmanager');
    new.role   := 'am';
    return new;
  end if;
  -- Partner: post leeft in de portefeuille van zijn winkel, onder de winkelnaam.
  select am_id, name into v_winkel
    from public.tappunten
   where auth_user_id = auth.uid() and am_id is not null
   limit 1;
  if v_winkel.am_id is null then
    raise exception 'Geen winkel/portefeuille gekoppeld aan dit account';
  end if;
  new.am_id  := v_winkel.am_id;
  new.author := v_winkel.name;
  new.role   := 'partner';
  return new;
end; $$;

drop trigger if exists tp_guard_community on public.community;
create trigger tp_guard_community
  before insert on public.community
  for each row execute function public.tp_guard_community();

-- ============================================================================
-- KLAAR. Besloten tijdlijn per portefeuille — geen kruislekken tussen AM's.
-- ============================================================================

-- ################### 014_am_locaties.sql ###################

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
