from __future__ import annotations

from ..database import connect
from ..db import get_settings
from ..pipeline_models import ProcessorContext, ProcessorResult
from ..sync_service import process_local_presence_tasks, process_sync_tasks, task_retry_after


async def process_local_sync(context: ProcessorContext, payload: dict) -> ProcessorResult:
    entry_id = context.subject_id if context.subject_type == "entry" else int(payload.get("entry_id") or 0)
    if entry_id <= 0:
        return ProcessorResult.terminal("本地同步处理器缺少 entry_id")
    settings = get_settings()
    try:
        await process_sync_tasks(settings, limit=5)
    except Exception as exc:
        return ProcessorResult.retryable(str(exc)[:2000], task_retry_after(settings, context.attempts + 1))
    with connect() as conn:
        synced_count = conn.execute(
            "SELECT COUNT(*) AS count FROM local_assets WHERE entry_id=? AND status='synced'",
            (entry_id,),
        ).fetchone()["count"]
        pending_count = conn.execute(
            "SELECT COUNT(*) AS count FROM sync_tasks WHERE entry_id=? AND status IN ('pending','failed','running')",
            (entry_id,),
        ).fetchone()["count"]
    if pending_count:
        return ProcessorResult.retryable("仍有本地同步任务待完成", task_retry_after(settings, context.attempts + 1))
    return ProcessorResult.success(
        f"本地同步完成: {synced_count} 个文件",
        data={"entry_id": entry_id, "synced_count": int(synced_count or 0)},
        next_payload={"_subject_type": "entry", "_subject_id": entry_id, "entry_id": entry_id},
    )


async def process_local_presence(context: ProcessorContext, payload: dict) -> ProcessorResult:
    entry_id = context.subject_id if context.subject_type == "entry" else int(payload.get("entry_id") or 0)
    if entry_id <= 0:
        return ProcessorResult.terminal("本地存在性处理器缺少 entry_id")
    settings = get_settings()
    try:
        await process_local_presence_tasks(settings, limit=20)
    except Exception as exc:
        return ProcessorResult.retryable(str(exc)[:2000], task_retry_after(settings, context.attempts + 1))
    with connect() as conn:
        local_count = conn.execute(
            "SELECT COUNT(*) AS count FROM local_assets WHERE entry_id=? AND status='synced'",
            (entry_id,),
        ).fetchone()["count"]
    return ProcessorResult.success(
        "本地存在性检查完成",
        data={"entry_id": entry_id, "local_asset_count": int(local_count or 0)},
    )
