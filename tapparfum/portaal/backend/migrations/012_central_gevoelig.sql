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
