from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from .database import connect
from .runtime_store import runtime_store
from .utils import enrich_catalog_entry, rows_to_dicts, summarize_seasonal_entry


CATALOG_PAGE_SIZE = 24


def _safe_page(value: int) -> int:
    return max(1, int(value or 1))


def _safe_page_size(value: int) -> int:
    return max(1, min(96, int(value or CATALOG_PAGE_SIZE)))


def _tag_values(text: str) -> list[str]:
    try:
        value = json.loads(text or "[]")
    except Exception:
        value = []
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        tag = str(item or "").strip()
        if not tag:
            continue
        if len(tag) > 16:
            continue
        if any(ch.isdigit() for ch in tag) and any(ch in tag for ch in "-/年月日"):
            continue
        result.append(tag)
    return result


def _catalog_kind(value: str) -> str:
    key = str(value or "seasonal").strip().lower()
    if key in {"seasonal", "anime", "movie", "tv"}:
        return key
    return "seasonal"


def _catalog_where(kind: str, filters: dict[str, Any]) -> tuple[str, list[Any]]:
    clauses = ["COALESCE(e.hidden, 0)=0"]
    params: list[Any] = []
    if kind == "seasonal":
        clauses.extend(
            [
                "e.bangumi_id != ''",
                "COALESCE(se.following, 1)=1",
                "COALESCE(se.archived, 0)=0",
            ]
        )
    else:
        clauses.append("LOWER(COALESCE(e.media_type, 'anime'))=?")
        params.append(kind)

    keyword = str(filters.get("keyword") or "").strip().lower()
    if keyword:
        like = f"%{keyword}%"
        clauses.append(
            """
            (
              LOWER(COALESCE(e.display_title, '')) LIKE ?
              OR LOWER(COALESCE(e.title_cn, '')) LIKE ?
              OR LOWER(COALESCE(e.title_root, '')) LIKE ?
              OR LOWER(COALESCE(w.title_root, '')) LIKE ?
              OR LOWER(COALESCE(e.title_raw, '')) LIKE ?
              OR LOWER(COALESCE(e.bangumi_id, '')) LIKE ?
              OR LOWER(COALESCE(e.tmdb_id, '')) LIKE ?
            )
            """
        )
        params.extend([like] * 7)

    year = int(filters.get("year") or 0)
    if year > 0:
        clauses.append("e.year=?")
        params.append(year)

    month = int(filters.get("month") or 0)
    if 1 <= month <= 12:
        clauses.append("e.month=?")
        params.append(month)

    region = str(filters.get("region") or "").strip()
    if region:
        clauses.append("e.region=?")
        params.append(region)

    media_type = str(filters.get("media_type") or "").strip().lower()
    if media_type and media_type in {"anime", "movie", "tv"}:
        clauses.append("LOWER(COALESCE(e.media_type, 'anime'))=?")
        params.append(media_type)

    scope = str(filters.get("scope") or "").strip()
    if scope:
        clauses.append(
            """
            (
              e.season_label=?
              OR e.arc_label=?
              OR e.part_label=?
              OR ('第' || e.season_number || '季')=?
              OR ('Season ' || printf('%02d', e.season_number))=?
            )
            """
        )
        params.extend([scope, scope, scope, scope, scope])

    for tag in filters.get("tags") or []:
        tag_text = str(tag or "").strip()
        if not tag_text:
            continue
        clauses.append("e.tags_json LIKE ?")
        params.append(f"%{tag_text}%")

    return " AND ".join(clauses), params


def _catalog_select_sql(where_sql: str) -> str:
    return f"""
        SELECT e.id,
          e.work_id,
          e.media_type,
          e.region,
          e.source_provider,
          e.metadata_provider,
          e.external_id,
          e.target_library_id,
          e.genres_json,
          e.tags_json,
          e.display_title,
          e.title_root,
          e.poster_url,
          e.entry_kind,
          e.season_label,
          e.arc_label,
          e.part_label,
          e.special_label,
          e.title_cn,
          e.title_raw,
          e.bangumi_id,
          e.tmdb_id,
          e.bangumi_score,
          e.tmdb_score,
          e.year,
          e.month,
          e.season_number,
          w.title_root AS work_title,
          COUNT(DISTINCT ep.id) AS episode_count,
          COUNT(DISTINCT r.id) AS release_count,
          COUNT(DISTINCT r.subtitle_group) AS group_count,
          COUNT(DISTINCT r.resolution) AS resolution_count,
          COUNT(DISTINCT r.language) AS language_count,
          GROUP_CONCAT(DISTINCT r.subtitle_group) AS subtitle_groups,
          GROUP_CONCAT(DISTINCT r.resolution) AS resolutions,
          GROUP_CONCAT(DISTINCT r.language) AS languages,
          COUNT(DISTINCT CASE WHEN dj.status IN ('submitted','running','completed','remote_downloading','local_copying') THEN dj.id END) AS downloaded_count,
          COUNT(DISTINCT da.id) AS download_artifact_count,
          COUNT(DISTINCT CASE WHEN COALESCE(ep.watchable, 0)=1 THEN ep.id END) AS local_asset_count,
          MAX(CASE WHEN ce.event_date >= ? THEN 1 ELSE 0 END) AS recent_update
        FROM entries e
        LEFT JOIN seasonal_entries se ON se.entry_id=e.id
        JOIN works w ON w.id=e.work_id
        LEFT JOIN episodes ep ON ep.entry_id=e.id
        LEFT JOIN releases r ON r.entry_id=e.id
        LEFT JOIN download_jobs dj ON dj.entry_id=e.id AND dj.episode_number=ep.episode_number
        LEFT JOIN download_artifacts da ON da.entry_id=e.id AND da.episode_number=ep.episode_number
        LEFT JOIN local_assets la ON la.entry_id=e.id AND la.episode_number=ep.episode_number AND la.status='synced'
        LEFT JOIN calendar_entries ce ON ce.entry_id=e.id
        WHERE {where_sql}
        GROUP BY e.id
        ORDER BY e.updated_at DESC, e.id DESC
        LIMIT ? OFFSET ?
    """


def _catalog_facets(kind: str, where_sql: str, params: list[Any]) -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT e.year, e.month, e.media_type, e.region, e.season_number,
                   e.season_label, e.arc_label, e.part_label, e.tags_json
            FROM entries e
            LEFT JOIN seasonal_entries se ON se.entry_id=e.id
            JOIN works w ON w.id=e.work_id
            WHERE {where_sql}
            ORDER BY e.updated_at DESC, e.id DESC
            LIMIT 800
            """,
            tuple(params),
        ).fetchall()
    years: set[int] = set()
    months: set[int] = set()
    media_types: set[str] = set()
    regions: set[str] = set()
    scopes: set[str] = set()
    tags: dict[str, int] = {}
    for row in rows:
        year = int(row["year"] or 0)
        month = int(row["month"] or 0)
        if year > 0:
            years.add(year)
        if 1 <= month <= 12:
            months.add(month)
        media_type = str(row["media_type"] or "").strip()
        if media_type:
            media_types.add(media_type)
        region = str(row["region"] or "").strip()
        if region:
            regions.add(region)
        scope = str(row["season_label"] or row["arc_label"] or row["part_label"] or "").strip()
        if not scope:
            season = max(1, int(row["season_number"] or 1))
            scope = f"第{season}季"
        scopes.add(scope)
        for tag in _tag_values(str(row["tags_json"] or "[]")):
            tags[tag] = tags.get(tag, 0) + 1
    return {
        "years": sorted(years, reverse=True),
        "months": sorted(months),
        "media_types": sorted(media_types),
        "regions": sorted(regions),
        "scopes": sorted(scopes),
        "tags": [item[0] for item in sorted(tags.items(), key=lambda item: (-item[1], item[0]))[:36]],
        "kind": kind,
    }


def catalog_response(kind: str, *, page: int = 1, page_size: int = CATALOG_PAGE_SIZE, **filters: Any) -> dict[str, Any]:
    catalog_kind = _catalog_kind(kind)
    page = _safe_page(page)
    page_size = _safe_page_size(page_size)
    offset = (page - 1) * page_size
    where_sql, params = _catalog_where(catalog_kind, filters)
    recent_cutoff = (datetime.now().date() - timedelta(days=7)).isoformat()
    with connect() as conn:
        total = int(
            conn.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM entries e
                LEFT JOIN seasonal_entries se ON se.entry_id=e.id
                JOIN works w ON w.id=e.work_id
                WHERE {where_sql}
                """,
                tuple(params),
            ).fetchone()["count"]
            or 0
        )
        rows = conn.execute(
            _catalog_select_sql(where_sql),
            (recent_cutoff, *params, page_size, offset),
        ).fetchall()
    raw_items = rows_to_dicts(rows)
    if catalog_kind == "seasonal":
        items = [enrich_catalog_entry(summarize_seasonal_entry(row)) for row in raw_items]
    else:
        items = [enrich_catalog_entry(row) for row in raw_items]
    for item in items:
        item["recent_update"] = int(item.get("recent_update") or 0)
    return {
        "kind": catalog_kind,
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": offset + len(items) < total,
        "facets": _catalog_facets(catalog_kind, where_sql, params),
    }


def calendar_response(week: str = "") -> dict[str, Any]:
    try:
        start = datetime.strptime(str(week or "")[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        today = datetime.now(timezone.utc)
        start = today - timedelta(days=today.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
              ce.id,
              ce.entry_id,
              ce.event_date,
              ce.event_time AS updated_at,
              ce.synced,
              e.display_title,
              e.title_root,
              e.poster_url,
              e.entry_kind,
              e.season_label,
              e.arc_label,
              e.part_label,
              e.special_label,
              w.title_root AS work_title,
              ce.episode_number
            FROM calendar_entries ce
            JOIN entries e ON e.id=ce.entry_id
            JOIN seasonal_entries se ON se.entry_id=e.id
            JOIN works w ON w.id=e.work_id
            WHERE COALESCE(e.hidden, 0)=0
              AND COALESCE(se.following, 1)=1
              AND COALESCE(se.archived, 0)=0
              AND ce.event_date >= ?
              AND ce.event_date < ?
            ORDER BY ce.event_date DESC, ce.episode_number DESC
            LIMIT 160
            """,
            (start.date().isoformat(), end.date().isoformat()),
        ).fetchall()
    return {"items": [enrich_catalog_entry(row) for row in rows_to_dicts(rows)]}


def logs_response() -> dict[str, Any]:
    logs = list(runtime_store.snapshot().get("logs") or [])[-300:]
    return {
        "server_logs": logs,
        "console_overview": {
            "recent_error_count": sum(1 for line in logs if "[ERROR]" in str(line)),
            "recent_warn_count": sum(1 for line in logs if "[WARN]" in str(line)),
        },
    }
