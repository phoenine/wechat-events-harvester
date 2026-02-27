from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query, status

from core.common.config import cfg, set_config
from core.integrations.supabase.auth import get_current_user
from schemas import success_response, error_response, ConfigManagementCreate


router = APIRouter(prefix="/configs", tags=["配置管理"])


_NOT_FOUND = object()


def _flatten_config(config: dict, prefix: str = "") -> list[dict]:
    items: list[dict] = []
    for key, value in config.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            items.extend(_flatten_config(value, full_key))
        else:
            items.append(
                {
                    "config_key": full_key,
                    "config_value": str(value) if value is not None else "",
                    "description": "系统配置项",
                }
            )
    return items


def _get_config_value(config_key: str):
    value = cfg.get(config_key, _NOT_FOUND)
    return value


@router.get("", summary="获取配置项列表")
async def list_configs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _current_user: dict = Depends(get_current_user),
):
    """获取配置项列表（YAML单源）"""
    try:
        configs = _flatten_config(cfg.get_config() or {})
        total = len(configs)
        paginated_configs = configs[offset : offset + limit]

        return success_response(
            data={
                "list": paginated_configs,
                "page": {"limit": limit, "offset": offset},
                "total": total,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=500, message=str(e)),
        )


@router.get("/{config_key}", summary="获取单个配置项详情")
async def get_config(
    config_key: str,
    _current_user: dict = Depends(get_current_user),
):
    """获取单个配置项详情（YAML单源）"""
    try:
        value = _get_config_value(config_key)
        if value is _NOT_FOUND:
            raise HTTPException(status_code=404, detail="Config not found")
        return success_response(
            data={
                "config_key": config_key,
                "config_value": str(value) if value is not None else "",
                "description": "系统配置项",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=500, message=str(e)),
        )


@router.post("", summary="创建配置项")
async def create_config(
    config_data: ConfigManagementCreate = Body(...),
    _current_user: dict = Depends(get_current_user),
):
    """创建配置项（写入YAML）"""
    try:
        existing = _get_config_value(config_data.config_key)
        if existing is not _NOT_FOUND:
            raise HTTPException(
                status_code=400, detail="Config with this key already exists"
            )

        set_config(config_data.config_key, config_data.config_value)
        return success_response(
            data={
                "config_key": config_data.config_key,
                "config_value": config_data.config_value,
                "description": config_data.description or "系统配置项",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=500, message=str(e)),
        )


@router.put("/{config_key}", summary="更新配置项")
async def update_config(
    config_key: str = Path(..., min_length=1),
    config_data: ConfigManagementCreate = Body(...),
    _current_user: dict = Depends(get_current_user),
):
    """更新配置项（写入YAML）"""
    try:
        existing = _get_config_value(config_key)
        if existing is _NOT_FOUND:
            raise HTTPException(status_code=404, detail="Config not found")

        set_config(config_key, config_data.config_value)
        return success_response(
            data={
                "config_key": config_key,
                "config_value": config_data.config_value,
                "description": config_data.description or "系统配置项",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=500, message=str(e)),
        )


@router.delete("/{config_key}", summary="删除配置项")
async def delete_config(
    config_key: str,
    _current_user: dict = Depends(get_current_user),
):
    """删除配置项（YAML单源下暂不支持删除）"""
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=error_response(
            code=40501,
            message="YAML单源模式下暂不支持删除配置项",
        ),
    )
