"""Download official LiveKit development server, verify SHA256, extract executable locally."""

import hashlib
import platform
import tarfile
import urllib.request
from pathlib import Path

VERSION = "1.13.11"
root = Path(__file__).resolve().parent.parent / ".tools"
root.mkdir(exist_ok=True)
system = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
arch = {"x86_64": "amd64", "arm64": "arm64", "aarch64": "arm64"}.get(platform.machine())
if not system or not arch:
    raise SystemExit("Use the official LiveKit release for your platform.")
name = f"livekit_{VERSION}_{system}_{arch}.tar.gz"
base = f"https://github.com/livekit/livekit/releases/download/v{VERSION}/"
archive = root / name
urllib.request.urlretrieve(base + name, archive)
checks = urllib.request.urlopen(base + "checksums.txt").read().decode()
expected = next(line.split()[0] for line in checks.splitlines() if line.endswith(name))
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise SystemExit("Checksum mismatch; refusing to use downloaded artifact.")
with tarfile.open(archive) as tar:
    member = tar.getmember("livekit-server")
    if not member.isfile():
        raise SystemExit("Unexpected archive entry")
    # Extract only this known regular file, no archive paths or links.
    target = root / "livekit-server"
    target.write_bytes(tar.extractfile(member).read())
    target.chmod(0o755)
print("Verified LiveKit", VERSION, "installed at", target)
