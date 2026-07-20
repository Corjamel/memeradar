-- ============================================================================
-- TapParfum Portal — Documenten via Supabase Storage (Fase 2c)
-- Privé bucket 'tp-docs' + toegangsregels: een partner ziet/upload alleen in de
-- map van zijn eigen winkel, een AM in die van zijn winkels, kantoor (staff) overal.
-- Bestandspad = "<snelstartcode>/<tijd>_<naam>". Draai dit NÁ schema.sql + schema_am.sql.
-- Idempotent. (Storage-RLS is Supabase-specifiek; draai in de SQL Editor.)
-- ============================================================================

-- 1) Privé bucket
insert into storage.buckets (id, name, public)
values ('tp-docs', 'tp-docs', false)
on conflict (id) do nothing;

-- Helper: hoort de ingelogde gebruiker bij de winkel van dit bestandspad?
-- (eerste mapnaam = snelstartcode)
create or replace function public.tp_mag_bij_pad(objectname text)
returns boolean language sql stable security definer set search_path = public as $$
  select public.tp_is_staff() or exists (
    select 1 from public.tappunten tp
     where lower(tp.snelstart) = lower(split_part(objectname, '/', 1))
       and (tp.auth_user_id = auth.uid() or tp.am_id = public.tp_am_id())
  );
$$;

-- 2) Toegangsregels op de objecten in deze bucket
drop policy if exists tpdocs_select on storage.objects;
create policy tpdocs_select on storage.objects
  for select to authenticated
  using (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name));

drop policy if exists tpdocs_insert on storage.objects;
create policy tpdocs_insert on storage.objects
  for insert to authenticated
  with check (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name));

drop policy if exists tpdocs_update on storage.objects;
create policy tpdocs_update on storage.objects
  for update to authenticated
  using (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name))
  with check (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name));

drop policy if exists tpdocs_delete on storage.objects;
create policy tpdocs_delete on storage.objects
  for delete to authenticated
  using (bucket_id = 'tp-docs' and public.tp_mag_bij_pad(name));

-- ============================================================================
-- KLAAR. In het portaal: partner/AM/kantoor -> tappunt-dashboard -> 📎 Documenten.
-- Zonder cloud-sessie werkt het lokaal (kleine bestanden); ingelogd via de cloud
-- gaan bestanden naar deze bucket en worden ze met tijdelijke (signed) links
-- geopend — nooit publiek toegankelijk.
-- ============================================================================
