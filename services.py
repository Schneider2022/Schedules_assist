"""
Business logic for tracking UVA progress and updating Notion.
"""
import httpx
from notion_client import AsyncClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def fetch_uva_accepted_problems(uva_user_id: str) -> list[int]:
    """
    呼叫 uHunt API 取得使用者所有 AC (Accepted) 的題目 ID。
    """
    url = f"https://uhunt.onlinejudge.org/api/subs-user/{uva_user_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # uHunt subs 格式: [[sub_id, prob_id, ver, ...], ...]
            # ver == 90 代表 Accepted
            accepted_ids = [
                sub[1] for sub in data.get("subs", []) 
                if sub[2] == 90
            ]
            return list(set(accepted_ids))  # 回傳不重複的 AC 題號
            
        except httpx.HTTPError as e:
            logger.error(f"Error fetching UVA data for ID {uva_user_id}: {e}")
            return []

async def sync_uva_to_notion():
    """
    從 Notion 讀取 UVA User ID，取得 AC 列表後，更新 Notion Database。
    （不需從外部傳入 uva_user_id，完全依賴 Notion 表格內的設定）
    """
    notion = AsyncClient(auth=settings.NOTION_API_KEY)
    database_id = settings.NOTION_DATABASE_ID

    try:
        # 1. 抓取所有尚未完成的題目 (Status != Done)
        query_result = await notion.databases.query(
            database_id=database_id,
            filter={
                "property": "Status",
                "status": {
                    "does_not_equal": "Done"
                }
            }
        )
        
        pages = query_result.get("results", [])
        if not pages:
            logger.info("Notion 中沒有需要更新的未完成題目。")
            return

        # 2. 從抓取到的 Notion 欄位中提取 UVA User ID
        uva_user_id = None
        for page in pages:
            properties = page.get("properties", {})
            uid_prop = properties.get("UVA User ID", {})
            # 只要在任何一列未完成的任務中找到 ID，就抓出來使用
            if uid_prop.get("number"):
                uva_user_id = str(uid_prop.get("number"))
                break 
        
        if not uva_user_id:
            logger.error("無法在 Notion 表格中找到 'UVA User ID'。請確保未完成題目的該欄位有填寫數字。")
            return

        logger.info(f"從 Notion 取得 UVA User ID: {uva_user_id}，開始向 uHunt 查詢...")

        # 3. 使用取得的 ID 呼叫 uHunt API
        accepted_problems = await fetch_uva_accepted_problems(uva_user_id)
        
        if not accepted_problems:
            logger.info("該帳號目前在 uHunt 上沒有 AC 紀錄或查詢失敗。")
            return

        # 4. 比對並更新 Notion 狀態
        update_count = 0
        for page in pages:
            properties = page.get("properties", {})
            
            # 安全地讀取 UVA Problem ID
            prob_id_prop = properties.get("UVA Problem ID", {})
            prob_id = prob_id_prop.get("number")

            # 如果這個 Notion 題號出現在 uHunt 的 AC 列表中
            if prob_id and int(prob_id) in accepted_problems:
                logger.info(f"發現題目 {prob_id} 已 AC！正在更新 Notion 狀態為 Done...")
                await notion.pages.update(
                    page_id=page["id"],
                    properties={
                        "Status": {
                            "status": {"name": "Done"}
                        }
                    }
                )
                update_count += 1
                
        logger.info(f"同步完成！本次共更新了 {update_count} 題。")

    except Exception as e:
        logger.error(f"Notion 同步過程中發生錯誤: {e}")