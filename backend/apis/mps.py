import time
from datetime import datetime, timezone
from typing import List, Dict, Any, cast, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Body,
    UploadFile,
    File,
)
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
from core.integrations.supabase.auth import get_current_user
from core.feeds import feed_repo
from core.feeds.collector import collect_feed_articles
from core.integrations.wx import search_Biz
from models import success_response, error_response
from core.common.config import cfg
from core.common.log import logger
from core.common.res import save_avatar_locally
from jobs.article import UpdateArticle
from core.common.utils import TaskQueue


router = APIRouter(prefix=f"/mps", tags=["公众号管理"])


@router.get("/search/{kw}", summary="搜索公众号")
async def search_mp(
    kw: str = "",
    limit: int = 10,
    offset: int = 0,
    _current_user: dict = Depends(get_current_user),
):
    try:
        result = search_Biz(kw, limit=limit, offset=offset)
        data = {
            "list": result.get("list") if result is not None else [],
            "page": {"limit": limit, "offset": offset},
            "total": result.get("total") if result is not None else 0,
        }
        return success_response(data)
    except Exception as e:
        logger.info(f"搜索公众号错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"搜索公众号失败,请重新扫码授权！",
            ),
        )


@router.get("", summary="获取公众号列表")
async def get_mps(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kw: str = Query(""),
    _current_user: dict = Depends(get_current_user),
):
    try:
        filters = {}
        if kw:
            filters["mp_name"] = {"ilike": f"%{kw}%"}

        # 获取总数
        total = await feed_repo.count_feeds(filters=filters)

        # 获取分页数据
        feeds_raw = await feed_repo.get_feeds(
            filters=filters, limit=limit, offset=offset, order_by="created_at"
        )
        feeds: List[Dict[str, Any]] = cast(List[Dict[str, Any]], feeds_raw)

        return success_response(
            {
                "list": [
                    {
                        "id": feed["id"],
                        "mp_name": feed["mp_name"],
                        "mp_cover": feed["mp_cover"],
                        "mp_intro": feed["mp_intro"],
                        "status": feed["status"],
                        "created_at": feed["created_at"],
                    }
                    for feed in feeds
                ],
                "page": {"limit": limit, "offset": offset, "total": total},
                "total": total,
            }
        )
    except Exception as e:
        logger.info(f"获取公众号列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50001, message="获取公众号列表失败"),
        )


@router.get("/update/{mp_id}", summary="更新公众号文章")
async def update_mps(
    mp_id: str,
    start_page: int = 0,
    end_page: int = 1,
    _current_user: dict = Depends(get_current_user),
):
    try:
        # 获取公众号信息
        mp_raw = await feed_repo.get_feed_by_id(mp_id)
        mp: Dict[str, Any] = cast(Dict[str, Any], mp_raw)
        if not mp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="请选择一个公众号"),
            )

        sync_interval = cfg.get("sync_interval", 60)
        if mp.get("update_time") is None:
            mp["update_time"] = int(time.time()) - sync_interval
        time_span = int(time.time()) - int(mp.get("update_time", 0))
        if time_span < sync_interval:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_response(
                    code=40402,
                    message="请不要频繁更新操作",
                    data={"time_span": time_span},
                ),
            )
        def UpArt(mp_data):
            try:
                collect_feed_articles(
                    mp_data,
                    on_article=UpdateArticle,
                    start_page=start_page,
                    max_page=end_page,
                )
            except Exception as e:
                logger.error(f"更新公众号文章线程异常: {e}")

        import threading

        threading.Thread(target=UpArt, args=(mp,)).start()

        return success_response(
            {"time_span": time_span, "list": [], "total": 0, "mps": mp}
        )
    except Exception as e:
        logger.info(f"更新公众号文章: {str(e)}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50001, message=f"更新公众号文章{str(e)}"),
        )


@router.get("/{mp_id}", summary="获取公众号详情")
async def get_mp(
    mp_id: str,
):
    try:
        mp = await feed_repo.get_feed_by_id(mp_id)
        if not mp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="公众号不存在"),
            )
        return success_response(mp)
    except Exception as e:
        logger.info(f"获取公众号详情错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50001, message="获取公众号详情失败"),
        )


@router.post("/by_article", summary="通过文章链接获取公众号详情")
async def get_mp_by_article(
    url: str = Query(..., min_length=1), _current_user: dict = Depends(get_current_user)
):
    try:
        from driver.wx.service import fetch_article
        import asyncio

        # 在后台线程中执行同步的 Playwright 调用，避免在事件循环里直接使用 Sync API
        loop = asyncio.get_running_loop()
        env = await loop.run_in_executor(None, fetch_article, url)

        if not env or not env.get("ok"):
            # 统一错误 envelope：尽量透传 reason，保持原有错误响应风格
            err = (env or {}).get("error") or {}
            msg = err.get("message") or "获取公众号信息失败"
            reason = err.get("reason")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_response(
                    code=50001,
                    message=f"{msg}: {reason}" if reason else msg,
                    data=env,
                ),
            )

        return success_response(env.get("data"))
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f"获取公众号详情错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50001, message=f"获取公众号信息失败: {str(e)}"),
        )


@router.post("", summary="添加公众号")
async def add_mp(
    mp_name: str = Body(..., min_length=1, max_length=255),
    mp_cover: str = Body(None, max_length=255),
    mp_id: str = Body(None, max_length=255),
    avatar: str = Body(None, max_length=500),
    mp_intro: str = Body(None, max_length=255),
    _current_user: dict = Depends(get_current_user),
):
    try:
        import base64

        if not mp_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code=40001, message="缺少公众号ID"),
            )

        try:
            mpx_id = base64.b64decode(mp_id).decode("utf-8")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code=40002, message="无效的公众号ID"),
            )

        cover_path: Optional[str] = None
        if avatar:
            cover_path = save_avatar_locally(avatar)
        elif mp_cover:
            cover_path = mp_cover

        now = datetime.now(timezone.utc)

        # 检查公众号是否已存在（按 faker_id / mp_id）
        existing_feed_raw = await feed_repo.get_feed_by_faker_id(mp_id)
        existing_feed: Dict[str, Any] = cast(Dict[str, Any], existing_feed_raw)

        if existing_feed:
            # 更新现有记录
            update_data: Dict[str, Any] = {
                "mp_name": mp_name,
                "mp_intro": mp_intro,
                "updated_at": now,
            }
            if cover_path:
                update_data["mp_cover"] = cover_path

            await feed_repo.update_feed(existing_feed["id"], update_data)
            feed = {**existing_feed, **update_data}
        else:
            # 创建新的Feed记录
            feed_data: Dict[str, Any] = {
                "id": f"MP_WXS_{mpx_id}",
                "mp_name": mp_name,
                "mp_cover": cover_path,
                "mp_intro": mp_intro,
                "status": 1,  # 默认启用状态
                "created_at": now,
                "updated_at": now,
                "faker_id": mp_id,
                "update_time": 0,
                "sync_time": 0,
            }
            feed = await feed_repo.create_feed(feed_data)

        # 在这里实现第一次添加时获取公众号文章
        if not existing_feed:
            max_page = int(cfg.get("max_page", "2"))
            TaskQueue.add_task(
                collect_feed_articles,
                feed,
                on_article=UpdateArticle,
                max_page=max_page,
            )

        return success_response(
            {
                "id": feed["id"],
                "mp_name": feed["mp_name"],
                "mp_cover": feed.get("mp_cover"),
                "mp_intro": feed.get("mp_intro"),
                "status": feed.get("status"),
                "faker_id": feed.get("faker_id", mp_id),
                "created_at": feed.get("created_at"),
            }
        )
    except HTTPException:
        # 直接透传上面主动抛出的 HTTPException
        raise
    except Exception as e:
        logger.info(f"添加公众号错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50001, message="添加公众号失败"),
        )


@router.delete("/{mp_id}", summary="删除订阅号")
async def delete_mp(
    mp_id: str,
    _current_user: dict = Depends(get_current_user),
):
    try:
        mp = await feed_repo.get_feed_by_id(mp_id)
        if not mp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="订阅号不存在"),
            )

        await feed_repo.delete_feed(mp_id)
        return success_response({"message": "订阅号删除成功", "id": mp_id})
    except Exception as e:
        logger.info(f"删除订阅号错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50001, message="删除订阅号失败"),
        )
