from fastapi import APIRouter, Depends, HTTPException, status as fast_status, Query, Body
from core.integrations.supabase.auth import get_current_user
from core.articles import article_repo
from core.feeds import feed_repo
from core.integrations.supabase.storage import supabase_storage_articles
from schemas import success_response, error_response, format_search_kw
from core.common.log import logger
from typing import Optional, List, Dict, Any, cast
import re

router = APIRouter(prefix=f"/articles", tags=["文章管理"])


def _extract_storage_paths_from_content(content: str) -> List[str]:
    """从文章 HTML 中提取 article-images 桶对象路径。"""
    html = str(content or "")
    if not html:
        return []
    bucket = supabase_storage_articles.bucket
    public_prefix = f"/storage/v1/object/public/{bucket}/"
    sign_prefix = f"/storage/v1/object/sign/{bucket}/"
    paths: set[str] = set()

    for src in re.findall(r"""(?:src|data-src)\s*=\s*["']([^"']+)["']""", html):
        value = (src or "").strip()
        if not value:
            continue
        if public_prefix in value:
            paths.add(value.split(public_prefix, 1)[1].split("?", 1)[0])
            continue
        if sign_prefix in value:
            paths.add(value.split(sign_prefix, 1)[1].split("?", 1)[0])
            continue
        # 兼容直接存对象路径的情况
        if value.startswith("articles/"):
            paths.add(value)
    return [p for p in paths if p]


async def _delete_article_storage_objects(article: Dict[str, Any]) -> int:
    content = str(article.get("content") or "")
    paths = _extract_storage_paths_from_content(content)
    if not paths:
        return 0
    deleted = 0
    for path in paths:
        ok = await supabase_storage_articles.delete_object(path)
        if ok:
            deleted += 1
    return deleted


@router.get("", summary="获取文章列表")
async def get_articles(
    mp_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=100),
    _current_user: dict = Depends(get_current_user),
):
    try:
        # 转换状态参数
        status_int = None
        if status is not None:
            try:
                status_int = int(status)
            except ValueError:
                status_int = 1  # 默认状态

        articles_raw = await article_repo.get_articles(
            mp_id=mp_id,
            status=status_int,
            limit=limit,
            offset=offset,
            order_by="publish_at",
        )
        # 显式标注类型，便于静态类型检查
        articles: List[Dict[str, Any]] = cast(List[Dict[str, Any]], articles_raw)

        total = await article_repo.count_articles(
            mp_id=mp_id,
            status=status_int,
        )

        # 获取相关的feed信息
        mp_ids = {article.get("mp_id") for article in articles}
        mp_names = {}

        if mp_ids:
            feeds_raw = await feed_repo.get_feeds()
            feeds: List[Dict[str, Any]] = cast(List[Dict[str, Any]], feeds_raw)
            for feed in feeds:
                if feed["id"] in mp_ids:
                    mp_names[feed["id"]] = feed["name"]

        # 合并公众号名称到文章列表
        article_list = []
        for article in articles:
            article_dict = article.copy()
            article_dict["mp_name"] = mp_names.get(article.get("mp_id"), "未知公众号")
            article_list.append(article_dict)

        return success_response({"list": article_list, "total": total})

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取文章列表失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"获取文章列表失败: {str(e)}"),
        )


@router.get("/{article_id}", summary="获取文章详情")
async def get_article_detail(
    article_id: str,
    _current_user: dict = Depends(get_current_user),
):
    try:
        article = await article_repo.get_articles_by_id(article_id)

        if not article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="文章不存在"),
            )

        return success_response(article)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取文章详情失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"获取文章详情失败: {str(e)}"),
        )


@router.get("/{article_id}/next", summary="获取下一篇文章")
async def get_next_article(
    article_id: str, _current_user: dict = Depends(get_current_user)
):
    try:
        # 获取当前文章
        current_article_raw = await article_repo.get_articles_by_id(article_id)
        current_article: Dict[str, Any] = cast(Dict[str, Any], current_article_raw)
        if not current_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="当前文章不存在"),
            )
        # 获取同一公众号的文章
        articles_raw = await article_repo.get_articles(
            mp_id=current_article["mp_id"], order_by="publish_at"
        )
        articles: List[Dict[str, Any]] = cast(List[Dict[str, Any]], articles_raw)

        # 找到当前文章的位置
        current_index = None
        for i, article in enumerate(articles):
            if article["id"] == article_id:
                current_index = i
                break

        if current_index is None or current_index == 0:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(code=40402, message="没有下一篇文章"),
            )

        # 返回下一篇文章
        next_article = articles[current_index - 1]
        return success_response(next_article)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取下一篇文章失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"获取下一篇文章失败: {str(e)}"),
        )


@router.get("/{article_id}/prev", summary="获取上一篇文章")
async def get_prev_article(
    article_id: str, _current_user: dict = Depends(get_current_user)
):
    try:
        # 获取当前文章
        current_article_raw = await article_repo.get_articles_by_id(article_id)
        current_article: Dict[str, Any] = cast(Dict[str, Any], current_article_raw)
        if not current_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="当前文章不存在"),
            )

        # 获取同一公众号的文章
        articles_raw = await article_repo.get_articles(
            mp_id=current_article["mp_id"], order_by="publish_at"
        )
        articles: List[Dict[str, Any]] = cast(List[Dict[str, Any]], articles_raw)

        # 找到当前文章的位置
        current_index = None
        for i, article in enumerate(articles):
            if article["id"] == article_id:
                current_index = i
                break

        if current_index is None or current_index >= len(articles) - 1:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(code=40403, message="没有上一篇文章"),
            )

        # 返回上一篇文章
        prev_article = articles[current_index + 1]
        return success_response(prev_article)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取上一篇文章失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"获取上一篇文章失败: {str(e)}"),
        )


@router.delete("/clean_expired", summary="清理过期文章(删除15天前的publish_at)")
async def clean_expired_articles(_current_user: dict = Depends(get_current_user)):
    try:
        deleted_count = await article_repo.clean_expired_articles()
        return success_response(
            {"message": "清理过期文章成功", "deleted_count": deleted_count}
        )
    except Exception as e:
        logger.error(f"清理过期文章错误: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_201_CREATED,
            detail=error_response(code=50001, message="清理过期文章失败"),
        )


@router.delete("/clean", summary="清理无效文章(MP_ID不存在于Feeds表中的文章)")
async def clean_orphan_articles(_current_user: dict = Depends(get_current_user)):
    try:
        # 获取所有有效的feed ID
        feeds_raw = await feed_repo.get_feeds()
        feeds: List[Dict[str, Any]] = cast(List[Dict[str, Any]], feeds_raw)
        valid_feed_ids = {feed["id"] for feed in feeds}

        # 获取所有文章
        articles_raw = await article_repo.get_articles()
        articles: List[Dict[str, Any]] = cast(List[Dict[str, Any]], articles_raw)

        deleted_count = 0
        for article in articles:
            if article["mp_id"] not in valid_feed_ids:
                await article_repo.delete_article(article["id"])
                deleted_count += 1

        return success_response(
            {"message": "清理无效文章成功", "deleted_count": deleted_count}
        )
    except Exception as e:
        logger.error(f"清理无效文章错误: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_201_CREATED,
            detail=error_response(code=50001, message="清理无效文章失败"),
        )


@router.delete("/clean_duplicate_articles", summary="清理重复文章")
async def clean_duplicate(_current_user: dict = Depends(get_current_user)):
    try:
        from core.articles.cleaning import clean_duplicate_articles

        (msg, deleted_count) = clean_duplicate_articles()
        return success_response({"message": msg, "deleted_count": deleted_count})
    except Exception as e:
        logger.error(f"清理重复文章: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_201_CREATED,
            detail=error_response(code=50001, message="清理重复文章"),
        )


@router.delete("/batch", summary="批量删除文章")
async def delete_articles_batch(
    article_ids: List[str] = Body(..., embed=True),
    _current_user: dict = Depends(get_current_user),
):
    try:
        ids = [str(i).strip() for i in (article_ids or []) if str(i).strip()]
        if not ids:
            raise HTTPException(
                status_code=fast_status.HTTP_400_BAD_REQUEST,
                detail=error_response(code=40001, message="article_ids 不能为空"),
            )

        rows_raw = await article_repo.get_articles_base(filters={"id": {"in": ids}})
        rows: List[Dict[str, Any]] = cast(List[Dict[str, Any]], rows_raw)
        rows_by_id = {str(r.get("id")): r for r in rows}

        deleted_count = 0
        storage_deleted_count = 0
        missing_ids: List[str] = []
        failed_ids: List[str] = []

        for article_id in ids:
            article = rows_by_id.get(article_id)
            if not article:
                missing_ids.append(article_id)
                continue
            try:
                storage_deleted_count += await _delete_article_storage_objects(article)
                await article_repo.delete_article(article_id)
                deleted_count += 1
            except Exception:
                failed_ids.append(article_id)

        return success_response(
            {
                "deleted_count": deleted_count,
                "storage_deleted_count": storage_deleted_count,
                "missing_ids": missing_ids,
                "failed_ids": failed_ids,
            },
            message=f"批量删除完成，成功 {deleted_count} 篇",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除文章失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"批量删除文章失败: {str(e)}"),
        )


@router.delete("/{article_id}", summary="删除文章")
async def delete_article(
    article_id: str, _current_user: dict = Depends(get_current_user)
):
    try:
        # 检查文章是否存在
        article_rows = await article_repo.get_articles_by_id(article_id)
        if not article_rows:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(code=40401, message="文章不存在"),
            )
        article = article_rows[0]

        # 删除关联的 storage 图片对象（best-effort）
        storage_deleted = await _delete_article_storage_objects(article)

        # 删除文章
        await article_repo.delete_article(article_id)

        return success_response(
            {"storage_deleted": storage_deleted},
            message="文章已删除",
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"删除文章失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"删除文章失败: {str(e)}"),
        )
