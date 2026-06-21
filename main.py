"""
FastAPI GitHub OAuth2 Application
Entry point - run with: uvicorn main:app --reload
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.routers import auth, home
from app.services import sync_uva_to_notion  # 引入我們剛剛寫好的服務

# ── Lifespan (管理背景排程) ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 系統啟動時執行
    scheduler = AsyncIOScheduler()
    # 設定每天 23:50 執行同步任務
    scheduler.add_job(sync_uva_to_notion, 'cron', hour=23, minute=50)
    scheduler.start()
    print("背景排程已啟動：每天 23:50 執行 UVA 進度同步")
    
    yield  # 這裡代表 FastAPI 正常運行中
    
    # 系統關閉時執行
    scheduler.shutdown()
    print("背景排程已關閉")

# ── App 初始化 ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="UVA Progress Tracker",
    description="Track UVA progress and sync to Notion",
    version="1.0.0",
    lifespan=lifespan,  # 將 lifespan 註冊進 FastAPI
)

# Session middleware must be added before routers
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=settings.SESSION_MAX_AGE,
    https_only=settings.SESSION_HTTPS_ONLY,
    same_site="lax",
)

# Register routers
app.include_router(home.router)
app.include_router(auth.router)