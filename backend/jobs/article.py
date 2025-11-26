from core.repositories import article_repo
from core.config import DEBUG, cfg


def UpdateArticle(art: dict, check_exist: bool = False):
    """更新文章"""
    mps_count = 0
    if DEBUG:
        pass
    try:
        # 使用 Supabase 创建文章
        result = article_repo.sync_create_article(art)
        if result:
            mps_count = mps_count + 1
            return True
    except Exception as e:
        print(f"创建文章失败: {e}")
    return False


def Update_Over(data=None):
    print("更新完成")
    pass
