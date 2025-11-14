import os
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Body,
    status as fast_status,
)
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import and_
from core.auth import get_current_user
from core.db import DB
from core.models.article import Article
from core.models.events import Events
from .base import success_response, error_response
from core.models.base import DATA_STATUS
from schemas.events import EventCreate, EventUpdate
import re
import json
import requests
from typing import Tuple
from core.log import logger


# FastAPI/Pydantic v1/v2 compatibility for regex/pattern
def QueryPattern(default: str, pat: str):
    try:
        return Query(default, pattern=pat)  # Pydantic v2
    except TypeError:
        return Query(default, regex=pat)  # Pydantic v1


router = APIRouter(prefix="/events", tags=["活动"])


def _get_date_range(scope: str):
    now = datetime.now()
    start_of_day = datetime(now.year, now.month, now.day)
    if scope in ("today", "day"):
        return start_of_day, start_of_day + timedelta(days=1)
    elif scope == "week":
        start_of_week = start_of_day - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        return start_of_week, end_of_week
    else:
        return None, None


def _analyze_article_by_llm(
    title: str, content: Optional[str], default_url: Optional[str]
) -> Dict[str, Any]:
    api_base = os.getenv(
        "LLM_API_BASE", "https://api.siliconflow.cn/v1/chat/completions"
    )
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "Qwen/Qwen3-32B")

    full_text = f"标题：{title or ''}\n正文: {content or ''}".strip()

    # 入口调试信息
    logger.debug(
        "[events.llm] input "
        f"title_len={len(title or '')}, content_len={len(content or '')}, "
        f"default_url_present={bool(default_url)}"
    )
    logger.info(
        "[events.llm] setup "
        f"api_base={api_base}, model={model}, key_present={bool(api_key)}"
    )

    # 若未配置密钥，回退为启发式逻辑（保证功能可运行）
    if not api_key:
        logger.warning("[events.llm] LLM_API_KEY missing, using heuristic fallback")
        logger.debug(f"[events.llm] heuristic_text_sample={full_text[:200]!r}")
        is_event = any(
            k in full_text
            for k in [
                "活动",
                "讲座",
                "分享会",
                "沙龙",
                "大会",
                "培训",
                "路演",
                "赛",
                "招募",
                "报名",
            ]
        )
        if not is_event:
            logger.info("[events.llm] heuristic says not an event")
            return {"is_event": False}
        ret = {
            "is_event": True,
            "registration_time": "即时",
            "registration_method": default_url,
            "event_time": "未知",
            "event_fee": "未知",
            "audience": "未知",
            # 仅保留报名信息抬头，article_url不再从LLM拿
            "registration_title": "无",
        }
        logger.debug(f"[events.llm] heuristic_result={ret}")
        return ret

    prompt = (
        "你是一名结构化信息抽取助手。请根据以下微信公众号文章的标题与正文，"
        "判断该文章是否与【线上或线下活动】相关（例如讲座、培训、沙龙、招募、比赛、展览、分享会等）。"
        '如果不是活动，请输出：{"is_event": false}。\n\n'
        "如果是活动，请严格按照以下字段定义提取并返回 JSON 对象（不要包含额外说明或文字）：\n\n"
        "字段定义：\n"
        "1. is_event（布尔）— 是否为活动类文章。\n"
        "2. registration_title（字符串）— 活动的标题或主题。如果文章中有明确活动名或标题，请提取并总结为20字以内。\n"
        "3. registration_time（字符串）— 报名时间；若未提及，填“即刻报名”。\n"
        "4. registration_method（字符串）— 报名方式（例如链接、二维码、公众号回复等）；若未提及，填“参考公众号文章内容”。\n"
        "5. event_time（字符串）— 活动举行的具体时间；若未提及，填“未知”。\n"
        "6. event_fee（字符串）— 活动费用说明，如“免费”“99元/人”；若未提及，填“未知”。\n"
        "7. audience（字符串）— 目标参与人群，例如“亲子”“青少年”“公众”“高校学生”；若未提及，填“未知”。\n\n"
        "注意：请仅输出一个合法的 JSON 对象，不要添加任何自然语言解释或多余文字。\n\n"
        f"以下为文章内容：\n标题：{title or ''}\n正文：{content or ''}\n\n"
        "请开始输出。"
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        # "stream": False,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        payload_size = len(json.dumps(payload, ensure_ascii=False))
    except Exception:
        payload_size = -1
    logger.debug(
        "[events.llm] request "
        f"payload_size={payload_size}, prompt_len={len(prompt)}, timeout=30"
    )

    try:
        resp = requests.post(api_base, headers=headers, json=payload, timeout=600)
        logger.debug(
            "[events.llm] response "
            f"status={resp.status_code}, elapsed={getattr(resp, 'elapsed', None)}"
        )
        resp.raise_for_status()

        # 尝试解析 JSON
        data = resp.json()
        logger.debug(f"[events.llm] resp_json_keys={list(data.keys())}")

        content_text = (data.get("choices", [{}])[0].get("message", {}) or {}).get(
            "content", ""
        )
        logger.debug(f"[events.llm] raw_content_sample={content_text[:300]!r}")

        # 兼容模型可能返回包裹文本，从中提取JSON
        m = re.search(r"\{.*\}", content_text, re.S)
        json_str = m.group(0) if m else content_text
        logger.debug(f"[events.llm] extracted_json_sample={json_str[:300]!r}")

        result = json.loads(json_str)
        logger.debug(f"[events.llm] parsed_result_keys={list(result.keys())}")

        # 兜底与类型修正
        is_event_raw = result.get("is_event", False)
        if isinstance(is_event_raw, str):
            is_event = is_event_raw.strip().lower() in [
                "true",
                "yes",
                "是",
                "活动",
                "y",
            ]
        else:
            is_event = bool(is_event_raw)

        logger.info(f"[events.llm] is_event={is_event}")
        if not is_event:
            return {"is_event": False}

        registration_time = result.get("registration_time") or "即时"
        registration_method = result.get("registration_method") or (default_url or "无")
        event_time = result.get("event_time") or "无"
        event_fee = result.get("event_fee") or "无"
        audience = result.get("audience") or "无"
        registration_title = result.get("registration_title") or "无"

        ret = {
            "is_event": True,
            "registration_time": registration_time,
            "registration_method": registration_method,
            "event_time": event_time,
            "event_fee": event_fee,
            "audience": audience,
            "registration_title": registration_title,
            # "article_url" intentionally omitted here; will be set from article.url in upsert
        }
        logger.debug(f"[events.llm] normalized_result={ret}")
        return ret

    except requests.HTTPError as e:
        body = None
        try:
            body = resp.text[:500]
        except Exception:
            pass
        logger.exception(f"[events.llm] HTTPError: {e}; body_sample={body!r}")
    except Exception as e:
        logger.exception(f"[events.llm] analyze failed: {e}")

    # 调用失败时回退为保守策略，避免中断
    is_event = any(
        k in full_text
        for k in [
            "活动",
            "讲座",
            "分享会",
            "沙龙",
            "大会",
            "培训",
            "路演",
            "赛",
            "招募",
            "报名",
        ]
    )
    if not is_event:
        logger.info("[events.llm] fallback says not an event")
        return {"is_event": False}
    ret = {
        "is_event": True,
        "registration_time": "即时",
        "registration_method": default_url or "无",
        "event_time": "无",
        "event_fee": "无",
        "audience": "无",
        "registration_title": "无",
    }
    logger.debug(f"[events.llm] fallback_result={ret}")
    return ret


def _upsert_event(
    session, article: Article, analysis: Dict[str, Any]
) -> Tuple[Events, bool]:
    """
    以 article_id 作为唯一目标，存在则更新，不存在则创建；返回 (event, created_flag)。
    """
    existing = session.query(Events).filter(Events.article_id == article.id).first()
    now = datetime.now()
    if existing:
        logger.info(f"[events.upsert] update article_id={article.id}")
        existing.registration_time = analysis.get("registration_time", "即时")
        existing.registration_method = analysis.get(
            "registration_method", article.url or "无"
        )
        existing.event_time = analysis.get("event_time", "无")
        existing.event_fee = analysis.get("event_fee", "无")
        existing.audience = analysis.get("audience", "无")
        # 新增字段
        existing.registration_title = analysis.get("registration_title", "无")
        # 强制使用文章库URL
        existing.article_url = article.url or "无"
        existing.updated_at = now

        logger.debug(
            "[events.upsert] update fields "
            f"registration_time={existing.registration_time!r}, "
            f"registration_method={existing.registration_method!r}, "
            f"event_time={existing.event_time!r}, "
            f"event_fee={existing.event_fee!r}, "
            f"audience={existing.audience!r}, "
            f"updated_at={existing.updated_at}"
        )
        return existing, False
    else:
        logger.info(f"[events.upsert] create article_id={article.id}")
        evt = Events(
            article_id=article.id,
            registration_time=analysis.get("registration_time", "即时"),
            registration_method=analysis.get(
                "registration_method", article.url or "无"
            ),
            event_time=analysis.get("event_time", "无"),
            event_fee=analysis.get("event_fee", "无"),
            audience=analysis.get("audience", "无"),
            # 新增字段
            registration_title=analysis.get("registration_title", "无"),
            # 强制使用文章库URL
            article_url=article.url or "无",
            created_at=now,
            updated_at=now,
        )
        session.add(evt)

        logger.debug(
            "[events.upsert] create fields "
            f"registration_time={evt.registration_time!r}, "
            f"registration_method={evt.registration_method!r}, "
            f"event_time={evt.event_time!r}, "
            f"event_fee={evt.event_fee!r}, "
            f"audience={evt.audience!r}, "
            f"created_at={evt.created_at}, updated_at={evt.updated_at}"
        )
        return evt, True


@router.post("/fetch", summary="活动fetch（按日期筛选文章并分析生成events）")
def fetch_events(
    scope: str = QueryPattern("today", "^(today|day|week|all)$"),
    limit: int = Query(200, ge=1, le=200),
    payload: Optional[Dict[str, Any]] = Body(None),
    current_user: dict = Depends(get_current_user),
):
    session = DB.get_session()
    # Normalize scope/limit from JSON body if provided (supports {"scope":"week","limit":100})
    if payload:
        body_scope = (payload.get("scope") or "").strip().lower()
        if body_scope in {"today", "day", "week", "all"}:
            scope = "today" if body_scope == "day" else body_scope
        body_limit = payload.get("limit")
        try:
            if isinstance(body_limit, int) and 1 <= body_limit <= 200:
                limit = body_limit
        except Exception:
            pass
    try:
        logger.info(f"[events.fetch] scope={scope}, limit={limit}")
        start, end = _get_date_range(scope)
        if start and end:
            logger.info(
                f"[events.fetch] date_range: {start.isoformat()} ~ {end.isoformat()}"
            )

        q = session.query(Article).filter(Article.status != DATA_STATUS.DELETED)
        if start and end:
            q = q.filter(and_(Article.publish_at >= start, Article.publish_at < end))
        q = q.order_by(Article.publish_at.desc()).limit(limit)

        articles = q.all()
        logger.info(f"[events.fetch] scanned_articles={len(articles)}")

        existing_ids = {row[0] for row in session.query(Events.article_id).all()}
        logger.info(f"[events.fetch] existing_events={len(existing_ids)}")

        created, updated = [], []
        for art in articles:
            if art.id in existing_ids:
                logger.info(f"[events.fetch] skip existing article_id={art.id}")
                continue
            logger.debug(
                "[events.fetch] article "
                f"id={art.id}, title={ (art.title or '')[:50]!r }, "
                f"publish_time={getattr(art, 'publish_time', None)}, "
                f"publish_at={getattr(art, 'publish_at', None)}, "
                f"url={getattr(art, 'url', None)}"
            )

            analysis = _analyze_article_by_llm(
                art.title, getattr(art, "content", None), art.url
            )
            logger.debug(f"[events.fetch] analysis article_id={art.id} -> {analysis}")

            if not analysis.get("is_event", False):
                logger.info(f"[events.fetch] skip non-event article_id={art.id}")
                continue

            evt, created_flag = _upsert_event(session, art, analysis)
            if created_flag:
                created.append(evt.article_id)
            else:
                updated.append(evt.article_id)

        session.commit()
        logger.info(
            f"[events.fetch] result created={len(created)}, updated={len(updated)}"
        )
        return success_response(
            data={
                "scope": scope,
                "scanned": len(articles),
                "created_count": len(created),
                "updated_count": len(updated),
                "created_article_ids": created,
                "updated_article_ids": updated,
            }
        )
    except Exception as e:
        session.rollback()
        logger.exception(f"[events.fetch] failed: {e}")
        raise HTTPException(
            status_code=fast_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50001, message=f"活动fetch失败: {str(e)}"),
        )
    finally:
        session.close()


@router.post("", summary="创建活动记录")
def create_event(
    payload: EventCreate = Body(...),
    current_user: dict = Depends(get_current_user),
):
    session = DB.get_session()
    try:
        now = datetime.now()
        created_at = payload.created_at or now
        updated_at = payload.updated_at or now

        # 统一从文章库获取URL
        art = session.query(Article).filter(Article.id == payload.article_id).first()
        if not art:
            raise HTTPException(
                status_code=fast_status.HTTP_400_BAD_REQUEST,
                detail=error_response(code=40011, message="关联文章不存在"),
            )

        evt = Events(
            article_id=payload.article_id,
            registration_time=payload.registration_time or "即时",
            registration_method=payload.registration_method or (art.url or "无"),
            event_time=payload.event_time or "无",
            event_fee=payload.event_fee or "无",
            audience=payload.audience or "无",
            registration_title=payload.registration_title or "无",
            # 强制使用文章库URL
            article_url=art.url or "无",
            created_at=created_at,
            updated_at=updated_at,
        )
        session.add(evt)
        session.commit()
        session.refresh(evt)
        return success_response(evt)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=fast_status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=40001, message=f"创建失败: {str(e)}"),
        )
    finally:
        session.close()


@router.get("", summary="查询活动记录列表")
def list_events(
    article_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    session = DB.get_session()
    try:
        q = session.query(Events)
        if article_id:
            q = q.filter(Events.article_id == article_id)
        items = q.order_by(Events.updated_at.desc()).offset(offset).limit(limit).all()
        return success_response(items)
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=40002, message=f"查询失败: {str(e)}"),
        )
    finally:
        session.close()


@router.get("/{event_id}", summary="获取活动记录详情")
def get_event(event_id: int, current_user: dict = Depends(get_current_user)):
    session = DB.get_session()
    try:
        evt = session.query(Events).filter(Events.id == event_id).first()
        if not evt:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="活动记录不存在"),
            )
        return success_response(evt)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=40003, message=f"获取失败: {str(e)}"),
        )
    finally:
        session.close()


@router.put("/{event_id}", summary="更新活动记录")
def update_event(
    event_id: int,
    payload: EventUpdate = Body(...),
    current_user: dict = Depends(get_current_user),
):
    session = DB.get_session()
    try:
        evt = session.query(Events).filter(Events.id == event_id).first()
        if not evt:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="活动记录不存在"),
            )
        now = datetime.now()
        if payload.registration_time is not None:
            evt.registration_time = payload.registration_time
        if payload.registration_method is not None:
            evt.registration_method = payload.registration_method
        if payload.event_time is not None:
            evt.event_time = payload.event_time
        if payload.event_fee is not None:
            evt.event_fee = payload.event_fee
        if payload.audience is not None:
            evt.audience = payload.audience
        if payload.registration_title is not None:
            evt.registration_title = payload.registration_title

        # 每次更新都从文章库刷新一次URL（保证一致性）
        art = session.query(Article).filter(Article.id == evt.article_id).first()
        evt.article_url = (art.url if art else None) or "无"

        # 时间字段更新（允许覆盖created_at；若未提供updated_at则写当前时间）
        if payload.created_at is not None:
            evt.created_at = payload.created_at
        evt.updated_at = payload.updated_at or now

        session.commit()
        session.refresh(evt)
        return success_response(evt)
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=fast_status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=40004, message=f"更新失败: {str(e)}"),
        )
    finally:
        session.close()


@router.delete("/{event_id}", summary="删除活动记录")
def delete_event(event_id: int, current_user: dict = Depends(get_current_user)):
    session = DB.get_session()
    try:
        evt = session.query(Events).filter(Events.id == event_id).first()
        if not evt:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="活动记录不存在"),
            )
        session.delete(evt)
        session.commit()
        return success_response({"deleted_id": event_id})
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=fast_status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=40005, message=f"删除失败: {str(e)}"),
        )
    finally:
        session.close()
