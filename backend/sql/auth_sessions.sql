create extension if not exists pgcrypto;

create table if not exists public.auth_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null check (status in ('waiting','scanned','success','expired','error')),
  qr_path text,
  qr_signed_url text,
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_auth_sessions_user on public.auth_sessions(user_id);
create index if not exists idx_auth_sessions_status on public.auth_sessions(status);
create index if not exists idx_auth_sessions_updated on public.auth_sessions(updated_at);

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists trg_auth_sessions_updated on public.auth_sessions;
create trigger trg_auth_sessions_updated
before update on public.auth_sessions
for each row execute function public.set_updated_at();

create table if not exists public.auth_session_secret (
  session_id uuid primary key references public.auth_sessions(id) on delete cascade,
  token text,
  cookies_str text,
  expiry timestamptz,
  created_at timestamptz not null default now()
);

alter table public.auth_sessions enable row level security;
alter table public.auth_session_secret enable row level security;

create policy "session_select_own"
on public.auth_sessions
for select
to authenticated
using (user_id = auth.uid());

create policy "session_insert_own"
on public.auth_sessions
for insert
to authenticated
with check (user_id = auth.uid());

create policy "session_update_own"
on public.auth_sessions
for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "session_delete_own"
on public.auth_sessions
for delete
to authenticated
using (user_id = auth.uid());

create policy "secret_service_only_select"
on public.auth_session_secret
for select
to service_role
using (true);

create policy "secret_service_only_mod"
on public.auth_session_secret
for all
to service_role
using (true)
with check (true);

alter publication supabase_realtime add table public.auth_sessions;
