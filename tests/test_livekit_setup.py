import importlib.util
from pathlib import Path

import pytest
from dotenv import dotenv_values

spec = importlib.util.spec_from_file_location(
    "livekit_setup", Path(__file__).resolve().parents[1] / "scripts/configure_livekit_mac.py"
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)
SETTINGS = {
    "LIVEKIT_URL": "wss://test.example.invalid",
    "LIVEKIT_API_KEY": "test-key",
    "LIVEKIT_API_SECRET": "test-$secret",
}


def project(tmp_path):
    (tmp_path / "server").mkdir()
    (tmp_path / "server/main.py").touch()
    return tmp_path


def test_config_preserves_unrelated_values_and_replaces_duplicates(tmp_path):
    root = project(tmp_path)
    old = "# config\nLLM_PROVIDER=none\nLIVEKIT_URL=old\nexport LIVEKIT_URL=duplicate\n"
    (root / ".env").write_text(old)
    setup.configure(root, SETTINGS)
    values = dotenv_values(root / ".env")
    assert values["LLM_PROVIDER"] == "none"
    assert all(values[k] == v for k, v in SETTINGS.items())
    assert (root / ".env").read_text().count("LIVEKIT_URL=") == 1
    backup = next(root.glob("backup-before-update-*/.env"))
    assert backup.read_text() == old
    assert (root / ".env").stat().st_mode & 0o777 == 0o600
    assert backup.stat().st_mode & 0o777 == 0o600


def test_invalid_settings_do_not_modify_env(tmp_path):
    root = project(tmp_path)
    (root / ".env").write_text("KEEP=yes\n")
    with pytest.raises(ValueError):
        setup.configure(root, {**SETTINGS, "LIVEKIT_API_SECRET": "bad\nINJECT=yes"})
    assert (root / ".env").read_text() == "KEEP=yes\n"


def test_symlink_env_is_not_followed(tmp_path):
    root = project(tmp_path)
    secret = root / "original"
    secret.write_text("KEEP=yes\n")
    (root / ".env").symlink_to(secret)
    with pytest.raises(ValueError):
        setup.configure(root, SETTINGS)
    assert secret.read_text() == "KEEP=yes\n"
