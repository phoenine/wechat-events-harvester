-- 修复已执行过旧版迁移的环境：
-- feeds.tag_id 误为 text 时，转换为 integer 并补齐外键/索引

alter table if exists public.feeds
  add column if not exists tag_id integer;

do $$
declare
  col_type text;
begin
  select data_type
  into col_type
  from information_schema.columns
  where table_schema = 'public'
    and table_name = 'feeds'
    and column_name = 'tag_id';

  if col_type = 'text' then
    alter table public.feeds
      alter column tag_id type integer
      using (nullif(tag_id, '')::integer);
  end if;
end
$$;

alter table if exists public.feeds
  drop constraint if exists feeds_tag_id_fkey;

alter table if exists public.feeds
  add constraint feeds_tag_id_fkey
  foreign key (tag_id) references public.tags(id)
  on delete set null;

create index if not exists idx_feeds_tag_id
  on public.feeds(tag_id);
