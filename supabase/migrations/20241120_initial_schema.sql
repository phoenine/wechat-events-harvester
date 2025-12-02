-- 创建用户扩展资料表 profiles
CREATE TABLE IF NOT EXISTS public.profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
    nickname TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 订阅源表
CREATE TABLE IF NOT EXISTS public.feeds (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    avatar_url TEXT,
    qr_url TEXT,
    qr_signed_url TEXT,
    faker_id TEXT,
    biz TEXT,
    gh_id TEXT,
    uin TEXT,
    key TEXT,
    pass_ticket TEXT,
    cookies TEXT,
    last_publish TIMESTAMP WITH TIME ZONE,
    last_fetch TIMESTAMP WITH TIME ZONE,
    status INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 文章表
CREATE TABLE IF NOT EXISTS public.articles (
    id TEXT PRIMARY KEY,
    mp_id TEXT REFERENCES public.feeds (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    author TEXT,
    digest TEXT,
    content TEXT,
    content_md TEXT,
    cover_url TEXT,
    publish_time BIGINT,
    publish_at TIMESTAMP WITH TIME ZONE,
    read_num INTEGER DEFAULT 0,
    like_num INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    reward_num INTEGER DEFAULT 0,
    url TEXT,
    copyright_stat INTEGER DEFAULT 0,
    is_top INTEGER DEFAULT 0,
    first_data TEXT,
    status INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 标签表
CREATE TABLE IF NOT EXISTS public.tags (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 文章标签关联表
CREATE TABLE IF NOT EXISTS public.article_tags (
    article_id TEXT REFERENCES public.articles (id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES public.tags (id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (article_id, tag_id)
);

-- 消息任务表
CREATE TABLE IF NOT EXISTS public.message_tasks (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    cron_expression TEXT,
    target_type TEXT, -- all, tag, mp
    target_ids TEXT, -- comma separated ids
    webhook_url TEXT,
    webhook_type TEXT DEFAULT 'custom', -- custom, dingding, feishu, wechat
    webhook_content_type TEXT DEFAULT 'html', -- html, markdown, text
    status INTEGER DEFAULT 1,
    last_execute TIMESTAMP WITH TIME ZONE,
    next_execute TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 消息任务日志表
CREATE TABLE IF NOT EXISTS public.message_task_logs (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES public.message_tasks (id) ON DELETE CASCADE,
    status TEXT, -- success, failed
    message TEXT,
    article_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 配置管理表
CREATE TABLE IF NOT EXISTS public.config_management (
    id SERIAL PRIMARY KEY,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 认证会话表（用于微信扫码登录）
CREATE TABLE IF NOT EXISTS public.auth_sessions (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users (id) ON DELETE CASCADE,
    status TEXT DEFAULT 'waiting', -- waiting, confirmed, expired
    token TEXT,
    cookies_str TEXT,
    expiry TIMESTAMP WITH TIME ZONE,
    qr_path TEXT,
    qr_signed_url TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_articles_mp_id ON public.articles (mp_id);

CREATE INDEX IF NOT EXISTS idx_articles_publish_at ON public.articles (publish_at);

CREATE INDEX IF NOT EXISTS idx_articles_status ON public.articles (status);

CREATE INDEX IF NOT EXISTS idx_feeds_status ON public.feeds (status);

CREATE INDEX IF NOT EXISTS idx_message_tasks_status ON public.message_tasks (status);

CREATE INDEX IF NOT EXISTS idx_message_task_logs_task_id ON public.message_task_logs (task_id);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON public.auth_sessions (user_id);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_status ON public.auth_sessions (status);

CREATE INDEX IF NOT EXISTS idx_article_tags_article_id ON public.article_tags (article_id);

CREATE INDEX IF NOT EXISTS idx_article_tags_tag_id ON public.article_tags (tag_id);