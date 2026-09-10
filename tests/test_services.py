"""Unit tests for settings and history services."""

from pathlib import Path

from vietzip.services.history_service import HistoryService
from vietzip.services.recent_service import RecentService
from vietzip.services.settings_service import SettingsService


def test_settings_service(tmp_path):
    cfg_file = tmp_path / "settings.json"
    service = SettingsService(cfg_file)

    service.set("theme", "Dark")
    service.set("compression_level", 9)

    assert service.get("theme") == "Dark"
    assert service.get("compression_level") == 9

    # Kiểm tra đọc lại từ file
    reloaded = SettingsService(cfg_file)
    assert reloaded.get("theme") == "Dark"
    assert reloaded.get("compression_level") == 9


def test_history_service(tmp_path):
    hist_file = tmp_path / "history.json"
    service = HistoryService(hist_file, max_records=5)

    service.add_record(
        operation="compress",
        input_summary="file1.txt",
        output_path="out.zip",
        file_count=1,
        original_size=1000,
        final_size=500,
        elapsed_seconds=1.2,
    )

    records = service.get_records()
    assert len(records) == 1
    assert records[0]["operation"] == "compress"

    service.clear()
    assert len(service.get_records()) == 0


def test_recent_service(tmp_path):
    rec_file = tmp_path / "recent.json"
    service = RecentService(rec_file, max_items=3)

    f1 = tmp_path / "1.zip"
    f1.touch()
    f2 = tmp_path / "2.zip"
    f2.touch()

    service.add(f1)
    service.add(f2)

    items = service.get_all()
    assert len(items) == 2
    assert items[0] == str(f2.resolve())
