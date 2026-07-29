-- ============================================================================
-- 019 — Sales Game: landelijk klassement (server-aggregaat, geanonimiseerd)
-- ----------------------------------------------------------------------------
-- WAAROM: de Sales Game is een LANDELIJKE competitie, maar RLS geeft een partner
-- alleen de eigen winkel terug — dus zag die "positie 1 van 1". Dit aggregaat
-- rekent server-side over ALLE traject-tappunten en geeft alleen een
-- geanonimiseerd klassement terug: rang, klasse, score, groei% en — behalve voor
-- de eigen winkel / staf / de eigen AM — een gemaskeerde naam ("Winkel #n").
--
-- De score is EXACT de frontend-score (modules/salesgame/logic.js gameScoreVan +
-- modules/punten/logic.js totaalScore). BELANGRIJK: de punt-gewichten hieronder
-- spiegelen BASIS/BONUS_MANUAL uit punten/logic.js — wijzig je die daar, pas ze
-- dan hier ook aan. (Gevalideerd tegen de JS met een lokale Postgres-run.)
--
-- Idempotent. Draai NA 002 (tp_am_id) en 006 (tp_is_eigen_winkel). PostgreSQL 16.
-- ============================================================================

create or replace function public.tp_salesgame_board(
  p_min_punten int default 0, p_min_basis numeric default 0)
returns table(
  rang int, klasse text, score int, groei_pct int, jo numeric,
  reden text, tekort int, is_zelf boolean, naam text)
language sql stable security definer set search_path = public as $$
with base as (
  select tp.snelstart, tp.name, tp.auth_user_id, tp.am_id, tp.data as d,
    coalesce((tp.data->>'jaaromzet')::numeric, 0) as jo,
    coalesce((tp.data->>'vorigJaar')::numeric, 0) as vj,
    nullif(tp.data->>'liveDate', '') as live
  from public.tappunten tp
  where coalesce(tp.data->>'traject', '') <> 'false'   -- inTraject: traject !== false
),
calc as (
  select b.*,
    case when b.live is not null and left(b.live, 4) = to_char(now(), 'YYYY')
         then greatest(extract(month from now())::int - substring(b.live, 6, 2)::int + 1, 1)
         else extract(month from now())::int end as m
  from base b
),
grow as (
  select c.*,
    case when c.m < 2 or c.vj <= 0 then null
         else ((c.jo / c.m) - (c.vj / 12.0)) / (c.vj / 12.0) end as groei
  from calc c
),
eff as (
  select g.*,
    case when coalesce((g.d->'goal'->>'doel')::numeric, 0) > 0
         then coalesce((g.d->'goal'->>'doel')::numeric, 0)
         else coalesce((g.d->>'doel')::numeric, 0) end as effdoel
  from grow g
),
scored as (
  select e.*,
    (select coalesce(sum(pt), 0) from (values
       ('geuren',6),('prijzen',5),('link',1),('amcontact',1),('kwaliteit',5),('geurnotenboek',5),
       ('home',5),('exclusief',5),('bodymist',3),('zichtbaar',5),('presentatie',10),('hoek',5),
       ('hashtags',3),('promopakket',3),('certificaat',5),('voorraad',3)) w(k, pt)
      where (e.d->'bp'->>w.k) = 'true') as basis,
    (select coalesce(sum(pt), 0) from (values
       ('geuravond',5),('weekpost',5),('eigenacties',5),('gnbdagelijks',2),('dagtarget',5),
       ('wederverkoper',5),('nieuwmodule',5),('excluit',3)) w(k, pt)
      where (e.d->'bonus'->>w.k) = 'true') as bonush,
    coalesce((select sum((v->>'punten')::numeric) from jsonb_each(e.d->'actieDeelname') as a(k, v)), 0) as actiep,
    coalesce((select count(*) from jsonb_each(e.d->'actieDeelname') as a(k, v) where (v->>'res') = 'true'), 0)::int as acties,
    case when e.groei is null then 0
         when e.groei >= 1.5 then 10 when e.groei >= 1.0 then 8 when e.groei >= 0.75 then 6
         when e.groei >= 0.5 then 4 when e.groei >= 0.25 then 2 else 0 end as gpunt,
    case when e.effdoel > 0 and e.jo >= e.effdoel then 5 else 0 end as jdpunt,
    case when (e.d ? 'be') and (e.d->>'beDoneAt') is not null and e.live is not null and (e.d->'be'->>'days') is not null
         then case
                when (e.d->>'beDoneAt')::date - e.live::date <= (e.d->'be'->>'days')::numeric * 0.75 then 8
                when (e.d->>'beDoneAt')::date - e.live::date <= (e.d->'be'->>'days')::numeric then 5
                else 0 end
         else 0 end as bepunt
  from eff e
),
tot as (
  select s.*,
    (s.basis + s.bonush + s.gpunt + s.jdpunt + s.bepunt + s.actiep)::numeric as totscore,
    case when s.groei is null then null else round(s.groei * 100)::int end as gpct
  from scored s
),
klas as (
  select t.*,
    (coalesce(t.gpct, 0) + t.acties * 5 + least(20, round(t.totscore * 0.2))::int)::int as gscore,
    case when t.totscore < p_min_punten then 'nietq'
         when t.gpct is null then 'nieuw'
         when t.vj < p_min_basis then 'nietq'
         else 'groei' end as klasse,
    case when t.totscore < p_min_punten then 'punten'
         when t.gpct is not null and t.vj < p_min_basis then 'basis'
         else null end as reden
  from tot t
),
ranked as (
  select k.*,
    case when k.klasse = 'groei' then row_number() over (partition by k.klasse order by k.gscore desc, k.snelstart)
         when k.klasse = 'nieuw' then row_number() over (partition by k.klasse order by k.jo desc, k.snelstart)
         else null end::int as r
  from klas k
)
select
  r as rang, klasse, gscore as score, gpct as groei_pct, jo,
  reden,
  case when reden = 'punten' then greatest(p_min_punten - totscore, 0)::int else 0 end as tekort,
  (auth_user_id is not null and auth_user_id = auth.uid()) as is_zelf,
  case when public.tp_is_staff()
         or (auth_user_id is not null and auth_user_id = auth.uid())
         or (am_id is not null and am_id = public.tp_am_id())
       then name else 'Winkel #' || coalesce(r, 0) end as naam
from ranked
order by klasse, r nulls last;
$$;

revoke all on function public.tp_salesgame_board(int, numeric) from public;
grant execute on function public.tp_salesgame_board(int, numeric) to authenticated;
