-- 一对多标签设计：一个 tag 对应多个 feed
-- 在 feeds 上增加 tag_id（integer），替代 feed_tags 关系表

alter table if exists public.feeds
  add column if not exists tag_id integer;

-- 兼容历史执行：若 tag_id 已是 text，则尝试安全转换为 integer
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

do $$
begin
  if not exists (
    select 1
    from information_schema.table_constraints
    where constraint_schema = 'public'
      and table_name = 'feeds'
      and constraint_name = 'feeds_tag_id_fkey'
  ) then
    alter table public.feeds
      add constraint feeds_tag_id_fkey
      foreign key (tag_id) references public.tags(id)
      on delete set null;
  end if;
end
$$;

create index if not exists idx_feeds_tag_id
  on public.feeds(tag_id);

-- 若历史存在 feed_tags，则迁移数据（同一个 feed 多个 tag 时保留一条）
do $$
begin
  if exists (
    select 1
    from information_schema.tables
    where table_schema = 'public' and table_name = 'feed_tags'
  ) then
    with chosen as (
      select feed_id, min(tag_id::integer) as tag_id
      from public.feed_tags
      group by feed_id
    )
    update public.feeds f
    set tag_id = c.tag_id
    from chosen c
    where f.id = c.feed_id and (f.tag_id is null or f.tag_id = '');
  end if;
end
$$;
