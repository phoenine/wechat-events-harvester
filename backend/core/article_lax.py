from core.repositories import article_repo, feed_repo
from core.models import DataStatus as DATA_STATUS
import json


class ArticleInfo:
    # 没有内容的文章数量
    no_content_count: int = 0
    # 有内容的文章数量
    has_content_count: int = 0
    # 所有文章数量
    all_count: int = 0
    # 不正常的文章数量
    wrong_count: int = 0
    # 公众号总数
    mp_all_count: int = 0


def laxArticle():
    info = ArticleInfo()

    # 所有文章数量
    info.all_count = article_repo.sync_count_articles()

    # 获取没有内容的文章数量 (content为空字符串或null)
    info.no_content_count = article_repo.sync_count_articles(
        filters={"content": {"is": None}}
    )

    # 有内容的文章数量
    info.has_content_count = info.all_count - info.no_content_count

    # 获取删除的文章 (status != 1)
    info.wrong_count = article_repo.sync_count_articles(
        filters={"status": {"neq": DATA_STATUS["ACTIVE"]}}
    )

    # 公众号总数
    info.mp_all_count = feed_repo.sync_count_feeds()

    return info.__dict__
    pass


# ARTICLE_INFO = laxArticle()
# print(ARTICLE_INFO)
ARTICLE_INFO: dict = {}
