create table if not exists public.config_managements (
  id bigserial primary key,
  config_key text not null unique,
  config_value text not null default '',
  description text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists trg_config_managements_updated on public.config_managements;
create trigger trg_config_managements_updated
before update on public.config_managements
for each row execute function public.set_updated_at();

create index if not exists idx_config_managements_key on public.config_managements(config_key);
create index if not exists idx_config_managements_updated_at on public.config_managements(updated_at desc);
