from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("APP_DATA_DIR", tempfile.mkdtemp(prefix="autoanime-media-contract-test-"))

from app.db import init_db, save_settings
from app.database import connect
from app.main import MediaCreatePayload, create_media_entry, settings_response


class MediaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        init_db()

    def test_settings_response_exposes_only_new_settings_contract(self) -> None:
        save_settings(
            {
                "auto_download_unique": "false",
                "auto_download_by_priority": "false",
                "download_backend": "api",
                "local_library_root": "/legacy",
                "nfo_output_root": "/legacy-nfo",
                "downloaders_json": json.dumps(
                    [
                        {
                            "id": "api-main",
                            "name": "PikPak API",
                            "type": "pikpak_api",
                            "remote_dir": "/Temp",
                            "auth_mode": "token",
                            "access_token": "access",
                            "refresh_token": "refresh",
                            "enabled": True,
                        }
                    ]
                ),
            }
        )

        payload = settings_response()

        for key in [
            "auto_download_unique",
            "auto_download_by_priority",
            "download_backend",
            "local_library_root",
            "nfo_output_root",
        ]:
            self.assertNotIn(key, payload)
        self.assertEqual(payload["downloaders"][0]["type"], "pikpak_api")
        self.assertEqual(payload["downloaders"][0]["remote_dir"], "/Temp")

    def test_create_media_entry_returns_episode_resource_contract(self) -> None:
        detail = create_media_entry(
            "movie",
            MediaCreatePayload(
                mode="add",
                title="Contract Movie",
                tmdb_id="tmdb-contract",
                year=2026,
                episode_number=1,
                resource_title="Contract Movie 2026 1080p",
                source_ref="magnet:?xt=urn:btih:contractmovie",
                subtitle_group="Manual",
                resolution="1080p",
                language="简体",
                subtitle_format="embedded",
            ),
        )

        self.assertEqual(detail["entry"]["media_type"], "movie")
        self.assertEqual(len(detail["episode_resources"]), 1)
        self.assertEqual(detail["episode_resources"][0]["selected"], 1)
        self.assertGreater(int(detail["episode_resources"][0]["release_id"]), 0)
        self.assertEqual(detail["episode_resources"][0]["magnet"], "magnet:?xt=urn:btih:contractmovie")
        self.assertGreater(int(detail["download_run_id"]), 0)
        with connect() as conn:
            release = conn.execute(
                "SELECT selected, magnet FROM releases WHERE id=?",
                (int(detail["episode_resources"][0]["release_id"]),),
            ).fetchone()
        self.assertIsNotNone(release)
        self.assertEqual(release["selected"], 1)
        self.assertEqual(release["magnet"], "magnet:?xt=urn:btih:contractmovie")
        self.assertNotIn("releases", detail)
        self.assertNotIn("download_artifacts", detail)
        self.assertNotIn("local_assets", detail)
        self.assertNotIn("tasks", detail)


if __name__ == "__main__":
    unittest.main()
