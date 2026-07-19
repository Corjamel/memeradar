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
