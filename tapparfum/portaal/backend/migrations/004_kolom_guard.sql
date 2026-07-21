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
