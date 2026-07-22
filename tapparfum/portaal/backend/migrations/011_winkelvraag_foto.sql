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
