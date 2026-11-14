"""Install private LiveKit settings and restart only this project's local server."""

import argparse
import datetime
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

KEYS = ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")


def configure(project, settings):
    project = Path(project).resolve()
    if not (project / "server/main.py").is_file():
        raise ValueError("Choisis le dossier FirstFive contenant server/main.py.")
    if any(not isinstance(settings.get(k), str) or not settings[k].strip() for k in KEYS):
        raise ValueError("Les trois paramètres LiveKit sont nécessaires.")
    values = {k: settings[k].strip() for k in KEYS}
    if any(any(c in v for c in "\r\n\x00") for v in values.values()):
        raise ValueError("Une valeur LiveKit contient un caractère invalide.")
    url = urlparse(values["LIVEKIT_URL"])
    if url.scheme != "wss" or not url.hostname or "\\" in values["LIVEKIT_URL"]:
        raise ValueError("L'URL LiveKit Cloud doit commencer par wss://, sans antislash.")
    target = project / ".env"
    if target.is_symlink():
        raise ValueError("Le fichier .env est un lien symbolique ; configuration interrompue.")
    old = target.read_text() if target.exists() else ""
    pattern = re.compile(r"^\s*(?:export\s+)?(?:" + "|".join(KEYS) + r")\s*=")
    lines = [line for line in old.splitlines() if not pattern.match(line)]
    # Quote values without dotenv expansion, including any dollar signs in secrets.
    lines.extend(f"{k}='{values[k]}'" for k in KEYS)
    if any("'" in v or "\\" in v for v in values.values()):
        raise ValueError("Format de clé inattendu ; configuration interrompue.")
    if target.exists():
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = project / ("backup-before-update-" + stamp)
        backup.mkdir(mode=0o700)
        shutil.copyfile(target, backup / ".env")
        (backup / ".env").chmod(0o600)
    fd, name = tempfile.mkstemp(prefix=".env-livekit-", dir=project)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write("\n".join(lines) + "\n")
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)
    return project, values


def stop_project_server(project):
    result = subprocess.run(
        ["lsof", "-nP", "-iTCP:8000", "-sTCP:LISTEN", "-t"],
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("Impossible de vérifier le port 8000. Arrête le serveur avec Ctrl C.")
    pids = {int(line) for line in result.stdout.splitlines() if line.isdigit()}
    for pid in pids:
        command = subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True)
        details = subprocess.check_output(
            ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"], text=True
        )
        directories = [
            Path(line[1:]).resolve() for line in details.splitlines() if line.startswith("n")
        ]
        if (
            "uvicorn" not in command
            or "server.main:app" not in command
            or project not in directories
        ):
            raise RuntimeError(
                "Un autre programme utilise le port 8000 ; aucun processus n'a été arrêté."
            )
    for pid in pids:
        os.kill(pid, signal.SIGTERM)
    for _ in range(40):
        remaining = []
        for pid in pids:
            try:
                os.kill(pid, 0)
                remaining.append(pid)
            except ProcessLookupError:
                pass
        if not remaining:
            return
        time.sleep(0.25)
    raise RuntimeError("Le serveur n'a pas terminé son arrêt. Arrête-le avec Ctrl C puis relance.")


def run(project, values):
    python = project / ".venv/bin/python"
    if not python.exists():
        raise RuntimeError("Environnement Python absent ; lance d'abord scripts/start_mac.command.")
    stop_project_server(project)
    env = os.environ.copy()
    env.update(values)
    child = subprocess.Popen(
        [str(python), "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=project,
        env=env,
    )
    try:
        for _ in range(40):
            if child.poll() is not None:
                raise RuntimeError("Le serveur n'a pas démarré. Voir les messages ci-dessus.")
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1) as response:
                    health = json.load(response)
                if health.get("livekit") is True:
                    print("Configuration LiveKit chargée. Laisse ce Terminal ouvert.", flush=True)
                    print(
                        "Il reste à tester l'audio dans les deux sens avec les lunettes.",
                        flush=True,
                    )
                    subprocess.run(
                        ["open", "http://localhost:8000/console?mode=operator"], check=False
                    )
                    break
            except (OSError, ValueError):
                pass
            time.sleep(0.25)
        else:
            raise RuntimeError("Le serveur ne confirme pas la configuration LiveKit.")
        child.wait()
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--configure-only", action="store_true")
    args = parser.parse_args()
    if sys.platform != "darwin" and not args.configure_only:
        raise SystemExit("Cet installateur est destiné au Mac où fonctionne FirstFive.")
    project = args.project or Path.home() / "Documents/Hackathon/HackJunction/FirstFive"
    if not (project / "server/main.py").is_file() and sys.platform == "darwin":
        selected = subprocess.check_output(
            [
                "osascript",
                "-e",
                'POSIX path of (choose folder with prompt "Choisis ton dossier FirstFive existant")',
            ],
            text=True,
        )
        project = Path(selected.strip())
    try:
        settings = json.loads(args.config.read_text())
        project, values = configure(project, settings)
        print(
            "Les réglages LiveKit ont été enregistrés dans .env. Les clés ne sont pas affichées.",
            flush=True,
        )
        if not args.configure_only:
            run(project, values)
    except KeyboardInterrupt:
        print("Serveur arrêté.")
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
        # Do not include exception payloads that might contain private configuration.
        raise SystemExit(
            "Configuration ou redémarrage interrompu. Vérifie le dossier FirstFive et le serveur sur le port 8000. Les détails du serveur, s'il a démarré, sont affichés ci-dessus."
        ) from None


if __name__ == "__main__":
    main()
