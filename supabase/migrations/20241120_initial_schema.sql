-- 基线初始化（已整合当前项目实际结构）

create extension if not exists pgcrypto;

-- 通用 updated_at 触发器函数
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;

-- 用户扩展资料
create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  nickname text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 标签
create table if not exists public.tags (
  id serial primary key,
  name text not null unique,
  description text,
  cover text,
  status integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 公众号订阅源
create table if not exists public.feeds (
  id text primary key,
  name text not null,
  description text,
  avatar_url text,
  faker_id text unique,
  tag_id integer references public.tags(id) on delete set null,
  last_publish timestamptz,
  last_fetch timestamptz,
  status integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 文章
create table if not exists public.articles (
  id text primary key,
  mp_id text references public.feeds(id) on delete cascade,
  title text not null,
  content text,
  content_md text,
  is_gathered boolean not null default false,
  publish_time bigint,
  url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 文章图片映射（对应 storage: article-images）
create table if not exists public.article_images (
  id uuid primary key default gen_random_uuid(),
  article_id text not null references public.articles(id) on delete cascade,
  bucket text not null default 'article-images',
  object_path text not null,
  public_url text not null default '',
  origin_url text not null default '',
  position integer not null default 1,
  created_at timestamptz not null default now(),
  unique (article_id, object_path)
);

-- 消息任务
create table if not exists public.message_tasks (
  id uuid primary key default gen_random_uuid(),
  message_template text not null default '',
  web_hook_url text not null default '',
  mps_id text not null default '',
  name text not null default '',
  message_type integer not null default 0,
  cron_exp text not null default '',
  status integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 消息任务日志
create table if not exists public.message_task_logs (
  id bigserial primary key,
  task_id uuid references public.message_tasks(id) on delete cascade,
  status text,
  message text,
  article_count integer not null default 0,
  created_at timestamptz not null default now()
);

-- 配置管理
create table if not exists public.config_managements (
  id bigserial primary key,
  config_key text not null unique,
  config_value text not null default '',
  description text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 微信扫码认证会话
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

-- 会话敏感字段分表存储（仅 service role 可访问）
create table if not exists public.auth_session_secret (
  session_id uuid primary key references public.auth_sessions(id) on delete cascade,
  token text,
  cookies_str text,
  expiry timestamptz,
  created_at timestamptz not null default now()
);

-- 索引
create index if not exists idx_articles_mp_id on public.articles(mp_id);
create index if not exists idx_articles_publish_time on public.articles(publish_time desc);
create index if not exists idx_feeds_status on public.feeds(status);
create index if not exists idx_feeds_tag_id on public.feeds(tag_id);
create index if not exists idx_message_tasks_status on public.message_tasks(status);
create index if not exists idx_message_task_logs_task_id on public.message_task_logs(task_id);
create index if not exists idx_config_managements_key on public.config_managements(config_key);
create index if not exists idx_config_managements_updated_at on public.config_managements(updated_at desc);
create index if not exists idx_auth_sessions_user on public.auth_sessions(user_id);
create index if not exists idx_auth_sessions_status on public.auth_sessions(status);
create index if not exists idx_auth_sessions_updated on public.auth_sessions(updated_at);
create index if not exists idx_article_images_article_id on public.article_images(article_id);
create index if not exists idx_article_images_object_path on public.article_images(object_path);

-- updated_at 触发器
drop trigger if exists trg_profiles_updated on public.profiles;
create trigger trg_profiles_updated
before update on public.profiles
for each row execute function public.set_updated_at();

drop trigger if exists trg_tags_updated on public.tags;
create trigger trg_tags_updated
before update on public.tags
for each row execute function public.set_updated_at();

drop trigger if exists trg_feeds_updated on public.feeds;
create trigger trg_feeds_updated
before update on public.feeds
for each row execute function public.set_updated_at();

drop trigger if exists trg_articles_updated on public.articles;
create trigger trg_articles_updated
before update on public.articles
for each row execute function public.set_updated_at();

drop trigger if exists trg_message_tasks_updated on public.message_tasks;
create trigger trg_message_tasks_updated
before update on public.message_tasks
for each row execute function public.set_updated_at();

drop trigger if exists trg_config_managements_updated on public.config_managements;
create trigger trg_config_managements_updated
before update on public.config_managements
for each row execute function public.set_updated_at();

drop trigger if exists trg_auth_sessions_updated on public.auth_sessions;
create trigger trg_auth_sessions_updated
before update on public.auth_sessions
for each row execute function public.set_updated_at();
