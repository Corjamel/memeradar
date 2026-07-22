-- ============================================================================
-- TapParfum Portaal — Community (besloten tijdlijn per AM-portefeuille)
-- ----------------------------------------------------------------------------
-- v71 (r.3382) legt de keuze vast: de community is BESLOTEN PER accountmanager-
-- portefeuille. Partners van verschillende accountmanagers zien elkaars posts
-- en winkelnamen NIET. Dat is precies de "geen datalek"-eis: een post leeft in
-- één portefeuille (am_id) en is alleen zichtbaar binnen die portefeuille.
--
--   partner  -> leest + plaatst in de portefeuille van zíjn winkel
--   AM       -> leest + plaatst (als accountmanager) in zíjn portefeuille
--   kantoor  -> leest alles (moderatie) + mag verwijderen
--
-- Anti-spoofing: een BEFORE INSERT-guard zet am_id/author/role server-side op
-- basis van wie je bent — een partner kan dus geen post in een andere
-- portefeuille of onder een valse naam plaatsen, ook niet via de rauwe API.
-- Draai NA 001..012. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

create table if not exists public.community (
  id         uuid primary key default gen_random_uuid(),
  am_id      uuid not null references public.accountmanagers(id) on delete cascade,
  author     text not null,
  role       text not null default 'partner' check (role in ('partner', 'am', 'hq')),
  txt        text not null,
  created_at timestamptz not null default now()
);
create index if not exists community_am_idx on public.community(am_id, created_at desc);

alter table public.community enable row level security;

-- De portefeuille (am_id) van de winkel van de ingelogde partner (NULL als de
-- gebruiker geen gekoppelde winkel heeft, bv. een AM of kantoor).
create or replace function public.tp_partner_am_id()
returns uuid language sql stable security definer set search_path = public as $$
  select am_id from public.tappunten
   where auth_user_id = auth.uid() and am_id is not null
   limit 1;
$$;

-- Lezen: kantoor alles; AM zijn portefeuille; partner de portefeuille van zijn
-- winkel. am_id is NOT NULL, dus een NULL-portefeuille matcht bewust niets.
drop policy if exists community_select on public.community;
create policy community_select on public.community
  for select to authenticated
  using (public.tp_is_staff()
         or am_id = public.tp_am_id()
         or am_id = public.tp_partner_am_id());

-- Plaatsen: kantoor overal; AM in eigen portefeuille; partner in de portefeuille
-- van zijn winkel. De guard hieronder maakt de kolommen alsnog waterdicht.
drop policy if exists community_insert on public.community;
create policy community_insert on public.community
  for insert to authenticated
  with check (public.tp_is_staff()
         or am_id = public.tp_am_id()
         or am_id = public.tp_partner_am_id());

-- Wijzigen: niemand herschrijft posts (alleen kantoor, voor correctie).
drop policy if exists community_update on public.community;
create policy community_update on public.community
  for update to authenticated
  using (public.tp_is_staff())
  with check (public.tp_is_staff());

-- Verwijderen (moderatie): alleen kantoor.
drop policy if exists community_delete on public.community;
create policy community_delete on public.community
  for delete to authenticated
  using (public.tp_is_staff());

-- Anti-spoofing-guard: dwingt portefeuille, auteur en rol af aan de bron.
create or replace function public.tp_guard_community()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_am uuid; v_naam text; v_winkel record;
begin
  -- Kantoor mag bewust vrij plaatsen (HQ-mededeling in een gekozen portefeuille).
  if public.tp_is_staff() then
    if new.role is null then new.role := 'hq'; end if;
    return new;
  end if;
  -- Accountmanager: post leeft in zijn eigen portefeuille, onder zijn naam.
  v_am := public.tp_am_id();
  if v_am is not null then
    select naam into v_naam from public.accountmanagers where id = v_am;
    new.am_id  := v_am;
    new.author := coalesce(v_naam, 'Accountmanager');
    new.role   := 'am';
    return new;
  end if;
  -- Partner: post leeft in de portefeuille van zijn winkel, onder de winkelnaam.
  select am_id, name into v_winkel
    from public.tappunten
   where auth_user_id = auth.uid() and am_id is not null
   limit 1;
  if v_winkel.am_id is null then
    raise exception 'Geen winkel/portefeuille gekoppeld aan dit account';
  end if;
  new.am_id  := v_winkel.am_id;
  new.author := v_winkel.name;
  new.role   := 'partner';
  return new;
end; $$;

drop trigger if exists tp_guard_community on public.community;
create trigger tp_guard_community
  before insert on public.community
  for each row execute function public.tp_guard_community();

-- ============================================================================
-- KLAAR. Besloten tijdlijn per portefeuille — geen kruislekken tussen AM's.
-- ============================================================================
