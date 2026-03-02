-- 为 tags 表补充前端需要的字段
ALTER TABLE public.tags
    ADD COLUMN IF NOT EXISTS cover TEXT,
    ADD COLUMN IF NOT EXISTS status INTEGER DEFAULT 1;
