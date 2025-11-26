from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from schemas import success_response, error_response
from core.config import set_config, cfg
from core.supabase.auth import (
    get_current_user,
    authenticate_user_credentials,
    UserCredentials,
)
from core.supabase.storage import SupabaseStorage
from core.supabase.database import db_manager
from driver.base import WX_API
from driver.success import Success


router = APIRouter(prefix=f"/auth", tags=["认证"])


def ApiSuccess(data):
    if data != None:
        print("\n登录结果:")
        print(f"Token: {data['token']}")
        set_config("token", data["token"])
        cfg.reload()
    else:
        print("\n登录失败, 请检查上述错误信息")


@router.get("/qr/code", summary="获取登录二维码")
async def get_qrcode(_current_user=Depends(get_current_user)):
    session_id = None
    if db_manager.valid_session_db():
        user_id = _current_user.get("supabase_user_id") or None
        session_id = await db_manager.create_session(user_id=user_id, expires_minutes=2)
        setattr(WX_API, "current_session_id", session_id)
    code_url = WX_API.GetCode(Success)
    if session_id:
        code_url.update({"session_id": session_id})
    return success_response(code_url)


@router.get("/qr/image", summary="获取登录二维码图片")
async def qr_image(_current_user=Depends(get_current_user)):
    return success_response(WX_API.GetHasCode())


@router.get("/qr/url", summary="获取二维码完整访问地址")
async def qr_url(_current_user=Depends(get_current_user)):
    sb = SupabaseStorage()
    if not WX_API.GetHasCode():
        return success_response(
            {"image_url": None, "mode": "supabase" if sb.valid() else "local"}
        )
    url = getattr(WX_API, "wx_login_url", None)
    if (
        url
        and getattr(WX_API, "current_session_id", None)
        and db_manager.valid_session_db()
    ):
        try:
            await db_manager.update_session(
                getattr(WX_API, "current_session_id"),
                status="waiting",
                qr_signed_url=url,
                expires_minutes=2,
            )
        except Exception:
            pass
    return success_response(
        {"image_url": url, "mode": "supabase" if sb.valid() else "local"}
    )


@router.get("/qr/status", summary="获取扫描状态")
async def qr_status(_current_user=Depends(get_current_user)):
    return success_response(
        {
            "login_status": WX_API.HasLogin(),
        }
    )


@router.get("/qr/over", summary="扫码完成")
async def qr_success(_current_user=Depends(get_current_user)):
    return success_response(WX_API.Close())


@router.post("/login", summary="用户登录")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # 使用Supabase认证
        credentials = UserCredentials(
            username=form_data.username, password=form_data.password
        )

        auth_result = await authenticate_user_credentials(credentials)

        # authenticate_user_credentials 现已返回 TokenResponse 对象
        return success_response(auth_result.dict())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(code=40101, message=f"登录失败: {str(e)}"),
        )


@router.post("/token", summary="获取Token")
async def getToken(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # 使用Supabase认证
        credentials = UserCredentials(
            username=form_data.username, password=form_data.password
        )
        auth_result = await authenticate_user_credentials(credentials)
        return auth_result.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=error_response(code=40101, message=f"认证失败: {str(e)}"),
        )


@router.post("/logout", summary="用户注销")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"code": 0, "message": "注销成功"}


@router.post("/refresh", summary="刷新Token")
async def refresh_token(_current_user: dict = Depends(get_current_user)):
    """
    当前基于 Supabase Access Token 的无状态认证模式下，
    如需刷新，请在客户端通过 Supabase Auth 流程重新获取 Token。
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_response(
            code=40001,
            message="当前认证模式下不支持在服务端刷新 Token, 请通过重新登录获取新令牌",
        ),
    )


@router.get("/verify", summary="验证Token有效性")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """验证当前token是否有效"""
    return success_response(
        {
            "is_valid": True,
            "username": current_user["username"],
            "email": current_user.get("email"),
            "user_id": current_user.get("id"),
        }
    )
