-- ============================================================================
-- 018 — Winkelvragen: 'nieuw voor partner'-signaal (nieuw antwoord)
-- ----------------------------------------------------------------------------
-- WAAROM: als de AM/kantoor een winkelvraag beantwoordt, hoort de partner een
-- signaal te krijgen ("er is een nieuw antwoord") — net als v71's nieuwVoorP.
-- Zonder dit telde de partner-badge juist de eigen OPEN meldingen en zakte die
-- bij een antwoord (omgekeerde semantiek).
--
-- MODEL:
--   * kolom nieuw_voor_partner: zet de AM/kantoor op TRUE bij het beantwoorden
--     (mag: de kolom-guard 007 laat niet-staf alleen tappunt/type/txt/created_at
--      met rust; status/antwoord/dit veld blijven schrijfbaar voor de AM).
--   * De partner heeft BEWUST geen UPDATE-recht op winkelvragen (007), dus het
--     wissen ("gezien") loopt via een security-definer-RPC die STRIKT alleen de
--     eigen winkel raakt en alleen dit ene veld op false zet.
--
-- Idempotent. Draai NA 007. Gevalideerd op PostgreSQL 16.
-- ============================================================================

alter table public.winkelvragen
  add column if not exists nieuw_voor_partner boolean not null default false;

-- Partner markeert de antwoorden van de EIGEN winkel als gezien. Security definer
-- omdat de partner geen directe UPDATE mag; de WHERE bindt hard aan auth.uid()
-- via de eigen tappunten, en alleen nieuw_voor_partner wordt geraakt.
create or replace function public.tp_winkelvraag_gezien()
returns void language sql security definer set search_path = public as $$
  update public.winkelvragen w
     set nieuw_voor_partner = false
   where w.nieuw_voor_partner
     and w.tappunt_snelstart in (
       select tp.snelstart from public.tappunten tp
        where tp.auth_user_id = auth.uid());
$$;

revoke all on function public.tp_winkelvraag_gezien() from public;
grant execute on function public.tp_winkelvraag_gezien() to authenticated;
