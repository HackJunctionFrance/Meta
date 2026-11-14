"""Apply an update payload without replacing Xcode signing, secrets or local data."""

import argparse
import datetime
import shutil
from pathlib import Path


def apply(payload, target):
    payload, target = Path(payload).resolve(), Path(target).resolve()
    if not (target / "ios/CameraAccess/CameraAccess.xcodeproj").is_dir():
        raise ValueError(
            "Choisis le dossier FirstFive contenant ios/CameraAccess/CameraAccess.xcodeproj."
        )
    paths = []
    protected = {".env", ".venv", ".git", "data", "xcuserdata"}
    for source in payload.rglob("*"):
        if source.is_symlink():
            raise ValueError("Unexpected symlink in update payload")
        if not source.is_file():
            continue
        relative = source.relative_to(payload)
        if any(part in protected or part.endswith(".xcodeproj") for part in relative.parts):
            raise ValueError("Update attempts to replace a protected path")
        destination = target / relative
        if any(
            (target / Path(*relative.parts[:i])).is_symlink()
            for i in range(1, len(relative.parts) + 1)
        ):
            raise ValueError("Destination contains a symlink")
        if not destination.resolve().is_relative_to(target):
            raise ValueError("Destination escapes the selected folder")
        if destination.exists() and not destination.is_file():
            raise ValueError("Expected a file: " + str(relative))
        paths.append((source, relative))
    backup = target / (
        "backup-before-update-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    backup.mkdir()
    # Complete backup before changing any destination file.
    for source, relative in paths:
        destination = target / relative
        if destination.exists():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, saved)
    for source, relative in paths:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return backup


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    parser.add_argument("--payload", type=Path, default=Path(__file__).resolve().parent / "payload")
    args = parser.parse_args()
    try:
        backup = apply(args.payload, args.target)
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from error
    print("Mise à jour appliquée. Sauvegarde :", backup)
    print("Relance le serveur Mac et clique sur ▶ dans Xcode pour installer cette version.")
