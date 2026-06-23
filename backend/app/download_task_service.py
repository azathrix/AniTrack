from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from .database import connect
from .db import get_settings, now
from .downloader_service import provider_key, settings_for_attempt
from .library import render_episode_name, target_dir
from .runtime_service import ACTIVE_DOWNLOAD_STATUSES
from .sync_service import local_episode_path
from .utils import row_to_dict


FINAL_DOWNLOAD_STATUSES = {"completed", "failed", "cancelled"}
DOWNLOAD_STATUS_MAP = {
    "running": "submitting",
    "submitted": "remote_downloading",
    "downloading": "local_copying",
}


def canonical_download_status(value: str) -> str:
    key = str(value or "pending").strip().lower()
    return DOWNLOAD_STATUS_MAP.get(key, key or "pending")


def download_phase(value: str) -> str:
    status = canonical_download_status(value)
    if status in {
        "pending",
        "submitting",
        "remote_downloading",
        "remote_completed",
        "local_copying",
        "completed",
        "failed",
        "cancelled",
    }:
        return status
    return "pending"


def download_status_text(value: str) -> str:
    return {
        "pending": "等待下载",
        "submitting": "提交下载器",
        "remote_downloading": "等待下载器完成",
        "remote_completed": "下载器已完成",
        "local_copying": "整理到本地",
        "completed": "可观看",
        "failed": "失败",
        "cancelled": "已取消",
    }.get(download_phase(value), value or "等待下载")


def provider_index_from_key(value: str) -> int:
    text = str(value or "")
    if "#" not in text:
        return 0
    try:
        return max(0, int(text.rsplit("#", 1)[1]) - 1)
    except ValueError:
        return 0


def active_download_exists(conn, entry_id: int, episode_number: int) -> bool:
    placeholders = ",".join("?" for _ in ACTIVE_DOWNLOAD_STATUSES)
    row = conn.execute(
        f"""
        SELECT 1
        FROM download_jobs
        WHERE entry_id=? AND episode_number=? AND status IN ({placeholders})
        LIMIT 1
        """,
        (entry_id, episode_number, *ACTIVE_DOWNLOAD_STATUSES),
    ).fetchone()
    return bool(row)


def selected_episode_resource(conn, entry_id: int, episode_number: int):
    return conn.execute(
        """
        SELECT *
        FROM episode_resources
        WHERE entry_id=? AND episode_number=?
        ORDER BY selected DESC, id DESC
        LIMIT 1
        """,
        (entry_id, episode_number),
    ).fetchone()


def queue_download_for_release(release_id: int, *, reset_cancelled: bool = False) -> dict[str, Any]:
    if release_id <= 0:
        return {"queued": False, "reason": "缺少 release_id"}
    settings = settings_for_attempt(get_settings(), 0)
    with connect() as conn:
        release = conn.execute(
            """
            SELECT r.*, e.display_title, e.title_raw, e.title_cn, e.bangumi_id, e.tmdb_id,
                   e.year, e.season_number, e.media_type, e.target_library_id
            FROM releases r
            JOIN entries e ON e.id=r.entry_id
            WHERE r.id=?
            """,
            (release_id,),
        ).fetchone()
        if not release:
            return {"queued": False, "reason": "发布不存在"}
        entry_id = int(release["entry_id"] or 0)
        episode_number = int(release["episode_number"] or 0)
        local_asset = conn.execute(
            """
            SELECT id
            FROM local_assets
            WHERE entry_id=? AND episode_number=? AND status='synced'
            LIMIT 1
            """,
            (entry_id, episode_number),
        ).fetchone()
        if local_asset:
            return {"queued": False, "reason": "本地文件已存在"}
        if active_download_exists(conn, entry_id, episode_number):
            return {"queued": False, "reason": "已有活跃下载任务"}
        resource = selected_episode_resource(conn, entry_id, episode_number)
        episode = conn.execute(
            "SELECT id FROM episodes WHERE entry_id=? AND episode_number=? ORDER BY id DESC LIMIT 1",
            (entry_id, episode_number),
        ).fetchone()
        source_ref = str((resource and resource["source_ref"]) or release["magnet"] or release["torrent_url"] or "")
        remote_target = target_dir(dict(release), settings)
        remote_name = render_episode_name(dict(release), episode_number, "", settings)
        remote_path = str(PurePosixPath(remote_target) / remote_name)
        target_local_path = local_episode_path({"artifact_name": remote_name, "episode_number": episode_number}, dict(release), settings)
        provider = provider_key(settings)
        ts = now()
        existing = conn.execute(
            """
            SELECT id, status
            FROM download_jobs
            WHERE entry_id=? AND episode_number=?
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (entry_id, episode_number),
        ).fetchone()
        if existing and canonical_download_status(str(existing["status"] or "")) == "cancelled" and not reset_cancelled:
            return {"queued": False, "reason": "该集下载已取消，需手动重试"}
        conn.execute(
            """
            INSERT INTO download_jobs
              (series_id, entry_id, episode_resource_id, episode_id, episode_number, release_id,
               provider, provider_index, provider_key, download_task_id, status, phase, attempts,
               source_ref, target_dir, remote_path, target_local_path, normalized_name,
               progress, progress_text, created_at, updated_at, last_seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'pending', 'pending', 0,
                    ?, ?, ?, ?, ?, 0, '等待下载', ?, ?, ?)
            ON CONFLICT(entry_id, episode_number, provider) DO UPDATE SET
              release_id=excluded.release_id,
              series_id=excluded.series_id,
              episode_resource_id=excluded.episode_resource_id,
              episode_id=excluded.episode_id,
              provider_index=excluded.provider_index,
              provider_key=excluded.provider_key,
              status='pending',
              phase='pending',
              retry_after='',
              last_error='',
              source_ref=excluded.source_ref,
              target_dir=excluded.target_dir,
              remote_path=excluded.remote_path,
              target_local_path=excluded.target_local_path,
              normalized_name=excluded.normalized_name,
              progress=0,
              progress_text='等待下载',
              updated_at=excluded.updated_at,
              last_seen_at=excluded.last_seen_at
            """,
            (
                int(release["series_id"] or 0),
                entry_id,
                int(resource["id"] or 0) if resource else 0,
                int(episode["id"] or 0) if episode else 0,
                episode_number,
                release_id,
                provider,
                provider_index_from_key(provider),
                provider,
                source_ref,
                remote_target,
                remote_path,
                target_local_path,
                remote_name,
                ts,
                ts,
                ts,
            ),
        )
        task = conn.execute(
            """
            SELECT *
            FROM download_jobs
            WHERE entry_id=? AND episode_number=? AND provider=?
            """,
            (entry_id, episode_number, provider),
        ).fetchone()
        conn.execute(
            """
            UPDATE episode_resources
            SET status='queued', updated_at=?
            WHERE entry_id=? AND episode_number=? AND selected=1
            """,
            (ts, entry_id, episode_number),
        )
    return {"queued": True, "task": row_to_dict(task), "reason": "已创建下载任务"}


def list_download_tasks(limit: int = 200) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT dj.*,
                   e.display_title,
                   e.title_cn,
                   e.title_raw,
                   e.media_type AS entry_media_type,
                   er.title AS resource_title,
                   er.source_ref AS resource_ref,
                   la.id AS local_asset_id,
                   la.local_path AS local_asset_path
            FROM download_jobs dj
            LEFT JOIN entries e ON e.id=dj.entry_id
            LEFT JOIN episode_resources er ON er.id=dj.episode_resource_id
            LEFT JOIN local_assets la
              ON la.entry_id=dj.entry_id
             AND la.episode_number=dj.episode_number
             AND la.status='synced'
            ORDER BY CASE dj.status
              WHEN 'local_copying' THEN 0
              WHEN 'remote_completed' THEN 1
              WHEN 'remote_downloading' THEN 2
              WHEN 'submitting' THEN 3
              WHEN 'pending' THEN 4
              WHEN 'failed' THEN 5
              WHEN 'cancelled' THEN 6
              WHEN 'completed' THEN 7
              ELSE 8
            END, dj.updated_at DESC, dj.id DESC
            LIMIT ?
            """,
            (max(1, min(500, int(limit or 200))),),
        ).fetchall()
    tasks: list[dict[str, Any]] = []
    for row in rows:
        item = row_to_dict(row)
        status = canonical_download_status(str(item.get("status") or ""))
        item["status"] = status
        item["phase"] = download_phase(str(item.get("phase") or status))
        item["status_text"] = download_status_text(status)
        item["display_title"] = item.get("display_title") or item.get("title_cn") or item.get("title_raw") or "未命名条目"
        item["resource_title"] = item.get("resource_title") or item.get("normalized_name") or item.get("source_ref") or "-"
        item["active"] = status in ACTIVE_DOWNLOAD_STATUSES
        tasks.append(item)
    return tasks


def download_overview(tasks: list[dict[str, Any]] | None = None) -> dict[str, int]:
    rows = tasks if tasks is not None else list_download_tasks()
    return {
        "total": len(rows),
        "active": sum(1 for item in rows if item.get("active")),
        "pending": sum(1 for item in rows if item.get("status") == "pending"),
        "failed": sum(1 for item in rows if item.get("status") == "failed"),
        "completed": sum(1 for item in rows if item.get("status") == "completed"),
    }
