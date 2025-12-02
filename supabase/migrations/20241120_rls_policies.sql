-- 启用RLS（行级安全）
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feeds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.article_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_task_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.config_management ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_sessions ENABLE ROW LEVEL SECURITY;

-- 用户资料表策略（profiles）
CREATE POLICY "用户只能查看自己的资料" ON public.profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "用户可以更新自己的资料" ON public.profiles
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "用户可以插入自己的资料" ON public.profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 订阅源表策略 - 所有认证用户都可以查看和操作
CREATE POLICY "认证用户可以查看订阅源" ON public.feeds
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以创建订阅源" ON public.feeds
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以更新订阅源" ON public.feeds
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以删除订阅源" ON public.feeds
    FOR DELETE USING (auth.role() = 'authenticated');

-- 文章表策略 - 所有认证用户都可以查看和操作
CREATE POLICY "认证用户可以查看文章" ON public.articles
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以创建文章" ON public.articles
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以更新文章" ON public.articles
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以删除文章" ON public.articles
    FOR DELETE USING (auth.role() = 'authenticated');

-- 标签表策略 - 所有认证用户都可以查看和操作
CREATE POLICY "认证用户可以查看标签" ON public.tags
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以创建标签" ON public.tags
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以更新标签" ON public.tags
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以删除标签" ON public.tags
    FOR DELETE USING (auth.role() = 'authenticated');

-- 文章标签关联表策略 - 所有认证用户都可以操作
CREATE POLICY "认证用户可以查看文章标签关联" ON public.article_tags
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以创建文章标签关联" ON public.article_tags
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以删除文章标签关联" ON public.article_tags
    FOR DELETE USING (auth.role() = 'authenticated');

-- 消息任务表策略 - 所有认证用户都可以操作
CREATE POLICY "认证用户可以查看消息任务" ON public.message_tasks
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以创建消息任务" ON public.message_tasks
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以更新消息任务" ON public.message_tasks
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以删除消息任务" ON public.message_tasks
    FOR DELETE USING (auth.role() = 'authenticated');

-- 消息任务日志表策略 - 所有认证用户都可以查看
CREATE POLICY "认证用户可以查看消息任务日志" ON public.message_task_logs
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "认证用户可以创建消息任务日志" ON public.message_task_logs
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- 配置表策略 - 所有认证用户都可以查看，但只有服务角色可以修改
CREATE POLICY "认证用户可以查看配置" ON public.config_management
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "服务角色可以管理配置" ON public.config_management
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- 认证会话表策略 - 用户只能查看自己的会话
CREATE POLICY "用户可以查看自己的认证会话" ON public.auth_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "用户可以创建认证会话" ON public.auth_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "用户可以更新自己的认证会话" ON public.auth_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "用户可以删除自己的认证会话" ON public.auth_sessions
    FOR DELETE USING (auth.uid() = user_id);


-- 授权基本权限
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;

-- 授权特定表的插入权限给匿名用户（用于注册）
GRANT INSERT ON public.profiles TO anon;