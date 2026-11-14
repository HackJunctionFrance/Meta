#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

python_bin=""
for candidate in python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' 2>/dev/null; then
    python_bin="$candidate"
    break
  fi
done
if [ -z "$python_bin" ]; then
  echo "Python 3.11 ou plus récent est nécessaire."
  echo "Installe Python 3.12 pour macOS depuis python.org, puis relance ce script."
  exit 1
fi
if [ ! -d .venv ]; then
  "$python_bin" -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.lock
if command -v scutil >/dev/null 2>&1; then
  mac_name="$(scutil --get LocalHostName)"
  printf '\nAdresse à saisir dans FirstFive sur l’iPhone : http://%s.local:8000\n' "$mac_name"
  printf 'Le Mac et l’iPhone doivent être sur le même réseau.\n'
fi
printf '\nFirstFive : laisse ce terminal ouvert. Ctrl+C arrête le serveur.\n'
printf 'Navigateur sur ce Mac : http://localhost:8000/test-caller\n'
printf 'Console : http://localhost:8000/console?mode=operator\n\n'
exec .venv/bin/python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
