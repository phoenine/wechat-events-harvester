import os
import re
from typing import Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from schemas import success_response, error_response
from core.integrations.supabase.auth import get_current_user
from core.profiles import profile_repo
from core.integrations.supabase.storage import supabase_storage_avatar
from core.common.runtime_settings import runtime_settings


router = APIRouter(prefix="/user", tags=["用户资料"])


def _render_storage_path(template: str, values: dict[str, str]) -> str:
    """渲染 storage 路径模板，避免因占位符不一致导致 KeyError。"""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in values:
            return str(values[key])
        return str(values.get("uuid", uuid4().hex))

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", replace, template)


@router.get("", summary="获取当前用户资料")
async def get_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_response(code=40101, message="未登录或会话已失效"),
            )

        # 从 profiles 仓储中获取扩展信息（允许不存在）
        profile = await profile_repo.get_profile_by_user_id(user_id)
        profile = profile or {}

        # 基础信息来自 Supabase Auth
        email = current_user.get("email") or ""
        metadata = current_user.get("user_metadata") or {}
        role = metadata.get("role", "user")

        return success_response(
            {
                "id": user_id,
                "email": email,
                "username": metadata.get("username") or email,
                "nickname": profile.get("nickname")
                or metadata.get("nickname")
                or email,
                "avatar": profile.get("avatar_url") or "",
                "role": role,
                "is_active": True,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50001, message=f"获取用户信息失败: {str(e)}"),
        )


@router.post("/avatar", summary="上传用户头像")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """处理用户头像上传"""
    try:
        allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=error_response(code=41501, message="不支持的头像类型"),
            )

        # 默认限制 5MB，可通过配置 avatar.max_bytes 覆盖
        max_bytes = await runtime_settings.get_int("avatar.max_bytes", 5 * 1024 * 1024)
        file_bytes = bytearray()
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            file_bytes.extend(chunk)
            if len(file_bytes) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=error_response(code=41301, message="头像文件过大"),
                )
        _, ext = os.path.splitext(file.filename or "")
        if not ext:
            ext = ".jpg"
        user_id = str(current_user.get("id") or "")
        username = str(current_user.get("username") or user_id or "user")
        object_path = _render_storage_path(
            supabase_storage_avatar.path,
            {
                "uuid": str(uuid4()),
                "user_id": user_id,
                "username": username,
                "filename": file.filename or f"{username}{ext}",
            },
        )

        avatar_url = await supabase_storage_avatar.upload_bytes(
            data=bytes(file_bytes),
            path=object_path,
            content_type=file.content_type or "image/jpeg",
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_response(code=40101, message="未登录或会话已失效"),
            )

        await profile_repo.update_avatar(user_id, avatar_url)
        return success_response(data={"avatar": avatar_url})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"头像上传失败: {str(e)}",
        )


# TODO: 本地文件上传接口，暂时弃用
# @router.post("/upload", summary="上传文件")
# async def upload_file(
#     file: UploadFile = File(...),
#     type: str = "tags",
#     current_user: dict = Depends(get_current_user),
# ):
#     """处理用户文件上传"""
#     try:
#         # 验证 type 参数的安全性
#         if not type.isalnum() or type in ["", ".."]:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=error_response(code=40003, message="无效的文件类型"),
#             )
#         file_url_path = f"files/{type}/"
#         from core.res.avatar import files_dir
#
#         upload_path = f"{files_dir}/{type}/"
#         # 确保上传目录存在
#         os.makedirs(upload_path, exist_ok=True)
#
#         # 生成唯一的文件名
#         file_name = f"{current_user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
#         file_path = f"{upload_path}/{file_name}"
#
#         # 保存文件
#         with open(file_path, "wb") as buffer:
#             buffer.write(await file.read())
#         return success_response(data={"url": f"/{file_url_path}/{file_name}"})
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"文件上传失败: {str(e)}"
#         )
