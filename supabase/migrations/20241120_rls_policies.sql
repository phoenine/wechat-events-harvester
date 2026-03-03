-- RLS 基线策略（已与当前表结构对齐）

alter table public.profiles enable row level security;
alter table public.feeds enable row level security;
alter table public.articles enable row level security;
alter table public.article_images enable row level security;
alter table public.tags enable row level security;
alter table public.message_tasks enable row level security;
alter table public.message_task_logs enable row level security;
alter table public.config_managements enable row level security;
alter table public.auth_sessions enable row level security;
alter table public.auth_session_secret enable row level security;

-- profiles
drop policy if exists "用户只能查看自己的资料" on public.profiles;
create policy "用户只能查看自己的资料"
on public.profiles for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "用户可以更新自己的资料" on public.profiles;
create policy "用户可以更新自己的资料"
on public.profiles for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "用户可以插入自己的资料" on public.profiles;
create policy "用户可以插入自己的资料"
on public.profiles for insert
to authenticated
with check (auth.uid() = user_id);

-- feeds
drop policy if exists "认证用户可以查看订阅源" on public.feeds;
create policy "认证用户可以查看订阅源"
on public.feeds for select
to authenticated
using (true);

drop policy if exists "认证用户可以创建订阅源" on public.feeds;
create policy "认证用户可以创建订阅源"
on public.feeds for insert
to authenticated
with check (true);

drop policy if exists "认证用户可以更新订阅源" on public.feeds;
create policy "认证用户可以更新订阅源"
on public.feeds for update
to authenticated
using (true)
with check (true);

drop policy if exists "认证用户可以删除订阅源" on public.feeds;
create policy "认证用户可以删除订阅源"
on public.feeds for delete
to authenticated
using (true);

-- articles
drop policy if exists "认证用户可以查看文章" on public.articles;
create policy "认证用户可以查看文章"
on public.articles for select
to authenticated
using (true);

drop policy if exists "认证用户可以创建文章" on public.articles;
create policy "认证用户可以创建文章"
on public.articles for insert
to authenticated
with check (true);

drop policy if exists "认证用户可以更新文章" on public.articles;
create policy "认证用户可以更新文章"
on public.articles for update
to authenticated
using (true)
with check (true);

drop policy if exists "认证用户可以删除文章" on public.articles;
create policy "认证用户可以删除文章"
on public.articles for delete
to authenticated
using (true);

-- article_images
drop policy if exists "认证用户可以查看文章图片映射" on public.article_images;
create policy "认证用户可以查看文章图片映射"
on public.article_images for select
to authenticated
using (true);

drop policy if exists "认证用户可以写入文章图片映射" on public.article_images;
create policy "认证用户可以写入文章图片映射"
on public.article_images for insert
to authenticated
with check (true);

drop policy if exists "认证用户可以更新文章图片映射" on public.article_images;
create policy "认证用户可以更新文章图片映射"
on public.article_images for update
to authenticated
using (true)
with check (true);

drop policy if exists "认证用户可以删除文章图片映射" on public.article_images;
create policy "认证用户可以删除文章图片映射"
on public.article_images for delete
to authenticated
using (true);

-- tags
drop policy if exists "认证用户可以查看标签" on public.tags;
create policy "认证用户可以查看标签"
on public.tags for select
to authenticated
using (true);

drop policy if exists "认证用户可以创建标签" on public.tags;
create policy "认证用户可以创建标签"
on public.tags for insert
to authenticated
with check (true);

drop policy if exists "认证用户可以更新标签" on public.tags;
create policy "认证用户可以更新标签"
on public.tags for update
to authenticated
using (true)
with check (true);

drop policy if exists "认证用户可以删除标签" on public.tags;
create policy "认证用户可以删除标签"
on public.tags for delete
to authenticated
using (true);

-- message_tasks
drop policy if exists "认证用户可以查看消息任务" on public.message_tasks;
create policy "认证用户可以查看消息任务"
on public.message_tasks for select
to authenticated
using (true);

drop policy if exists "认证用户可以创建消息任务" on public.message_tasks;
create policy "认证用户可以创建消息任务"
on public.message_tasks for insert
to authenticated
with check (true);

drop policy if exists "认证用户可以更新消息任务" on public.message_tasks;
create policy "认证用户可以更新消息任务"
on public.message_tasks for update
to authenticated
using (true)
with check (true);

drop policy if exists "认证用户可以删除消息任务" on public.message_tasks;
create policy "认证用户可以删除消息任务"
on public.message_tasks for delete
to authenticated
using (true);

-- message_task_logs
drop policy if exists "认证用户可以查看消息任务日志" on public.message_task_logs;
create policy "认证用户可以查看消息任务日志"
on public.message_task_logs for select
to authenticated
using (true);

drop policy if exists "认证用户可以创建消息任务日志" on public.message_task_logs;
create policy "认证用户可以创建消息任务日志"
on public.message_task_logs for insert
to authenticated
with check (true);

-- config_managements
drop policy if exists "认证用户可以查看配置" on public.config_managements;
create policy "认证用户可以查看配置"
on public.config_managements for select
to authenticated
using (true);

drop policy if exists "服务角色可以管理配置" on public.config_managements;
create policy "服务角色可以管理配置"
on public.config_managements for all
to service_role
using (true)
with check (true);

-- auth_sessions
drop policy if exists "用户可以查看自己的认证会话" on public.auth_sessions;
create policy "用户可以查看自己的认证会话"
on public.auth_sessions for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "用户可以创建认证会话" on public.auth_sessions;
create policy "用户可以创建认证会话"
on public.auth_sessions for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "用户可以更新自己的认证会话" on public.auth_sessions;
create policy "用户可以更新自己的认证会话"
on public.auth_sessions for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "用户可以删除自己的认证会话" on public.auth_sessions;
create policy "用户可以删除自己的认证会话"
on public.auth_sessions for delete
to authenticated
using (auth.uid() = user_id);

-- auth_session_secret（仅 service role）
drop policy if exists "secret_service_only_select" on public.auth_session_secret;
create policy "secret_service_only_select"
on public.auth_session_secret for select
to service_role
using (true);

drop policy if exists "secret_service_only_mod" on public.auth_session_secret;
create policy "secret_service_only_mod"
on public.auth_session_secret for all
to service_role
using (true)
with check (true);

-- 基本权限
grant usage on schema public to anon, authenticated;
grant all on all tables in schema public to authenticated;
grant all on all sequences in schema public to authenticated;
grant select on all tables in schema public to anon;
grant select on all sequences in schema public to anon;

-- 匿名注册场景允许插入 profiles
grant insert on public.profiles to anon;
