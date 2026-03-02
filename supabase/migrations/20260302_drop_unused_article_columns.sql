-- 删除 articles 表中不再使用的字段
ALTER TABLE public.articles
    DROP COLUMN IF EXISTS author,
    DROP COLUMN IF EXISTS digest,
    DROP COLUMN IF EXISTS publish_at,
    DROP COLUMN IF EXISTS read_num,
    DROP COLUMN IF EXISTS like_num,
    DROP COLUMN IF EXISTS comment_count,
    DROP COLUMN IF EXISTS reward_num,
    DROP COLUMN IF EXISTS copyright_stat,
    DROP COLUMN IF EXISTS is_top,
    DROP COLUMN IF EXISTS first_data,
    DROP COLUMN IF EXISTS status;

-- 删除已无意义的索引
DROP INDEX IF EXISTS idx_articles_publish_at;
DROP INDEX IF EXISTS idx_articles_status;
