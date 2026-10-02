"""Curated no-MD+ reference. Deliberately independent of BuildVariant.BUGFIXED."""
from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

from .common import BUILD, DEPENDENCIES, SOURCE_MODERN_DIR, BuildError, load_json, require_program, run
from .source import _clone_at, _git_output, genesis_checksum

AUDITED_COMMIT = "380f37a731bfc720bb0371a35a593184a7ec5e43"
STOCK_BUGFIXED_ROM_PATH = BUILD / "sonic2-stock-bugfixed.md"
STOCK_BUGFIXED_LISTING_PATH = BUILD / "sonic2-stock-bugfixed.lst"
SOURCE_HASHES = {
    "s2.asm": "448630bb22c08b5281d143438296e5b9045f6539699ec3724147a7f945c938b9",
    "s2.constants.asm": "8de5f4a4e6abc56ea2504afe2f4d58cc8a7a3bfa80e3f3c9f1372231a3ca16cd",
    "s2.sounddriver.asm": "ff34692c633f96d50073c24f6ebb72df5c739892c31be6b19b2ae604e76232c7",
}
# Read-only audit: compressed songs have a separate assembly environment.
BUILD_LUA_SHA256 = "be0f24531604d40159f7b333f9ee7284d15a096ad6bcc3127808b97a2c136175"
PAGE_FLIP_FLAG = "ForgeFix2PSpritePageFlip"
# Upstream's enabled MCZ right-drill fix subtracts from the left drill by mistake.
# Keep its branch and instruction width; change only the addressed sub-object.
MCZ_RIGHT_DRILL_OLD = ("\taddi_.w\t#1,sub2_x_pos(a0)\n"
                       "    if fixBugs\n"
                       "\t; This properly makes the right drill fall the opposite direction.\n"
                       "\tbtst\t#render_flags.x_flip,render_flags(a0)\t; is Eggman facing right?\n"
                       "\tbeq.s\t.notfacingright2\t\t\t; is not, branch\n"
                       "\tsubi_.w\t#2,sub5_x_pos(a0)\n\n"
                       ".notfacingright2:")
MCZ_RIGHT_DRILL_FIXED = MCZ_RIGHT_DRILL_OLD.replace("subi_.w\t#2,sub5_x_pos(a0)",
                                                    "subi_.w\t#2,sub2_x_pos(a0)")
# Correct an unintended collision side effect of upstream's Obj2B culling fix.
# Keep the larger display radius and subtract eight only for SolidObject.
ARZ_PILLAR_OLD = ("\taddi.w\t#$B,d1\n"
                  "    endif\n"
                  "\tmoveq\t#0,d2\n"
                  "\tmove.b\ty_radius(a0),d2\n"
                  "\tmove.w\td2,d3\n"
                  "\taddq.w\t#1,d3\n"
                  "\tmove.w\t(sp)+,d4\n"
                  "\tjsrto\tJmpTo8_SolidObject")
ARZ_PILLAR_FIXED = ARZ_PILLAR_OLD.replace(
    "\tmove.b\ty_radius(a0),d2\n",
    "\tmove.b\ty_radius(a0),d2\n"
    "    if fixBugs\n"
    "\t; Forge: retain the culling fix, with retail-equivalent collision height.\n"
    "\tsubq.w\t#8,d2\n"
    "    endif\n",
)
# Obj82 already compensates walking collision for its larger pillar display
# radius. Derive both collision heights from the retail radius, without growth.
ARZ_OBJ82_OLD = ("\taddi.w\t#$B,d1\n"
                 "\tmoveq\t#0,d2\n"
                 "\tmove.b\ty_radius(a0),d2\n"
                 "\tmove.w\td2,d3\n"
                 "\taddq.w\t#1,d3\n"
                 "    if fixBugs\n"
                 "\ttst.b\tmapping_frame(a0)\t; is this a pillar?\n"
                 "\tbeq.s\t.notPillar\t\t; if not, branch\n"
                 "\tsubq.w\t#2,d3\n\n"
                 ".notPillar:\n"
                 "    endif\n"
                 "\tjsrto\tJmpTo23_SolidObject")
ARZ_OBJ82_FIXED = ARZ_OBJ82_OLD.replace(
    "\tmove.w\td2,d3\n\taddq.w\t#1,d3\n", "",
).replace("\tsubq.w\t#2,d3\n", "\tsubq.w\t#2,d2\n").replace(
    "    endif\n\tjsrto\tJmpTo23_SolidObject",
    "    endif\n\tmove.w\td2,d3\n\taddq.w\t#1,d3\n\tjsrto\tJmpTo23_SolidObject",
)
STOCK_BUGFIXED_SIZE = 2_097_152
STOCK_BUGFIXED_CHECKSUM = "FDEC"
STOCK_BUGFIXED_MD5 = "9a0fd894e5fd5e85a354d2578fab7421"
STOCK_BUGFIXED_SHA256 = "7e8fe718aea8344dfe32931097977c0661bc0dbc9c41cba60e7b7a5e12be933f"

# Exact context anchors, not a rewrite of arbitrary fixBugs expressions.
# The two normal VInt upload paths deliberately share one anchor (count 2).
PAGE_FLIP_PATTERNS = {
    "s2.asm": (
        ("    if ~~fixBugs\n\t; As with the sprite table upload,", 1),
        ("    if ~~fixBugs\n\t; Does not need to be done on lag frames.", 1),
        ("    if fixBugs\n\t; In two-player mode, we have to update the sprite table", 1),
        ("    if fixBugs\n\ttst.w\t(Two_player_mode).w\n\tbeq.s\t++\n"
         "\t; Like in Sonic 3, the sprite tables are page-flipped", 2),
        ("\tstopZ80\n    if fixBugs\n\t; Like in Sonic 3,", 1),
        ("BuildSprites_2P:\n    if fixBugs\n", 1),
        ("BuildSprites_P2:\n    if fixBugs\n", 1),
        ("    if fixBugs\n\t; The new sprite tables are complete:", 1),
    ),
    "s2.constants.asm": (
        ("    if fixBugs\nSprite_Table_Alternate:", 1),
        ("    if fixBugs\nCurrent_sprite_table_page:", 1),
    ),
}


def _replace_exact(text: str, old: str, new: str, count: int = 1) -> str:
    if text.count(old) != count:
        raise BuildError(f"Expected {count} curated source pattern(s): {old!r}")
    return text.replace(old, new)


def transform_source(data: bytes, filename: str) -> bytes:
    if filename not in SOURCE_HASHES or hashlib.sha256(data).hexdigest() != SOURCE_HASHES[filename]:
        raise BuildError(f"Pinned curated {filename} source hash changed")
    text = data.decode("utf-8")
    if filename == "s2.asm":
        text = _replace_exact(text, "\nfixBugs = 0\n", "\nfixBugs = 1\n"
                              f"{PAGE_FLIP_FLAG} = 0 ; Preserve retail 2P sprite-table behaviour.\n")
        text = _replace_exact(text, "\nFixMusicAndSFXDataBugs = fixBugs\n",
                              "\nFixMusicAndSFXDataBugs = 0\n")
        text = _replace_exact(text, MCZ_RIGHT_DRILL_OLD, MCZ_RIGHT_DRILL_FIXED)
        text = _replace_exact(text, ARZ_PILLAR_OLD, ARZ_PILLAR_FIXED)
        text = _replace_exact(text, ARZ_OBJ82_OLD, ARZ_OBJ82_FIXED)
    elif filename == "s2.sounddriver.asm":
        text = _replace_exact(text, "\nFixDriverBugs = fixBugs\n", "\nFixDriverBugs = 0\n")
    for pattern, count in PAGE_FLIP_PATTERNS.get(filename, ()):
        text = _replace_exact(text, pattern, pattern.replace("fixBugs", PAGE_FLIP_FLAG), count)
    return text.encode("utf-8")


def tracked_hashes(work: Path) -> dict[str, str]:
    return {name: hashlib.sha256((work / name).read_bytes()).hexdigest()
            for name in _git_output(work, "ls-files", "-z").split("\0") if name}


def apply_policy(work: Path) -> dict[str, str]:
    """Mutate a pristine disposable clone, checking every tracked input/output."""
    if _git_output(work, "rev-parse", "HEAD") != AUDITED_COMMIT:
        raise BuildError("Curated policy requires the audited pinned commit")
    if _git_output(work, "status", "--porcelain", "--untracked-files=all"):
        raise BuildError("Curated policy requires a pristine disposable source clone")
    before = tracked_hashes(work)
    lua_text = (work / "build.lua").read_text()
    if (before["build.lua"] != BUILD_LUA_SHA256
            or lua_text.count("\nFixMusicAndSFXDataBugs = 0\n") != 1):
        raise BuildError("Compressed music build policy changed")
    # Validate all transformations before making any edits.
    outputs = {name: transform_source((work / name).read_bytes(), name) for name in SOURCE_HASHES}
    for name, content in outputs.items():
        (work / name).write_bytes(content)
    after = tracked_hashes(work)
    changed = {name for name in before if before[name] != after[name]}
    if changed != SOURCE_HASHES.keys():
        raise BuildError(f"Unexpected curated source changes: {sorted(changed)}")
    # Includes all sound/music/data and Fixed Files inputs; none are substituted.
    return {name: after[name] for name in sorted(changed)}


def verify_stock_bugfixed(path: Path) -> dict[str, str | int]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise BuildError(f"Cannot read stock Bugfixed ROM {path}: {exc}") from exc
    stored, calculated = genesis_checksum(data)
    result = {"size": len(data), "header_checksum": f"{stored:04X}",
              "calculated_checksum": f"{calculated:04X}",
              "md5": hashlib.md5(data, usedforsecurity=False).hexdigest(),
              "sha256": hashlib.sha256(data).hexdigest()}
    if stored != calculated:
        raise BuildError("Stock Bugfixed checksum mismatch")
    if (len(data), result["header_checksum"], result["md5"], result["sha256"]) != (
            STOCK_BUGFIXED_SIZE, STOCK_BUGFIXED_CHECKSUM, STOCK_BUGFIXED_MD5, STOCK_BUGFIXED_SHA256):
        raise BuildError(f"Stock Bugfixed ROM differs from the audited curated target: {result}")
    return result


def build_stock_bugfixed() -> dict[str, str | int]:
    lua = require_program("lua")
    run([lua, "-e", 'local major, minor = _VERSION:match("(%d+)%.(%d+)"); '
         'assert(tonumber(major) > 5 or (tonumber(major) == 5 and tonumber(minor) >= 3), '
         '"Stock Bugfixed build requires Lua 5.3 or newer")'])
    dependency = load_json(DEPENDENCIES)["source_modern"]
    if dependency["commit"] != AUDITED_COMMIT:
        raise BuildError("Curated policy requires the audited pinned commit")
    if not SOURCE_MODERN_DIR.is_dir():
        raise BuildError("Modern source is not fetched; run bootstrap first")
    if _git_output(SOURCE_MODERN_DIR, "rev-parse", "HEAD") != AUDITED_COMMIT:
        raise BuildError("Source dependency is not at the audited pinned commit")
    with tempfile.TemporaryDirectory(prefix="stock-bugfixed-", dir=BUILD) as directory:
        work = Path(directory) / "source"
        _clone_at(dependency["url"], AUDITED_COMMIT, work, SOURCE_MODERN_DIR)
        apply_policy(work)
        prepared_hashes = tracked_hashes(work)
        run([lua, "build.lua"], cwd=work)
        if tracked_hashes(work) != prepared_hashes:
            raise BuildError("Upstream build unexpectedly modified tracked source inputs")
        result = verify_stock_bugfixed(work / "s2built.bin")
        shutil.copy2(work / "s2built.bin", STOCK_BUGFIXED_ROM_PATH)
        shutil.copy2(work / "s2.lst", STOCK_BUGFIXED_LISTING_PATH)
    return result
