from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..catalog_service import CATALOG_PAGE_SIZE, catalog_response
from ..database import connect
from ..db import get_settings, log
from ..media_service import (
    archive_seasonal_entry,
    build_entry_response,
    build_media_entry_response,
    create_media_entry,
    hide_entry,
    media_items_response,
    normalize_api_media_type,
    save_entry_payload,
    set_entry_following,
)
from ..metadata import refresh_entry_metadata_by_ids
from ..rss_scan_service import start_metadata_refresh_task
from ..schemas import EntryPayload, MediaCreatePayload, MetadataFetchPayload


router = APIRouter()


def _tag_params(tags: list[str] | None, tag: list[str] | None) -> list[str]:
    return [str(item) for item in [*(tags or []), *(tag or [])] if str(item or "").strip()]


@router.get("/api/seasonal/catalog")
async def api_seasonal_catalog(
    page: int = Query(1, ge=1),
    page_size: int = Query(CATALOG_PAGE_SIZE, ge=1, le=96),
    keyword: str = Query(""),
    year: int = Query(0),
    month: int = Query(0),
    media_type: str = Query(""),
    region: str = Query(""),
    scope: str = Query(""),
    tags: list[str] | None = Query(None),
    tag: list[str] | None = Query(None),
) -> dict:
    return catalog_response(
        "seasonal",
        page=page,
        page_size=page_size,
        keyword=keyword,
        year=year,
        month=month,
        media_type=media_type,
        region=region,
        scope=scope,
        tags=_tag_params(tags, tag),
    )


@router.get("/api/media/{media_type}/catalog")
async def api_media_catalog(
    media_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(CATALOG_PAGE_SIZE, ge=1, le=96),
    keyword: str = Query(""),
    year: int = Query(0),
    month: int = Query(0),
    region: str = Query(""),
    scope: str = Query(""),
    tags: list[str] | None = Query(None),
    tag: list[str] | None = Query(None),
) -> dict:
    normalized = normalize_api_media_type(media_type)
    return catalog_response(
        normalized,
        page=page,
        page_size=page_size,
        keyword=keyword,
        year=year,
        month=month,
        region=region,
        scope=scope,
        tags=_tag_params(tags, tag),
    )


@router.get("/api/media/{media_type}")
async def api_media_items(media_type: str) -> dict:
    return media_items_response(media_type)


@router.post("/api/media/{media_type}")
async def api_create_media_entry(media_type: str, payload: MediaCreatePayload) -> dict:
    normalized_type = normalize_api_media_type(media_type)
    detail = create_media_entry(normalized_type, payload)
    entry_id = int((detail.get("entry") or {}).get("id") or 0)
    if entry_id > 0 and (payload.bangumi_id.strip() or payload.tmdb_id.strip()):
        settings = get_settings()
        await refresh_entry_metadata_by_ids(
            entry_id,
            normalized_type,
            bangumi_id=payload.bangumi_id.strip(),
            tmdb_id=payload.tmdb_id.strip(),
            tmdb_token=settings.get("tmdb_token", "").strip(),
            proxy=settings.get("rss_proxy", ""),
        )
        return build_media_entry_response(normalized_type, entry_id)
    return detail


@router.get("/api/media/{media_type}/{entry_id}")
async def api_media_entry(media_type: str, entry_id: int) -> dict:
    return build_media_entry_response(media_type, entry_id)


@router.put("/api/media/{media_type}/{entry_id}")
async def api_update_media_entry(media_type: str, entry_id: int, payload: EntryPayload) -> dict:
    normalize_api_media_type(media_type)
    return save_entry_payload(entry_id, payload, expected_domain=None)


@router.delete("/api/media/{media_type}/{entry_id}")
async def api_delete_media_entry(media_type: str, entry_id: int) -> dict[str, str]:
    normalized = normalize_api_media_type(media_type)
    return hide_entry(
        entry_id,
        expected_media_type=normalized,
        success_message="已删除媒体条目，本地文件不会被删除",
        log_prefix="已删除媒体条目",
    )


@router.post("/api/media/{media_type}/{entry_id}/follow")
async def api_follow_media_entry(media_type: str, entry_id: int) -> dict[str, str]:
    normalize_api_media_type(media_type)
    return set_entry_following(entry_id, True)


@router.post("/api/media/{media_type}/{entry_id}/unfollow")
async def api_unfollow_media_entry(media_type: str, entry_id: int) -> dict[str, str]:
    normalize_api_media_type(media_type)
    return set_entry_following(entry_id, False)


@router.post("/api/media/{media_type}/{entry_id}/metadata/fetch")
async def api_fetch_media_metadata(media_type: str, entry_id: int, payload: MetadataFetchPayload) -> dict:
    normalized_type = normalize_api_media_type(media_type)
    bangumi_id = payload.bangumi_id.strip()
    tmdb_id = payload.tmdb_id.strip()
    with connect() as conn:
        entry = conn.execute("SELECT bangumi_id, tmdb_id FROM entries WHERE id=?", (entry_id,)).fetchone()
    if not entry:
        raise HTTPException(status_code=404, detail="媒体条目不存在")
    settings = get_settings()
    refreshed = await refresh_entry_metadata_by_ids(
        entry_id,
        normalized_type,
        bangumi_id=bangumi_id,
        tmdb_id=tmdb_id,
        tmdb_token=settings.get("tmdb_token", "").strip(),
        proxy=settings.get("rss_proxy", ""),
    )
    if not refreshed:
        tmdb_value = str(tmdb_id or entry["tmdb_id"] or "").strip()
        if tmdb_value and not settings.get("tmdb_token", "").strip():
            raise HTTPException(status_code=400, detail="刷新 TMDB 信息需要先在设置中配置 TMDB token")
        raise HTTPException(status_code=400, detail="请先填写 Bangumi ID 或 TMDB ID")
    log("info", f"媒体元数据已刷新: entry_id={entry_id} provider={','.join(refreshed)}")
    return build_media_entry_response(media_type, entry_id)


@router.post("/api/entries/{entry_id}/metadata/refresh")
async def api_refresh_entry_metadata_task(entry_id: int) -> dict[str, str]:
    with connect() as conn:
        exists = conn.execute("SELECT id FROM entries WHERE id=?", (entry_id,)).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="媒体条目不存在")
    operation_id = start_metadata_refresh_task(entry_id, f"手动刷新元数据: entry_id={entry_id}")
    return {"status": "started", "operation_id": str(operation_id), "message": "元数据刷新任务已创建"}


@router.get("/api/entries/{entry_id}/episodes")
async def api_entry_episodes(entry_id: int) -> dict:
    detail = build_entry_response(entry_id)
    if not detail.get("entry"):
        raise HTTPException(status_code=404, detail="媒体条目不存在")
    return {
        "entry": detail.get("entry"),
        "episodes": detail.get("episodes", []),
        "episode_resources": detail.get("episode_resources", []),
        "episode_subtitles": detail.get("episode_subtitles", []),
    }


@router.delete("/api/seasonal/{entry_id}")
async def api_delete_seasonal_entry(entry_id: int) -> dict[str, str]:
    return archive_seasonal_entry(entry_id)


@router.delete("/api/library/{entry_id}")
async def api_delete_library_entry(entry_id: int) -> dict[str, str]:
    return hide_entry(
        entry_id,
        expected_domain="library",
        success_message="已隐藏番剧库条目，关联记录已保留",
        log_prefix="已隐藏番剧库条目",
    )
