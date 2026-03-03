from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from core.tags import tag_repo
from schemas import success_response, error_response, TagsCreate
from core.integrations.supabase.auth import get_current_user
from core.common.log import logger


router = APIRouter(prefix="/tags", tags=["标签管理"])


def _extract_feed_ids(raw_mps: object) -> list[str]:
    import json

    if raw_mps is None:
        return []
    payload = raw_mps
    if isinstance(raw_mps, str):
        text = raw_mps.strip()
        if not text:
            return []
        try:
            payload = json.loads(text)
        except Exception:
            return []
    if not isinstance(payload, list):
        return []
    ids: list[str] = []
    for item in payload:
        if isinstance(item, dict):
            v = item.get("id") or item.get("mp_id")
            if v:
                ids.append(str(v))
        elif item:
            ids.append(str(item))
    return sorted(set(ids))


def _to_api_tag(tag: dict, feed_ids: list[str] | None = None) -> dict:
    import json

    item = dict(tag or {})
    item["intro"] = item.get("description") or ""
    item["cover"] = item.get("cover") or ""
    item["status"] = item.get("status", 1)
    ids = feed_ids if feed_ids is not None else []
    item["mps_id"] = json.dumps(ids, ensure_ascii=False)
    return item


@router.get("", summary="获取标签列表", description="分页获取所有标签信息")
async def get_tags(
    offset: int = 0,
    limit: int = 100,
    _current_user: dict = Depends(get_current_user),
):
    """获取标签列表"""
    try:
        total = await tag_repo.count_tags()
        tags = await tag_repo.get_tags(limit=limit, offset=offset)
        tag_items = []
        for t in tags:
            tag_id = str((t or {}).get("id") or "")
            feed_ids = await tag_repo.get_feed_ids_by_tag(tag_id) if tag_id else []
            tag_items.append(_to_api_tag(t, feed_ids))
        return success_response(
            data={
                "list": tag_items,
                "page": {"limit": limit, "offset": offset, "total": total},
                "total": total,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=500, message=f"获取标签列表失败: {str(e)}"),
        )


@router.post("", summary="创建新标签", description="创建一个新的标签")
async def create_tag(
    tag: TagsCreate,
    _current_user: dict = Depends(get_current_user),
):
    """创建新标签"""

    try:
        description = tag.intro or None
        if not description:
            description = getattr(tag, "description", None)
        tag_data = {
            "name": tag.name or "",
            "description": description or "",
            "cover": tag.cover or "",
            "status": tag.status if tag.status is not None else 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        new_tag = await tag_repo.create_tag(tag_data)
        tag_id = str((new_tag or {}).get("id") or "")
        feed_ids = _extract_feed_ids(tag.mps_id)
        bound_rows = []
        if tag_id:
            bound_rows = await tag_repo.replace_feed_tags(tag_id, feed_ids)
        data = _to_api_tag(new_tag, feed_ids)
        data["bound_feed_count"] = len(bound_rows)
        return success_response(data=data)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"创建标签失败: {str(e)}",
            ),
        )


@router.get("/{tag_id}", summary="获取单个标签详情", description="根据ID获取标签详情")
async def get_tag(
    tag_id: str,
    _current_user: dict = Depends(get_current_user),
):
    """获取单个标签详情"""
    tag = await tag_repo.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code=404, message="Tag not found"),
        )
    feed_ids = await tag_repo.get_feed_ids_by_tag(tag_id)
    return success_response(data=_to_api_tag(tag, feed_ids))


@router.put(
    "/{tag_id}",
    summary="更新标签信息",
    description="根据ID更新标签信息",
)
async def update_tag(
    tag_id: str,
    tag_data: TagsCreate,
    _current_user: dict = Depends(get_current_user),
):
    """更新标签信息"""
    try:
        existing_tag = await tag_repo.get_tag_by_id(tag_id)
        if not existing_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(code=404, message="Tag not found"),
            )

        description = tag_data.intro or None
        if not description:
            description = getattr(tag_data, "description", None)
        update_data = {
            "name": tag_data.name,
            "description": description or "",
            "cover": tag_data.cover or "",
            "status": tag_data.status if tag_data.status is not None else 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        updated_tags = await tag_repo.update_tag(tag_id, update_data)
        feed_ids = _extract_feed_ids(tag_data.mps_id)
        bound_rows = await tag_repo.replace_feed_tags(tag_id, feed_ids)
        if updated_tags:
            data = _to_api_tag(updated_tags[0], feed_ids)
            data["bound_feed_count"] = len(bound_rows)
            return success_response(data=data)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(code=500, message="更新标签失败"),
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=400, message=str(e)),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=500, message=str(e)),
        )


@router.delete(
    "/{tag_id}",
    summary="删除标签",
    description="根据ID删除标签",
)
async def delete_tag(
    tag_id: str,
    _current_user: dict = Depends(get_current_user),
):
    """删除标签"""
    try:
        existing_tag = await tag_repo.get_tag_by_id(tag_id)
        if not existing_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(code=404, message="Tag not found"),
            )
        await tag_repo.delete_tag(tag_id)
        return success_response(message="Tag deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=500, message=f"删除标签失败: {str(e)}"),
        )
