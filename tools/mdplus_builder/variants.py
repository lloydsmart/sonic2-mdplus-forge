"""The two maintained build flavours; soundtrack policy stays in the manifest."""
from __future__ import annotations

from enum import Enum
from pathlib import Path

from .common import BUILD, ROM_PATH


class BuildVariant(Enum):
    PRODUCTION = "production"
    BUGFIXED = "bugfixed"

    @property
    def prepared_dir(self) -> Path:
        return BUILD / {
            BuildVariant.PRODUCTION: "prepared-modern",
            BuildVariant.BUGFIXED: "prepared-bugfixed",
        }[self]

    @property
    def rom_path(self) -> Path:
        return {
            BuildVariant.PRODUCTION: ROM_PATH,
            BuildVariant.BUGFIXED: BUILD / "sonic2-mdplus-bugfixed.md",
        }[self]

    def package_basename(self, basename: str) -> str:
        return basename + (" (Bugfixed)" if self is BuildVariant.BUGFIXED else "")
