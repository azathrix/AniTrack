from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from ..auth_service import (
    SESSION_COOKIE,
    account_response,
    authenticate,
    create_session_token,
    request_user,
    update_account,
)
from ..operation_service import record_operation_event


router = APIRouter()


class LoginPayload(BaseModel):
    username: str = ""
    password: str = ""


class AccountPayload(BaseModel):
    username: str = ""
    password: str = ""


@router.get("/api/auth/me")
async def api_auth_me(request: Request) -> dict:
    user = request_user(request)
    if not user:
        return {"authenticated": False, "username": ""}
    return account_response()


@router.post("/api/auth/login")
async def api_auth_login(payload: LoginPayload, response: Response) -> dict:
    username = payload.username.strip()
    if not authenticate(username, payload.password):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = create_session_token(username)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 14,
    )
    record_operation_event("auth", "登录成功", f"用户 {username} 已登录")
    return account_response()


@router.post("/api/auth/logout")
async def api_auth_logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE)
    record_operation_event("auth", "退出登录", "当前会话已退出")
    return {"authenticated": False, "message": "已退出登录"}


@router.put("/api/auth/account")
async def api_update_account(payload: AccountPayload, response: Response) -> dict:
    username = payload.username.strip() or "admin"
    update_account(username, payload.password)
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(username),
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 14,
    )
    record_operation_event("settings", "账号设置已保存", f"管理员账号已更新为 {username}")
    return account_response()
