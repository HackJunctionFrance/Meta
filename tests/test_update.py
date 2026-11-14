import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "updater", Path(__file__).resolve().parents[1] / "scripts/apply_update.py"
)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def test_update_preserves_signing_keys_and_backs_up_sources(tmp_path):
    target = tmp_path / "FirstFive"
    project = target / "ios/CameraAccess/CameraAccess.xcodeproj"
    project.mkdir(parents=True)
    (project / "project.pbxproj").write_text("USER SIGNING TEAM")
    (target / ".env").write_text("LOCAL CONFIG")
    (target / "server").mkdir()
    (target / "server/main.py").write_text("old")
    payload = tmp_path / "payload"
    (payload / "server").mkdir(parents=True)
    (payload / "server/main.py").write_text("new")
    backup = updater.apply(payload, target)
    assert (target / "server/main.py").read_text() == "new"
    assert (backup / "server/main.py").read_text() == "old"
    assert (project / "project.pbxproj").read_text() == "USER SIGNING TEAM"
    assert (target / ".env").read_text() == "LOCAL CONFIG"


def test_update_rejects_protected_paths_before_writing(tmp_path):
    target = tmp_path / "FirstFive"
    (target / "ios/CameraAccess/CameraAccess.xcodeproj").mkdir(parents=True)
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / ".env").write_text("must not be copied")
    with pytest.raises(ValueError):
        updater.apply(payload, target)
    assert not (target / ".env").exists()


def test_update_rejects_symlink_to_local_config(tmp_path):
    target = tmp_path / "FirstFive"
    (target / "ios/CameraAccess/CameraAccess.xcodeproj").mkdir(parents=True)
    (target / ".env").write_text("preserve")
    (target / "server").mkdir()
    (target / "server/main.py").symlink_to(target / ".env")
    payload = tmp_path / "payload"
    (payload / "server").mkdir(parents=True)
    (payload / "server/main.py").write_text("replacement")
    with pytest.raises(ValueError):
        updater.apply(payload, target)
    assert (target / ".env").read_text() == "preserve"
