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
