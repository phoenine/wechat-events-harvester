import os
from typing import List, Dict, Any, cast
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from datetime import datetime
from uuid import uuid4
from core.supabase.storage import SupabaseStorage
from schemas import success_response, error_response
from core.supabase.auth import get_current_user, pwd_context
from core.repositories import user_repo
from core.supabase.storage import supabase_storage_avatar

router = APIRouter(prefix="/user", tags=["用户管理"])

@router.get("", summary="获取用户信息")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    try:
        user_raw = await user_repo.get_user_by_username(current_user["username"])
        user: Dict[str, Any] = cast(Dict[str, Any], user_raw)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="用户不存在"),
            )
        return success_response(
            {
                "username": user["username"],
                "nickname": user.get("nickname") or user["username"],
                "avatar": user.get("avatar") or "",
                "email": user.get("email") or "",
                "role": user["role"],
                "is_active": user["is_active"],
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(code=50001, message="获取用户信息失败"),
        )


@router.get("/list", summary="获取用户列表")
async def get_user_list(
    current_user: dict = Depends(get_current_user),
    page: int = 1,
    page_size: int = 10,
):
    """获取所有用户列表（仅管理员可用）"""
    try:
        # 验证当前用户是否为管理员
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(code=40301, message="无权限执行此操作"),
            )

        # 查询用户总数
        total = await user_repo.count_users()

        # 分页查询用户列表
        offset = (page - 1) * page_size
        users_raw = await user_repo.get_users(limit=page_size, offset=offset)
        users: List[Dict[str, Any]] = cast(List[Dict[str, Any]], users_raw)
        # 格式化返回数据
        user_list = []
        for user in users:
            user_list.append(
                {
                    "username": user["username"],
                    "nickname": user.get("nickname") or user["username"],
                    "avatar": (user.get("avatar") or "/static/default-avatar.png"),
                    "email": user.get("email") or "",
                    "role": user["role"],
                    "is_active": user["is_active"],
                    "created_at": (user.get("created_at") or ""),
                    "updated_at": (user.get("updated_at") or ""),
                }
            )

        return success_response(
            {"total": total, "page": page, "page_size": page_size, "list": user_list}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(code=50002, message=f"获取用户列表失败: {str(e)}"),
        )


@router.post("", summary="添加用户")
async def add_user(
    user_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """添加新用户"""
    try:
        # 验证当前用户是否为管理员
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(code=40301, message="无权限执行此操作"),
            )

        # 验证输入数据
        required_fields = ["username", "password", "email"]
        for field in required_fields:
            if field not in user_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(code=40001, message=f"缺少必填字段: {field}"),
                )

        # 检查用户名是否已存在
        existing_user = await user_repo.get_user_by_username(user_data["username"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(code=40002, message="用户名已存在"),
            )

        # 创建新用户
        user_data = {
            "username": user_data["username"],
            "password_hash": pwd_context.hash(user_data["password"]),
            "email": user_data["email"],
            "role": user_data.get("role", "user"),
            "is_active": user_data.get("is_active", True),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        await user_repo.create_user(user_data)

        return success_response(message="用户添加成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"用户添加失败: {str(e)}"
        )


@router.put("", summary="修改用户资料")
async def update_user_info(
    update_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """修改用户基本信息(不包括密码)"""
    try:
        # 获取目标用户
        target_username = update_data.get("username", current_user["username"])
        user = await user_repo.get_user_by_username(target_username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="用户不存在"),
            )

        # 检查权限：只有管理员或用户自己可以修改信息
        if (
            current_user["role"] != "admin"
            and current_user["username"] != target_username
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(code=40301, message="无权限修改其他用户信息"),
            )

        # 不允许通过此接口修改密码
        if "password" in update_data:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=error_response(code=40002, message="请使用专门的密码修改接口"),
            )

        # 构建更新数据
        update_user_data = {}
        if "is_active" in update_data:
            update_user_data["is_active"] = bool(update_data["is_active"])
        if "email" in update_data:
            update_user_data["email"] = update_data["email"]
        if "role" in update_data and current_user["role"] == "admin":
            update_user_data["role"] = update_data["role"]

        # 更新用户信息
        await user_repo.update_user(target_username, update_user_data)
        return success_response(message="更新成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"更新失败: {str(e)}"
        )


@router.put("/password", summary="修改密码")
async def change_password(
    password_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """修改用户密码"""
    try:
        # 验证请求数据
        if "old_password" not in password_data or "new_password" not in password_data:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=error_response(code=40001, message="需要提供旧密码和新密码"),
            )

        # 获取用户
        user_raw = await user_repo.get_user_by_username(current_user["username"])
        user: Dict[str, Any] = cast(Dict[str, Any], user_raw)
        if not user:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(code=40401, message="用户不存在"),
            )

        # 验证旧密码
        if not pwd_context.verify(password_data["old_password"], user["password_hash"]):

            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=error_response(code=40003, message="旧密码不正确"),
            )

        # 验证新密码复杂度
        new_password = password_data["new_password"]
        if len(new_password) < 8:

            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=error_response(code=40004, message="密码长度不能少于8位"),
            )

        # 更新密码
        update_data = {"password_hash": pwd_context.hash(new_password)}
        await user_repo.update_user(current_user["username"], update_data)

        # 清除用户缓存，确保新密码立即生效
        from core.supabase.auth import clear_user_cache

        clear_user_cache(current_user["username"])
        return success_response(message="密码修改成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"密码修改失败: {str(e)}"
        )


@router.post("/avatar", summary="上传用户头像")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """处理用户头像上传"""
    try:
        file_bytes = await file.read()
        _, ext = os.path.splitext(file.filename or "")
        if not ext:
            ext = ".jpg"
        object_path = supabase_storage_avatar.path.format(
            uuid=str(uuid4()),
            username=current_user["username"],
            filename=file.filename or f"{current_user['username']}{ext}",
        )

        avatar_url = await supabase_storage_avatar.upload_bytes(
            data=file_bytes,
            path=object_path,
            content_type=file.content_type or "image/jpeg",
        )
        await user_repo.update_user_avatar(current_user["username"], avatar_url)
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

#         upload_path = f"{files_dir}/{type}/"
#         # 确保上传目录存在
#         os.makedirs(upload_path, exist_ok=True)

#         # 生成唯一的文件名
#         file_name = f"{current_user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
#         file_path = f"{upload_path}/{file_name}"

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
