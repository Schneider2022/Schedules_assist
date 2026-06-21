"""
Home router — demonstrates reading user from the session.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.session import get_current_user
from app.services import sync_uva_to_notion

router = APIRouter(tags=["home"])


@router.get("/", summary="Home page")
async def home(request: Request):
    """
    Public home page.
    Returns a welcome message if the user is logged in, otherwise a prompt to log in.
    """
    user = get_current_user(request)

    if user:
        return JSONResponse({
            "message": f"Welcome, {user['name'] or user['email']}!",
            "user": {
                "email": user["email"],
                "name": user["name"],
                "picture": user["picture"],
            },
        })

    return JSONResponse({
        "message": "You are not logged in.",
        "login_url": "/login",
    })


@router.get("/me", summary="Current user profile")
async def me(request: Request):
    """
    Protected-style endpoint — returns 401 if not authenticated.
    In a real app, extract this into a dependency (Depends).
    """
    user = get_current_user(request)

    if not user:
        return JSONResponse(
            status_code=401,
            content={"detail": "Not authenticated. Visit /login to sign in."},
        )

    return JSONResponse({"user": user})

@router.post("/api/sync", summary="手動觸發 UVA 與 Notion 同步")
async def manual_sync(request: Request):
    """
    提供給前端按鈕呼叫，立刻執行一次同步任務。
    為了安全，可以限制只有登入的使用者才能觸發。
    """
    user = get_current_user(request)

    if not user:
        return JSONResponse(
            status_code=401,
            content={"detail": "請先登入後再執行同步操作。"},
        )

    # 執行同步邏輯
    try:
        await sync_uva_to_notion()
        return JSONResponse({"message": "同步任務已成功執行完成！請檢查你的 Notion 表格。"})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"同步過程中發生錯誤: {str(e)}"}
        )