"""Refresh the self-contained SPTL source download from its local repository."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path, help="Path to the SplayerPlasmaTaskbarLyrics repository")
args = parser.parse_args()
source = args.source.resolve()
metadata = json.loads((source / "plasmoid/metadata.json").read_text())
version = metadata["KPlugin"]["Version"]
files = subprocess.check_output(["git", "-C", str(source), "ls-files", "-z"]).decode().split("\0")
directories = {"docs", "helper", "plasmoid", "plugin", "shared", "tests", "tools"}
top_level = {"README.md", "LICENSE", "THIRD_PARTY.md"}
paths = sorted(name for name in files if name and
               (name in top_level or Path(name).parts[0] in directories))
assert {"README.md", "LICENSE", "tools/install.py", "helper/sptl/server.py",
        "shared/settings.json", "plasmoid/metadata.json"}.issubset(paths)
destination = ROOT / "public/projects/SPTL"
destination.mkdir(parents=True, exist_ok=True)
archive = destination / f"sptl-{version}-source.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
    for name in paths:
        info = zipfile.ZipInfo(f"SPTL-{version}/{name}", date_time=(2026, 11, 20, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        package.writestr(info, (source / name).read_bytes())
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None
print(f"Packaged {len(paths)} source files into {archive.relative_to(ROOT)}")
print(f"SHA-256: {hashlib.sha256(archive.read_bytes()).hexdigest()}")
