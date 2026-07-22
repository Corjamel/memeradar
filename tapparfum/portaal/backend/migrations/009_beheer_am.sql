-- ============================================================================
-- TapParfum Portaal — Beheer: accountmanagers uitnodigen per e-mail
-- ----------------------------------------------------------------------------
-- Kantoor voegt een AM toe met naam + e-mailadres (uitnodiging). De AM maakt
-- daarna zelf zijn login aan op het portaal; bij zijn eerste login koppelt
-- tp_koppel_am() zijn account automatisch aan de juiste AM-rij — uitsluitend
-- als zijn ingelogde e-mailadres exact overeenkomt met de uitnodiging.
-- Draai NA 001..008. Idempotent. Gevalideerd op PostgreSQL 16.
-- ============================================================================

alter table public.accountmanagers add column if not exists email text;
create unique index if not exists accountmanagers_email_idx
  on public.accountmanagers (lower(email)) where email is not null;

-- Koppel de ingelogde gebruiker aan zijn AM-uitnodiging (op e-mail).
-- security definer: leest auth.users en schrijft de koppeling, maar ALLEEN
-- voor het eigen account en alleen als de rij nog vrij is (of al van hem is).
create or replace function public.tp_koppel_am()
returns uuid language plpgsql security definer set search_path = public as $$
declare gekoppeld uuid; em text;
begin
  select lower(u.email) into em from auth.users u where u.id = auth.uid();
  if em is null or em = '' then return null; end if;
  update public.accountmanagers
     set auth_user_id = auth.uid()
   where lower(email) = em
     and (auth_user_id is null or auth_user_id = auth.uid())
   returning id into gekoppeld;
  return gekoppeld;
end; $$;

revoke all on function public.tp_koppel_am() from public;
grant execute on function public.tp_koppel_am() to authenticated;

-- ============================================================================
-- KLAAR. Kantoor: Beheer -> AM toevoegen (naam + e-mail). De AM: portaal ->
-- 'Eerste keer' -> accountmanager -> account aanmaken met dat e-mailadres.
-- ============================================================================
