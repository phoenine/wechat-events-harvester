# Supabase SQL 整合说明

当前目录已按“新环境可直接初始化”整理，建议执行顺序如下：

1. `supabase/migrations/20241120_initial_schema.sql`
2. `supabase/migrations/20241120_rls_policies.sql`
3. `supabase/config_managements_seed.sql`

## 说明

- `20241120_initial_schema.sql` 已整合当前最终结构，包含：
  - `config_managements`（已统一为复数）
  - `auth_sessions + auth_session_secret`（已统一为分表存敏感字段）
  - `article_images`
  - `feeds.tag_id -> tags.id`（一对多）
- 历史表 `article_tags` / `feed_tags` 不再作为基线创建，相关补丁迁移已移除。

## 配置初始化

- 新环境按上面的 1/2/3 执行即可（`initial_schema` 已包含 `config_managements` 表结构）。
- `supabase/config_managements.sql` 保留用于旧环境单独补齐配置表结构。
- 默认值（幂等 upsert）：`supabase/config_managements_seed.sql`
