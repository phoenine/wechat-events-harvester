-- articles 字段调整：
-- 1) 删除 cover_url
-- 2) 新增 is_gathered（是否已完成“文章->活动”采集，默认 false）

alter table if exists public.articles
  drop column if exists cover_url;

alter table if exists public.articles
  add column if not exists is_gathered boolean not null default false;

-- 回填历史数据：统一为 false（后续由活动采集流程显式置为 true）
update public.articles
set is_gathered = false
where is_gathered is distinct from false;
