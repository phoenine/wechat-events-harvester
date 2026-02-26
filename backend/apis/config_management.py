from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query, status
from core.config_management import config_repo
from core.integrations.supabase.auth import get_current_user
from models import success_response, error_response, ConfigManagementCreate


router = APIRouter(prefix="/configs", tags=["配置管理"])

@router.get("", summary="获取配置项列表")
async def list_configs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _current_user: dict = Depends(get_current_user),
):
    """获取配置项列表"""
    try:
        # 从数据库获取配置项
        configs = await config_repo.get_configs()
        total = len(configs)

        # 分页处理
        paginated_configs = configs[offset : offset + limit]

        return success_response(
            data={
                "list": paginated_configs,
                "page": {"limit": limit, "offset": offset},
                "total": total,
            }
        )
    except HTTPException:
        raise
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
    """获取单个配置项详情"""
    try:
        config = await config_repo.get_config_by_key(config_key)
        if not config:
            raise HTTPException(status_code=404, detail="Config not found")
        return success_response(data=config)
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
    """创建配置项"""
    try:
        existing_config = await config_repo.get_config_by_key(config_data.config_key)
        if existing_config:
            raise HTTPException(
                status_code=400, detail="Config with this key already exists"
            )

        config_data_dict = {
            "config_key": config_data.config_key,
            "config_value": config_data.config_value,
            "description": config_data.description,
        }

        new_config = await config_repo.set_config(
            config_data.config_key,
            config_data.config_value,
            config_data.description or "",
        )
        return success_response(data=new_config)
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
    """更新配置项"""
    try:
        existing_config = await config_repo.get_config_by_key(config_key)
        if not existing_config:
            raise HTTPException(status_code=404, detail="Config not found")

        # 更新配置项
        updated_config = await config_repo.set_config(
            config_key, config_data.config_value, config_data.description or ""
        )
        return success_response(data=updated_config)
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
    """删除配置项"""
    try:
        # 检查配置项是否存在
        existing_config = await config_repo.get_config_by_key(config_key)
        if not existing_config:
            raise HTTPException(status_code=404, detail="Config not found")

        # 删除配置项
        await config_repo.delete_config(config_key)
        return success_response(message="Config deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=500, message=str(e)),
        )
