-- ============================================================================
-- 017 — Winkelvragen: extra types 'mijlpaal' en 'bezoek' toestaan
-- ----------------------------------------------------------------------------
-- WAAROM: de frontend stuurt bij een vrijgespeelde beloning / behaalde mijlpaal
-- automatisch een bericht met type 'mijlpaal' ("regel de uitkering"), zodat de
-- accountmanager het op de berichtlijn en in Vandaag ziet. De oorspronkelijke
-- CHECK (001..007) stond alleen 'vraag','probleem','retour' toe, waardoor die
-- insert stil faalde (de client vangt de fout en negeert 'm) — de AM kreeg de
-- mijlpaal dus nooit te zien. 'bezoek' bereidt de partner-bezoekaanvraag voor.
--
-- Idempotent. Draai NA 007. Gevalideerd op PostgreSQL 16.
-- ============================================================================

alter table public.winkelvragen
  drop constraint if exists winkelvragen_type_check;

alter table public.winkelvragen
  add constraint winkelvragen_type_check
  check (type in ('vraag','probleem','retour','bezoek','mijlpaal'));
