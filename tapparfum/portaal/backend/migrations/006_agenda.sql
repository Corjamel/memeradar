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
