import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, cast

from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException,
    Request,
    Response,
    status,
)

from core.repositories import feed_repo, tag_repo, article_repo
from core.rss import RSS
from schemas import error_response
from core.supabase.auth import get_current_user
from core.config import cfg
from core.print import print_error



router = APIRouter(prefix="/rss", tags=["Rss"])
feed_router = APIRouter(prefix="/feed", tags=["Feed"])

def verify_rss_access(current_user: dict = Depends(get_current_user)):
    """RSS访问认证方法"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(code=40101, message="未授权的RSS访问"),
        )
    return current_user

@router.get("/{feed_id}/api", summary="获取特定RSS源详情")
async def get_rss_source(
    feed_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await get_mp_articles_source(
        request=request,
        feed_id=feed_id,
        limit=limit,
        offset=offset,
        is_update=True,
    )

@router.get("", summary="获取RSS订阅列表")
async def get_rss_feeds(
    request: Request,
    limit: int = Query(10, ge=1, le=30),
    offset: int = Query(0, ge=0),
    is_update: bool = False,
):
    rss = RSS(name=f"all_{limit}_{offset}")
    rss_xml = rss.get_cache()
    if rss_xml is not None and is_update == False:
        return Response(content=rss_xml, media_type="application/xml")

    try:
        feeds_raw = await feed_repo.get_feeds(limit=limit, offset=offset)
        feeds: List[Dict[str, Any]] = cast(List[Dict[str, Any]], feeds_raw)
        rss_domain = cfg.get("rss.base_url", str(request.base_url))

        rss_list = [
            {
                "id": str(feed.get("id")),
                "title": feed.get("mp_name"),
                "link": f"{rss_domain}rss/{feed.get('id')}",
                "description": feed.get("mp_intro"),
                "image": feed.get("mp_cover"),
                "updated": (feed.get("created_at")),
            }
            for feed in feeds
        ]

        # 生成RSS XML
        # TODO: 这里的类型注解需要修正
        rss_xml = rss.generate_rss(rss_list, title="WeRSS订阅", link=rss_domain)

        return Response(content=rss_xml, media_type="application/xml")
    except Exception as e:
        print_error(f"获取RSS订阅列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message="获取RSS订阅列表失败"),
        )

@router.get("/fresh", summary="更新并获取RSS订阅列表")
async def update_rss_feeds(
    request: Request,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await get_rss_feeds(
        request=request,
        limit=limit,
        offset=offset,
        is_update=True,
    )

@router.get("/content/{content_id}", summary="获取缓存的文章内容")
async def get_rss_feed(content_id: str):
    rss = RSS()
    content = rss.get_cached_content(content_id)

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code=40402, message="文章内容未找到"),
        )
    title = content["title"]
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <title>{title}</title>
        </head>
    <body>
    <center>
    <h1 style="text-align:center;">{title}</h1>
    <div class="author">来源:{source}</div>
    <div class="author">发布时间:{publish_time}</div>
    <div class="copyright">
        <p>
        本文章仅用于学习和交流目的，不代表本网站观点和立场，如涉及版权问题，请及时联系我们删除。
        </p>
    </div>
    <div id=content>{text}</div>
    </center>
    </body>
    </html>
    """
    text = rss.add_logo_prefix_to_urls(content["content"])
    html = html.format(
        title=title,
        text=text,
        source=content["mp_name"],
        publish_time=content["publish_time"],
    )
    return Response(content=html, media_type="text/html")



@router.api_route("/{feed_id}/fresh", summary="更新并获取公众号文章RSS")
async def update_mp_rss_feed(
    request: Request,
    feed_id: str,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # TODO: 实现文章抓取逻辑

    return await get_mp_articles_source(
        request=request,
        feed_id=feed_id,
        limit=limit,
        offset=offset,
        is_update=True,
    )


@router.get("/{feed_id}", summary="获取公众号文章")
async def get_mp_articles_source(
    request: Request,
    feed_id: Optional[str] = None,
    tag_id: Optional[str] = None,
    ext: str = "xml",
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kw: str = "",
    is_update: bool = True,
    content_type: Optional[str] = Query(None, alias="ctype"),
    template: Optional[str] = None,
):
    rss = RSS(name=f"{tag_id}_{feed_id}_{limit}_{offset}", ext=ext)
    rss.set_content_type(content_type)
    rss_xml = rss.get_cache()
    if rss_xml is not None and is_update == False:
        return Response(content=rss_xml, media_type=rss.get_type())

    try:
        rss_domain = cfg.get("rss.base_url", str(request.base_url))

        # 获取公众号信息
        if feed_id not in ["all", None]:
            feed = await feed_repo.get_feed_by_id(feed_id)
            if not feed:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_response(code=40401, message="公众号不存在"),
                )
            mp_ids = [feed_id]
        else:
            # 默认feed信息
            feed = {
                "mp_name": cfg.get("rss.title", "WeRss") or "WeRss",
                "mp_intro": cfg.get("rss.description") or "WeRss高效订阅我的公众号",
                "mp_cover": cfg.get("rss.cover") or f"{rss_domain}static/logo.svg",
            }
            mp_ids = None

            # 如果传入了tag_id就加载tag对应的订阅信息
            if tag_id is not None:
                tag = await tag_repo.get_tag_by_id(tag_id)
                if tag:
                    mps_ids = (
                        json.loads(tag.get("mps_id", "[]")) if tag.get("mps_id") else []
                    )
                    mp_ids = [str(mp["id"]) for mp in mps_ids] if mps_ids else []
                    feed["mp_name"] = tag.get("name", "")
                    feed["mp_intro"] = tag.get("intro", "")
                    feed["mp_cover"] = f"{rss_domain}{tag.get('cover', '')}"

        # 获取文章列表
        if mp_ids:
            articles_raw = await article_repo.get_articles_by_mp_ids(
                mp_ids, limit=limit, offset=offset
            )
        else:
            articles_raw = await article_repo.get_articles(limit=limit, offset=offset)

        articles: List[Dict[str, Any]] = cast(List[Dict[str, Any]], articles_raw)

        # 如果有搜索关键词，进行过滤
        if kw:
            articles = [
                article
                for article in articles
                if kw.lower() in (article.get("title") or "").lower()
            ]

        # 获取对应的公众号信息
        feed_map = {}
        if articles:
            mp_ids = list(
                set(
                    article.get("mp_id") for article in articles if article.get("mp_id")
                )
            )
            if mp_ids:
                feeds_raw = await feed_repo.get_feeds_by_ids(mp_ids)
                feeds: List[Dict[str, Any]] = cast(List[Dict[str, Any]], feeds_raw)
                feed_map = {feed["id"]: feed for feed in feeds}

        # 转换为RSS格式数据
        cst = timezone(timedelta(hours=8))
        rss_list = []
        for article in articles:
            mp_feed = feed_map.get(article.get("mp_id"), feed)

            rss_item = {
                "id": str(article.get("id")),
                "title": article.get("title") or "",
                "link": (
                    f"{rss_domain}rss/feed/{article.get('id')}"
                    if cfg.get("rss.local", False)
                    else article.get("url", "")
                ),
                "description": (
                    article.get("description", "")
                    if article.get("description") != ""
                    else article.get("title") or ""
                ),
                "content": article.get("content") or "",
                "image": article.get("pic_url") or "",
                "mp_name": mp_feed.get("mp_name") or "",
                "updated": (
                    datetime.fromtimestamp(article.get("publish_time", 0), tz=cst)
                    if article.get("publish_time")
                    else datetime.now(tz=cst)
                ),
                "feed": {
                    "id": mp_feed.get("id"),
                    "name": mp_feed.get("mp_name"),
                    "cover": mp_feed.get("mp_cover"),
                    "intro": mp_feed.get("mp_intro"),
                },
            }
            rss_list.append(rss_item)

        # 缓存文章内容
        for article in articles:
            mp_feed = feed_map.get(article.get("mp_id"), feed)
            content_data = {
                "id": article.get("id"),
                "title": article.get("title"),
                "content": article.get("content"),
                "content_md": article.get("content_md"),
                "publish_time": article.get("publish_time"),
                "mp_id": article.get("mp_id"),
                "pic_url": article.get("pic_url"),
                "mp_name": mp_feed.get("mp_name"),
            }
            rss.cache_content(article.get("id"), content_data)

        # 生成RSS XML
        rss_xml = rss.generate(
            rss_list,
            ext=ext,
            title=f"{feed.get('mp_name')}",
            link=rss_domain,
            description=feed.get("mp_intro"),
            image_url=feed.get("mp_cover"),
            template=template,
        )

        return Response(content=rss_xml, media_type=rss.get_type())
    except Exception as e:
        print_error(f"获取RSS错误:{e}")
        # 如果已有缓存内容，则退回使用缓存内容
        cached_xml = rss.get_cache()
        if cached_xml:
            return Response(content=cached_xml, media_type=rss.get_type())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50001, message="获取RSS失败"),
        )


@feed_router.get("/{feed_id}.{ext}", summary="获取公众号文章源")
async def rss_feed(
    request: Request,
    feed_id: str,
    ext: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kw: str = "",
    content_type: Optional[str] = Query(None, alias="ctype"),
    is_update: bool = True,
):
    return await get_mp_articles_source(
        request=request,
        feed_id=feed_id,
        limit=limit,
        offset=offset,
        is_update=is_update,
        ext=ext,
        kw=kw,
        content_type=content_type,
    )


@feed_router.get("/search/{kw}/{feed_id}.{ext}", summary="获取公众号文章源")
async def rss_search(
    request: Request,
    feed_id: str,
    ext: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kw: str = "",
    content_type: Optional[str] = Query(None, alias="ctype"),
    is_update: bool = True,
):
    return await get_mp_articles_source(
        request=request,
        feed_id=feed_id,
        limit=limit,
        offset=offset,
        is_update=is_update,
        ext=ext,
        kw=kw,
        content_type=content_type,
    )


@feed_router.get("/tag/{tag_id}.{ext}", summary="获取公众号文章源")
async def rss_by_tag(
    request: Request,
    tag_id: str = "",
    feed_id: Optional[str] = None,
    ext: str = "jmd",
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    kw: str = "",
    content_type: Optional[str] = Query(None, alias="ctype"),
    is_update: bool = True,
):
    return await get_mp_articles_source(
        request=request,
        feed_id=feed_id,
        tag_id=tag_id,
        limit=limit,
        offset=offset,
        is_update=is_update,
        ext=ext,
        kw=kw,
        content_type=content_type,
    )
