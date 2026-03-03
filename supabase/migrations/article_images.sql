-- 文章图片映射表：
-- - 记录文章与 Supabase Storage(article-images bucket) 对象的对应关系
-- - 用于删除文章时精准清理对象，不依赖从 HTML 反解析

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

create index if not exists idx_article_images_article_id
  on public.article_images(article_id);

create index if not exists idx_article_images_object_path
  on public.article_images(object_path);
