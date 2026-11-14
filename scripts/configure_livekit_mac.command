#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python3 configure_livekit_mac.py --config livekit-config.json
