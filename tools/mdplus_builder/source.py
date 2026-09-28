"""Pinned source checkout helpers and shared production ROM policy."""
from __future__ import annotations

from pathlib import Path

from .common import BUILD, BuildError, run

# This is ROM policy, deliberately independent of manifest/audio/package inputs.
ADDRYU_TRACKS = (
    ("MusID_EHZ", 3), ("MusID_CPZ", 5), ("MusID_ARZ", 7), ("MusID_CNZ", 8),
    ("MusID_HTZ", 9), ("MusID_MCZ", 10), ("MusID_OOZ", 11), ("MusID_MTZ", 12),
    ("MusID_SCZ", 13), ("MusID_WFZ", 14), ("MusID_DEZ", 15), ("MusID_SpecStage", 29),
    ("MusID_EHZ_2P", 26), ("MusID_CNZ_2P", 27), ("MusID_MCZ_2P", 28), ("MusID_HPZ", 31),
)


def _clone_at(url: str, commit: str, destination: Path, local_source: Path | None = None) -> None:
    if destination.exists():
        head = _git_output(destination, "rev-parse", "HEAD").strip()
        if head != commit:
            raise BuildError(f"{destination} is at {head}, expected {commit}; remove build/ and retry")
        return
    BUILD.mkdir(parents=True, exist_ok=True)
    clone_from = str(local_source) if local_source else url
    run(["git", "clone", "--no-checkout", clone_from, destination])
    run(["git", "checkout", "--detach", commit], cwd=destination)


def _git_output(repo: Path, *args: str) -> str:
    import subprocess

    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BuildError(f"Unable to inspect Git checkout {repo}") from exc


def genesis_checksum(data: bytes) -> tuple[int, int]:
    if len(data) < 0x200:
        raise BuildError("File is too small to be a Mega Drive ROM")
    stored = int.from_bytes(data[0x18E:0x190], "big")
    calculated = 0
    for offset in range(0x200, len(data), 2):
        calculated = (calculated + int.from_bytes(data[offset : offset + 2].ljust(2, b"\0"), "big")) & 0xFFFF
    return stored, calculated
