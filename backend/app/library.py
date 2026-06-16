from __future__ import annotations

import re

from .parser import clean_name


def bool_setting(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def normalize_series_root_title(value: str) -> str:
    text = clean_name(value or "Unknown")
    patterns = [
        r"\s+第[一二三四五六七八九十百零两\d]+季$",
        r"\s+第[一二三四五六七八九十百零两\d]+期$",
        r"\s+season\s*\d+$",
        r"\s+s(?:eason)?\s*\d+$",
        r"\s+part\s*\d+$",
        r"\s+cour\s*\d+$",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.I)
    return clean_name(text or value or "Unknown")


def render_series_dir(series: dict, settings: dict[str, str]) -> str:
    template = settings.get("series_dir_template") or "{title_base} ({year}) [bangumi-{bangumi_id}]"
    title_cn = clean_name(series.get("title_cn") or series.get("title_raw") or "Unknown")
    title_base = normalize_series_root_title(title_cn)
    bangumi_id = series.get("bangumi_id") or "unknown"
    year = int(series.get("year") or 0)
    return template.format(
        title_cn=title_cn,
        title_base=title_base,
        title_raw=clean_name(series.get("title_raw") or title_cn),
        bangumi_id=bangumi_id,
        tmdb_id=series.get("tmdb_id") or "unknown",
        year=year or "0000",
    )


def render_season_dir(season: int, settings: dict[str, str]) -> str:
    template = settings.get("season_dir_template") or "Season {season:02d}"
    return template.format(season=season or 1)


def render_episode_name(series: dict, episode_number: int, episode_title: str, settings: dict[str, str]) -> str:
    template = settings.get("episode_name_template") or "{title_cn} - S{season:02d}E{episode:02d} - {episode_title}"
    title_cn = clean_name(series.get("title_cn") or series.get("title_raw") or "Unknown")
    return template.format(
        title_cn=title_cn,
        season=int(series.get("season_number") or 1),
        episode=int(episode_number or 0),
        episode_title=clean_name(episode_title or f"第{int(episode_number or 0):02d}话"),
    )


def target_dir(series: dict, settings: dict[str, str]) -> str:
    root = settings.get("library_root") or "/Anime"
    root = "/" + root.strip("/")
    return "/".join(
        [
            root,
            render_series_dir(series, settings),
            render_season_dir(int(series.get("season_number") or 1), settings),
        ]
    )
