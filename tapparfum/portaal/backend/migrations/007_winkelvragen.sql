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
