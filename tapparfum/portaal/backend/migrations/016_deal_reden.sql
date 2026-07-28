-- ============================================================================
-- TapParfum Portaal — Deals: won/lost-reden (CRM-verdieping)
-- ----------------------------------------------------------------------------
-- Voegt een vrije-tekst 'reden' toe aan een deal. Bedoeld om bij afsluiten
-- (fase 'gewonnen' of 'verloren') vast te leggen wáárom — de basis voor
-- win/loss-analyse. RLS blijft zoals die is: rij-niveau (AM van de winkel +
-- kantoor); een extra kolom valt automatisch onder hetzelfde beleid.
-- Idempotent: veilig meerdere keren te draaien.
-- ============================================================================
alter table public.deals add column if not exists reden text;
