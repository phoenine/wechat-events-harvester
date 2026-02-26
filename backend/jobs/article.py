from core.articles import article_repo
from core.common.config import DEBUG, cfg
from core.common.log import logger


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
        logger.info(f"创建文章失败: {e}")
    return False


def Update_Over(data=None):
    logger.info("更新完成")
    pass
