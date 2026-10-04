from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import bugfixed
from .common import BUILD, DEPENDENCIES, ROM_PATH, SOURCE_MODERN_DIR, BuildError, load_json, require_program, run
from .source import ADDRYU_TRACKS, _clone_at, _git_output
from .variants import BuildVariant

STOCK_MODERN_ROM_PATH = BUILD / "sonic2-stock-modern.md"
STOCK_MODERN_LISTING_PATH = BUILD / "sonic2-stock-modern.lst"
STOCK_ROM_SIZE = 1_048_576
STOCK_ROM_MD5 = "9feeb724052c39982d432a7851c98d3e"
STOCK_ROM_SHA256 = "193bc4064ce0daf27ea9e908ed246d87ec576cc294833badebb590b6ad8e8f6b"


def bootstrap_modern(*, local_source: Path | None = None) -> None:
    dependency = load_json(DEPENDENCIES)["source_modern"]
    _clone_at(dependency["url"], dependency["commit"], SOURCE_MODERN_DIR, local_source)


def verify_stock_modern(path: Path) -> dict[str, str | int]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise BuildError(f"Cannot read stock ROM {path}: {exc}") from exc
    size = len(data)
    md5 = hashlib.md5(data, usedforsecurity=False).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()
    if (size, md5, sha256) != (STOCK_ROM_SIZE, STOCK_ROM_MD5, STOCK_ROM_SHA256):
        raise BuildError(
            "Modern stock ROM differs from the audited REV01 target: "
            f"size={size}, md5={md5}, sha256={sha256}"
        )
    return {"size": size, "md5": md5, "sha256": sha256}


def build_stock_modern() -> dict[str, str | int]:
    lua = require_program("lua")
    run([lua, "-e", 'local major, minor = _VERSION:match("(%d+)%.(%d+)"); '
         'assert(tonumber(major) > 5 or (tonumber(major) == 5 and tonumber(minor) >= 3), '
         '"Modern stock build requires Lua 5.3 or newer")'])
    if not SOURCE_MODERN_DIR.is_dir():
        raise BuildError("Modern source is not fetched; run bootstrap-modern first")
    dependency = load_json(DEPENDENCIES)["source_modern"]
    head = _git_output(SOURCE_MODERN_DIR, "rev-parse", "HEAD")
    if head != dependency["commit"]:
        raise BuildError(f"{SOURCE_MODERN_DIR} is at {head}, expected {dependency['commit']}")

    # Clone only committed files: local edits and stale generated ROMs cannot
    # affect the build, and upstream's generated files stay out of the input.
    with tempfile.TemporaryDirectory(prefix="stock-modern-", dir=BUILD) as directory:
        work = Path(directory) / "source"
        _clone_at(dependency["url"], dependency["commit"], work, SOURCE_MODERN_DIR)
        run([lua, "build.lua"], cwd=work)
        built = work / "s2built.bin"
        result = verify_stock_modern(built)
        shutil.copy2(built, STOCK_MODERN_ROM_PATH)
        shutil.copy2(work / "s2.lst", STOCK_MODERN_LISTING_PATH)
    return result


# Stage 2 is audited independently of the untouched stock build above.
AUDITED_MODERN_COMMIT = "380f37a731bfc720bb0371a35a593184a7ec5e43"
UPSTREAM_S2_SHA256 = "448630bb22c08b5281d143438296e5b9045f6539699ec3724147a7f945c938b9"
PREPARED_MODERN_DIR = BuildVariant.PRODUCTION.prepared_dir
MODERN_ROM_PATH = BUILD / "sonic2-modern-mdplus.md"
PLAY_MUSIC_ADDRESS = 0x135E
IMPLEMENTATION_ADDRESS = 0x100000
PREPARED_ROM_SIZE = 0x200000
PRODUCTION_CHECKSUM = "BE41"
PRODUCTION_MD5 = "9eb40c0601a7c424a0d1ce168b5f40f2"
PRODUCTION_SHA256 = "bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44"


@dataclass(frozen=True)
class VerificationProfile:
    """Frozen ROM identity, separate from the instruction/layout audit."""

    size: int
    checksum: str
    md5: str
    sha256: str


VERIFICATION_PROFILES = {
    BuildVariant.PRODUCTION: VerificationProfile(
        PREPARED_ROM_SIZE, PRODUCTION_CHECKSUM, PRODUCTION_MD5, PRODUCTION_SHA256,
    ),
    # Independently reproduced curated MD+ identity; never rebaseline Production.
    BuildVariant.BUGFIXED: VerificationProfile(
        2_097_152, "C145", "50e81d88e257f8d14608e57801b628c5",
        "f33a1946a609b8045bb56ffce2aba05196190965fed6ddf5f8eb3b80c52a0c52",
    ),
}

NATIVE_PLAY_MUSIC = bytes.fromhex("4a38ffe0660611c0ffe04e7511c0ffe44e75")
ROUTER_ADDRESS = 0x1003A8
HOOK_BYTES = bytes.fromhex("4ef9") + ROUTER_ADDRESS.to_bytes(4, "big") + bytes.fromhex("4e71") * 6
NATIVE_SOURCE = """PlayMusic:
\ttst.b\t(Sound_Queue.Music0).w
\tbne.s\t+
\tmove.b\td0,(Sound_Queue.Music0).w
\trts
+
\tmove.b\td0,(Sound_Queue.Music1).w
\trts
; End of function PlayMusic
"""
HOOK_SOURCE = """PlayMusic:
\tjmp\t(ForgeModernPlayMusic).l
; Keep the original 18-byte footprint; these six NOPs are unreachable.
\tnop
\tnop
\tnop
\tnop
\tnop
\tnop
    if (PlayMusic<>$135E)||(*-PlayMusic<>18)
\tfatal "Unexpected Stage 2 PlayMusic hook layout"
    endif
; End of function PlayMusic
"""
TAIL_SOURCE = "\tfinishBank\n\n; end of 'ROM'\n"
TAIL_REPLACEMENT = '\tfinishBank\n\n\tinclude "hybrid_modern.asm"\n\n; end of \'ROM\'\n'


# Audited upstream ID values, not a second routing policy. The assembler uses
# upstream symbols; the independent byte audit detects any numeric ID drift.
MODERN_MUSIC_IDS = dict(zip((
    "MusID_EHZ", "MusID_MCZ_2P", "MusID_OOZ", "MusID_MTZ", "MusID_HTZ",
    "MusID_ARZ", "MusID_CNZ_2P", "MusID_CNZ", "MusID_DEZ", "MusID_MCZ",
    "MusID_EHZ_2P", "MusID_SCZ", "MusID_CPZ", "MusID_WFZ", "MusID_HPZ",
), range(0x82, 0x91), strict=True)) | {"MusID_SpecStage": 0x92}
CONTROL_COMMANDS = (
    ("ForgeModernImmediate", 0x1300), ("ForgeModernFade", 0x1328),
    ("ForgeModernResume", 0x1400), ("ForgeModernVolumeLow", 0x1519),
    ("ForgeModernVolumeNormal", 0x15FF),
)
DISPATCH_ADDRESS = IMPLEMENTATION_ADDRESS + len(NATIVE_PLAY_MUSIC)
PRIMITIVES_ADDRESS = DISPATCH_ADDRESS + 16 * 8 + 2
COMMANDS = CONTROL_COMMANDS + tuple(
    (f"ForgeModernTrack{track:02d}", 0x1200 | track) for _, track in ADDRYU_TRACKS
)
PRIMITIVE_ADDRESSES = {label: PRIMITIVES_ADDRESS + i * 26 for i, (label, _) in enumerate(COMMANDS)}
IMPLEMENTATION_END = PRIMITIVES_ADDRESS + 21 * 26
OVERLAY_OPEN = bytes.fromhex("33fccd540003f7fa")
OVERLAY_CLOSE = bytes.fromhex("33fc00000003f7fa")


def expected_modern_extension() -> bytes:
    """Independent instruction encoding audit: every byte and branch target."""
    code = bytearray(NATIVE_PLAY_MUSIC)
    for symbol, track in ADDRYU_TRACKS:
        # Upstream encodes CMP.B immediate EA, not the CMPI alias.
        code.extend(bytes.fromhex("b03c") + MODERN_MUSIC_IDS[symbol].to_bytes(2, "big"))
        displacement = PRIMITIVE_ADDRESSES[f"ForgeModernTrack{track:02d}"] - (
            IMPLEMENTATION_ADDRESS + len(code) + 2
        )
        code.extend(bytes.fromhex("6700") + displacement.to_bytes(2, "big", signed=True))
    code.extend(bytes.fromhex("4e75"))
    for _, command in COMMANDS:
        code.extend(OVERLAY_OPEN + bytes.fromhex("33fc") + command.to_bytes(2, "big")
                    + bytes.fromhex("0003f7fe") + OVERLAY_CLOSE + bytes.fromhex("4e75"))
    return bytes(code)


def _modern_extension_source(variant: BuildVariant = BuildVariant.PRODUCTION) -> str:
    layout = LAYOUT_PROFILES[variant]
    text = Path(__file__).with_name("hybrid_modern.asm").read_text(encoding="utf-8")
    dispatch = "\n".join(
        f"    cmp.b   #{symbol},d0\n    beq.w   ForgeModernTrack{track:02d}"
        for symbol, track in ADDRYU_TRACKS
    )
    commands = "\n".join(
        f'{label}:\n    if {label}<>${PRIMITIVE_ADDRESSES[label] + layout.delta:06X}\n'
        f'        fatal "Unexpected {label} boundary"\n    endif\n'
        f"    move.w  #$CD54,(MDP_CTRL).l\n"
        f"    move.w  #${command:04X},(MDP_CMD).l\n"
        f"    move.w  #0,(MDP_CTRL).l\n    rts\n"
        for label, command in COMMANDS
    )
    for marker, replacement in (("; @DISPATCH@", dispatch), ("; @COMMANDS@", commands)):
        if text.count(marker) != 1:
            raise BuildError(f"Expected exactly one modern include marker: {marker}")
        text = text.replace(marker, replacement)
    policy = ("    if (ForgeFix2PSpritePageFlip<>0)||(FixDriverBugs<>0)||"
              "(FixMusicAndSFXDataBugs<>0)\n"
              '        fatal "Forge requires the frozen curated policy"\n    endif\n'
              if layout.curated else "")
    return (f"ForgeExpectedFixBugs = {int(layout.curated)}\n"
            f"ForgeImplementationBase = ${layout.implementation:06X}\n"
            f"ForgeSoundDataEnd = ${layout.sound_end:06X}\n" + policy + text)


# Every mutated upstream input is locked to the same audited modern commit.
UPSTREAM_Z80_SHA256 = "ff34692c633f96d50073c24f6ebb72df5c739892c31be6b19b2ae604e76232c7"
UPSTREAM_CONSTANTS_SHA256 = "8de5f4a4e6abc56ea2504afe2f4d58cc8a7a3bfa80e3f3c9f1372231a3ca16cd"
INPUT_START = "sndDriverInput:\n"
INPUT_END = "; End of function sndDriverInput\n"
INPUT_HOOK = """sndDriverInput:
    jmp (ForgeModernInput).l
    ds.b $10E0-*
    if (sndDriverInput<>$1084)||(*<>$10E0)
        fatal "Unexpected sndDriverInput footprint"
    endif
; End of function sndDriverInput
"""
LOADER_SOURCE = """SaxDec_GetByte:
\tmove.b\t(a6)+,d0
\tsubq.w\t#1,d7\t; Decrement remaining number of bytes
\tbne.s\t+
\taddq.w\t#4,sp\t; Exit the decompressor by meddling with the stack
+
\trts"""
LOADER_HOOK = """SaxDec_GetByte:
    jmp (ForgeModernSaxGetByte).l
    nop
    nop
    if (SaxDec_GetByte<>$EC0DE)||(*<>$EC0E8)
        fatal "Unexpected Saxman helper footprint"
    endif"""
RAM_HOLE = "\t\t\t\tds.b\t$500\t; $FFFFF100-$FFFFF5FF ; unused, leftover from the Sonic 1 sound driver (and used by it when you port it to Sonic 2)"
RAM_STATE = {
    "ForgeModernCounter": (0xFFF100, 4), "ForgeModernDuck": (0xFFF108, 1),
    "ForgeModernOwner": (0xFFF111, 1), "ForgeModernPending": (0xFFF112, 1),
    "ForgeModernHandoff": (0xFFF113, 1), "ForgeModernPaused": (0xFFF114, 1),
    "ForgeModernActive": (0xFFF115, 1),
}
RAM_HANDOFF = """ForgeModernCounter: ds.l 1
    ds.b 4
ForgeModernDuck: ds.b 1
    ds.b 8 ; includes $FFF110, deliberately unallocated
ForgeModernOwner: ds.b 1
ForgeModernPending: ds.b 1
ForgeModernHandoff: ds.b 1
ForgeModernPaused: ds.b 1
ForgeModernActive: ds.b 1
    ds.b $4EA ; retain the complete $F100-$F5FF reservation"""
SOUND_SOURCE = """PlaySound:
\t; Curiously, none of these functions write to 'Sound_Queue.Queue2'...
\tmove.b\td0,(Sound_Queue.SFX0).w
\trts
; End of function PlaySound
"""
SOUND2_SOURCE = """PlaySound2:
\tmove.b\td0,(Sound_Queue.SFX1).w
\trts
; End of function PlaySound2
"""
VINT_SOURCE = """VintRet:
\taddq.l\t#1,(Vint_runcount).w
\tmovem.l\t(sp)+,d0-a6
\trte
"""
VINT_HOOK = """VintRet:
    jmp (ForgeModernVintReturn).l
    nop
    nop
    if (VintRet<>$45E)||(*<>$468)
        fatal "Unexpected VInt return footprint"
    endif
"""
RESET_SOURCE = "\tbsr.w\tVDPSetupGame\n\tbsr.w\tJmpTo_SoundDriverLoad\n"
RESET_HOOK = """ForgeModernInitHook:
    jsr (ForgeModernInit).l
    nop
    if (ForgeModernInitHook<>$382)||(*<>$38A)
        fatal "Unexpected post-checksum GameInit hook footprint"
    endif
"""
PAUSE_SOURCES = tuple(
    (f"\tmove.b\t#MusID_{name},(Sound_Queue.Music0).w",
     f"\tjsr\t(ForgeModern{name}Request).l", count)
    for name, count in (("Pause", 1), ("Unpause", 3))
)


def _sound_hook(name: str, address: int) -> str:
    return (f'{name}:\n    jmp (ForgeModern{name}).l\n'
            f'    if ({name}<>${address:X})||(*-{name}<>6)\n'
            f'        fatal "Unexpected {name} footprint"\n    endif\n'
            f'; End of function {name}\n')


def _modern_router_source(variant: BuildVariant = BuildVariant.PRODUCTION) -> str:
    layout = LAYOUT_PROFILES[variant]
    text = Path(__file__).with_name("hybrid_modern_router.asm").read_text()
    routes = "\n".join(f"    cmp.b   #{symbol},d0\n    beq.w   ForgeModernRequest"
                       for symbol, _ in ADDRYU_TRACKS)
    text = _replace_modern(text, "; @ROUTE@", routes)
    assertions = []
    for name, (address, size) in RAM_STATE.items():
        assertions.append(
            f'    if ({name}<>ramaddr(${address | 0xFF000000:X}))||'
            f'({name}<Underwater_palette+$80)||({name}+{size}>Game_Mode)||'
            f'({name}<RAM_Start)||({name}+{size}>CrossResetRAM)\n'
            f'        fatal "{name} must occupy unused GameInit-cleared RAM"\n    endif\n')
    prefix = "".join(assertions)
    assertions = []
    for name, address in layout.router.items():
        assertions.append(f'    if {name}<>${address:06X}\n'
                          f'        fatal "Unexpected {name} boundary"\n    endif\n')
    return prefix + text + "".join(assertions)

Z80_READY = "\tld\t(ix+zVar.QueueToPlay),80h\t; Rewrite zComRange+8 flag so we know nothing new is coming in\n"
Z80_PAUSE = "\tld\ta,(zAbsVar.StopMusic)\t; Get pause/unpause flag"


def _replace_modern(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise BuildError(f"Expected exactly one modern source pattern: {old!r}")
    return text.replace(old, new)


def _prepare_modern_source(
    data: bytes, filename: str = "s2.asm", *, variant: BuildVariant = BuildVariant.PRODUCTION,
) -> bytes:
    layout = LAYOUT_PROFILES[variant]
    hashes = layout.source_hashes
    if filename not in hashes or hashlib.sha256(data).hexdigest() != hashes[filename]:
        raise BuildError(f"Pinned modern {filename} source structure changed")
    text = data.decode("utf-8")
    if filename == "s2.asm":
        for marker in (INPUT_START, INPUT_END):
            if text.count(marker) != 1:
                raise BuildError(f"Expected exactly one modern source pattern: {marker!r}")
        start = text.index(INPUT_START)
        end = text.index(INPUT_END, start) + len(INPUT_END)
        replacements = ((NATIVE_SOURCE, HOOK_SOURCE), (TAIL_SOURCE, TAIL_REPLACEMENT),
                        (text[start:end], INPUT_HOOK), (LOADER_SOURCE, layout.loader_hook),
                        (SOUND_SOURCE, _sound_hook("PlaySound", 0x1370)),
                        (SOUND2_SOURCE, _sound_hook("PlaySound2", 0x1376)),
                        (VINT_SOURCE, VINT_HOOK), (RESET_SOURCE, RESET_HOOK))
        for old, new, count in PAUSE_SOURCES:
            if text.count(old) != count:
                raise BuildError(f"Expected exactly {count} direct modern pause pattern: {old!r}")
            text = text.replace(old, new)
        if re.search(r"move\.b\s+#MusID_(?:Pause|Unpause),\(Sound_Queue\.Music[01]\)", text):
            raise BuildError("Ownership-blind pause mailbox write remains")
    elif filename == "s2.constants.asm":
        replacements = ((RAM_HOLE, RAM_HANDOFF),)
    else:
        replacements = (
            (Z80_READY, Z80_READY + "    cp MusID_ForgeStop\n    jp z,zHybridStopMusic\n"),
            (Z80_PAUSE, "    ld a,(zAbsVar.QueueToPlay)\n    cp MusID_ForgeStop\n"
             "    call z,zPlaySoundByIndex\n" + Z80_PAUSE),
            ("zTracksSaveEnd:\n", "zTracksSaveEnd:\nzHybridAck: ds.b 1\n"),
            # The added dispatch crosses the volume table's page boundary.
            # Make its existing two-byte automatic alignment explicit, so
            # upstream's warning-as-failure build still completes normally.
            ("\tensure1byteoffset 8\nzVolTLMaskTbl:",
             "    align 100h\n\tensure1byteoffset 8\nzVolTLMaskTbl:"),
            ("; end of Z80 'ROM'", '    include "hybrid_modern_z80.asm"\n\n; end of Z80 \'ROM\''),
        )
    for old, new in replacements:
        text = _replace_modern(text, old, new)
    return text.encode("utf-8")


def prepare_modern(*, variant: BuildVariant = BuildVariant.PRODUCTION) -> dict[str, str]:
    """Recreate generated preparation from committed inputs, never from old output."""
    prepared_dir = variant.prepared_dir
    dependency = load_json(DEPENDENCIES)["source_modern"]
    if dependency["commit"] != AUDITED_MODERN_COMMIT:
        raise BuildError("Modern adapter requires the audited pinned commit")
    if not SOURCE_MODERN_DIR.is_dir():
        raise BuildError("Modern source is not fetched; run bootstrap-modern first")
    head = _git_output(SOURCE_MODERN_DIR, "rev-parse", "HEAD")
    if head != dependency["commit"]:
        raise BuildError(f"{SOURCE_MODERN_DIR} is at {head}, expected {dependency['commit']}")
    with tempfile.TemporaryDirectory(prefix=f"prepare-{variant.value}-", dir=BUILD) as directory:
        work = Path(directory) / "source"
        _clone_at(dependency["url"], dependency["commit"], work, SOURCE_MODERN_DIR)
        if LAYOUT_PROFILES[variant].curated:
            bugfixed.apply_policy(work)
        for filename in ("s2.asm", "s2.sounddriver.asm", "s2.constants.asm"):
            path = work / filename
            path.write_bytes(_prepare_modern_source(path.read_bytes(), filename, variant=variant))
        for filename in ("hybrid_modern.asm", "hybrid_modern_handoff.asm",
                         "hybrid_modern_z80.asm", "hybrid_modern_router.asm", "modern_build.lua"):
            if (work / filename).exists():
                raise BuildError("Modern source already contains Forge's include filename")
            content = (_modern_extension_source(variant) if filename == "hybrid_modern.asm" else
                       _modern_router_source(variant) if filename == "hybrid_modern_router.asm" else
                       Path(__file__).with_name(filename).read_text(encoding="utf-8"))
            (work / filename).write_text(content, encoding="utf-8")
        # Only this generated output is replaced; dependency checkouts are inputs.
        if prepared_dir.exists():
            shutil.rmtree(prepared_dir)
        work.rename(prepared_dir)
    return {"source_commit": head, "prepared_source": str(prepared_dir)}


HANDOFF_ADDRESSES = {
    "ForgeModernBeginHandoff": 0x1002B6, "ForgeModernQueueStop": 0x1002BC,
    "ForgeModernCheckReady": 0x1002E8, "ForgeModernInput": 0x10032A,
    "ForgeModernSaxGetByte": 0x10039C, "ForgeModernHandoffEnd": 0x1003A8,
}
HANDOFF_END = HANDOFF_ADDRESSES["ForgeModernHandoffEnd"]
HANDOFF_SHA256 = "40082c3869f23691ccc6a631f794e44652f5c7c6f793b7fe3566de2b0d481759"
DRIVER_START = 0xEC0E8
DRIVER_LIMIT = 0xED100  # fixed DAC start; includes upstream's explicit growth padding
DRIVER_LENGTH_ADDRESS = 0xEC050
Z80_COMPRESSED_SIZE = 4009
Z80_LOADED_SIZE = 0x137A
Z80_SHA256 = "9f997cc7217dda878297f7359f3314c7876aeb29e8705d63bd4b6db1513db24f"
DRIVER_REGION_SHA256 = "d2288f0c731bcefd085782fe372e6d08cac815e127d35a01d885ea5866624812"
STOCK_MASKED_SHA256 = "3bf58d2d8a65599a52e13a7f92518e444c918d1b2edf8b5e7c9ab71fa715a268"
# Exact new-region checks accompany the digest of every unchanged stock byte.
# The whole audited REV01 baseline, with ONLY these regions zeroed, defines it.
STOCK_CHANGED_REGIONS = ((0x1084, 0x10E0), (DRIVER_LENGTH_ADDRESS, DRIVER_LENGTH_ADDRESS + 2),
                         (0xEC0DE, DRIVER_LIMIT))


# Stage 5 exact compiled routine boundaries and instruction digests.
ROUTER_ADDRESSES = {
    "ForgeModernPlayMusic": 0x1003A8,
    "ForgeModernRoute": 0x1003B8,
    "ForgeModernRequest": 0x1004B4,
    "ForgeModernDiscardMusic": 0x1004EE,
    "ForgeModernReturn": 0x100508,
    "ForgeModernComplete": 0x10050A,
    "ForgeModernPlayPending": 0x10051A,
    "ForgeModernClearTrack": 0x10053C,
    "ForgeModernRouteFade": 0x100552,
    "ForgeModernRouteStop": 0x100562,
    "ForgeModernPause": 0x100572,
    "ForgeModernUnpause": 0x100592,
    "ForgeModernSpeed": 0x1005BA,
    "ForgeModernExtraLife": 0x1005C4,
    "ForgeModernDuckStart": 0x1005CC,
    "ForgeModernDuckService": 0x1005DE,
    "ForgeModernPlaySound": 0x100614,
    "ForgeModernPlaySound2": 0x100638,
    "ForgeModernPauseRequest": 0x100658,
    "ForgeModernUnpauseRequest": 0x10066A,
    "ForgeModernVintReturn": 0x10067C,
    "ForgeModernInit": 0x100692,
    "ForgeModernReset": 0x10069E,
    "ForgeModernRouterEnd": 0x1006C0,
}
ROUTER_END = ROUTER_ADDRESSES["ForgeModernRouterEnd"]
ROUTER_SHA256 = "4fb3350a48a1bf210e740fe694f9b6023240bf8cb6d1ecb95fd2be76b7e60f83"
ROUTINE_SHA256 = {
    "ForgeModernPlayMusic": "1b185c168d72e222ac8300405c41a0629aa1528598cf161e64dc7ff6c0d71cf4",
    "ForgeModernRoute": "62794d0d5ed9db7e19c8fcff70215cf1549c9b7f8208fee8c20b41b027d86477",
    "ForgeModernRequest": "fbc31c5d3386eeca83ae282d306b68d8c17362d80637ae4ba2df12b2c5589e11",
    "ForgeModernDiscardMusic": "dc2ee44ec840b68caf7462330ca11ac17015f913fbca298daca7b1abcd7bbf14",
    "ForgeModernReturn": "1ceeabf0c6a5a30bad12cdac0e3ab015a7188a42e6aebb556aad00bb9cd693ad",
    "ForgeModernComplete": "643b3e1b45b965696d318c3ddaec1a4462f34db526a9b939cf8d9b88f54dcd8f",
    "ForgeModernPlayPending": "b230309fd77d44e3661d3566295843faa1db4ba3ae84712d3ed7b31cec7edc96",
    "ForgeModernClearTrack": "7c297facd3f5b44b52733497b98c94652fc679053d161f51ebd6ea027ebd7542",
    "ForgeModernRouteFade": "4b2dcda8ab2d551db1a725b95ae5201eb354de6e2011988b585d92f022a2ff5c",
    "ForgeModernRouteStop": "1c2076c0537ad794d8e2bc74f5418c50d27e8f0cb54bfeae6f99806cbab26708",
    "ForgeModernPause": "c62e5422a7f76791ae5d3ead6250a99a7563bcf74026191dc4b5de052030416c",
    "ForgeModernUnpause": "e51dd2655f1cd9b0a70ea0a08941020737d7473860240e727a205c4f581525d8",
    "ForgeModernSpeed": "8a2cdfd6f1ef2497d0f8be0a5cdfa53ba16aa8d53381b68d966384f6fb7e8b73",
    "ForgeModernExtraLife": "c05fc470bfb03a986815622e6eea83693ac898cca1e39402c1695228ae9392f0",
    "ForgeModernDuckStart": "592d47281d8ddadf6749185e7d23a86a7681757857aa7dc41bd91a435eb1deab",
    "ForgeModernDuckService": "1a4b2a21fb2022fce793893d5ffc533cddd0780ec51c63191833e7c03462b07e",
    "ForgeModernPlaySound": "90ed6255fe576f794e12151762a1165cd61353b8a51be108bd2b649e472ed38b",
    "ForgeModernPlaySound2": "18f7ece6af74de6556d82de327c498e9db1b0dc9ffe8c768bbd48a8fe3630475",
    "ForgeModernPauseRequest": "14d372f60d1f6641af316a3b5571569d9106167b93e04537e03700cc54a75f85",
    "ForgeModernUnpauseRequest": "523cbe8fb01e46d4c10b108d8e639f48624f47efb790b9df271d895910cf370d",
    "ForgeModernVintReturn": "d658e2dba208c11b60e9797dfc07833bcdfbc74ab394be87f802b235bd5ba214",
    "ForgeModernInit": "5de1f141b8b0ae9fa17d8aa254b785bd3b502976d1887d6b93ba6b627c1b62d8",
    "ForgeModernReset": "4692008d78e22992c6a3f0587c2c8fbe9938f0fce55a9222f8038ce36254b70b",
}
COMPLETION_ADDRESS = 0x100300

# Each hook is checked in full, then restored to its exact stock bytes.
LIVE_HOOKS = {
    0x382: ("ForgeModernInit", "4eb9", "61000dd461000f82"),
    0x45E: ("ForgeModernVintReturn", "4ef9", "52b8fe0c4cdf7fff4e73"),
    0x1370: ("ForgeModernPlaySound", "4ef9", "11c0ffe14e75"),
    0x1376: ("ForgeModernPlaySound2", "4ef9", "11c0ffe24e75"),
    0x13AC: ("ForgeModernPauseRequest", "4eb9", "11fc00feffe0"),
    0x13F2: ("ForgeModernUnpauseRequest", "4eb9", "11fc00ffffe0"),
    0x1406: ("ForgeModernUnpauseRequest", "4eb9", "11fc00ffffe0"),
    0x541A: ("ForgeModernUnpauseRequest", "4eb9", "11fc00ffffe0"),
}


@dataclass(frozen=True)
class LayoutProfile:
    """The two audited Forge layouts; offsets are shared only for identical code."""

    curated: bool
    source_hashes: dict[str, str]
    sound_end: int
    implementation: int
    live_hooks: dict[int, tuple[str, str, str]]
    sax_helper: int
    driver_length: int
    driver_start: int
    driver_limit: int
    compressed_size: int
    loaded_size: int
    loaded_sha256: str
    driver_sha256: str
    handoff_sha256: str
    router_sha256: str
    routine_sha256: dict[str, str]
    stock_size: int
    stock_checksum: str
    stock_masked_sha256: str

    @property
    def delta(self) -> int:
        return self.implementation - IMPLEMENTATION_ADDRESS

    @property
    def implementation_end(self) -> int:
        return IMPLEMENTATION_END + self.delta

    @property
    def handoff(self) -> dict[str, int]:
        return {n: a + self.delta for n, a in HANDOFF_ADDRESSES.items()}

    @property
    def router(self) -> dict[str, int]:
        return {n: a + self.delta for n, a in ROUTER_ADDRESSES.items()}

    @property
    def router_end(self) -> int:
        return ROUTER_END + self.delta

    @property
    def completion(self) -> int:
        return COMPLETION_ADDRESS + self.delta

    @property
    def hook_bytes(self) -> bytes:
        return bytes.fromhex("4ef9") + self.router["ForgeModernPlayMusic"].to_bytes(4, "big") + bytes.fromhex("4e71") * 6

    @property
    def loader_hook(self) -> str:
        return LOADER_HOOK.replace("$EC0DE", f"${self.sax_helper:X}").replace("$EC0E8", f"${self.driver_start:X}")

    @property
    def changed_regions(self) -> tuple[tuple[int, int], ...]:
        regions = ((0x1084, 0x10E0), (self.driver_length, self.driver_length + 2),
                   (self.sax_helper, self.driver_limit))
        # Production's baseline ends before Forge; curated's covers all 2 MiB.
        if self.curated:
            regions += ((self.implementation, self.router_end),)
        return regions


LAYOUT_PROFILES = {
    BuildVariant.PRODUCTION: LayoutProfile(
        False, {"s2.asm": UPSTREAM_S2_SHA256, "s2.constants.asm": UPSTREAM_CONSTANTS_SHA256,
                "s2.sounddriver.asm": UPSTREAM_Z80_SHA256},
        0xFFFEC, IMPLEMENTATION_ADDRESS, LIVE_HOOKS, 0xEC0DE, DRIVER_LENGTH_ADDRESS,
        DRIVER_START, DRIVER_LIMIT, Z80_COMPRESSED_SIZE, Z80_LOADED_SIZE, Z80_SHA256,
        DRIVER_REGION_SHA256, HANDOFF_SHA256, ROUTER_SHA256, ROUTINE_SHA256,
        STOCK_ROM_SIZE, "D951", STOCK_MASKED_SHA256,
    ),
    BuildVariant.BUGFIXED: LayoutProfile(
        True, {
            "s2.asm": "a5e234708be87f5b984d05f6bd4596a28ee792e210822cacd8ed346a9ea8f61f",
            "s2.constants.asm": "e6fac75b24da9ecbd2a11ab7d474a3fe1426afa134ef41d9170202f95e77ac54",
            "s2.sounddriver.asm": "ce96d9dda766fefa33de23ddccea373b58aceb92ec2a91fba30d998105d667a8",
        },
        0x107FEC, 0x108000, {
            0x382: ("ForgeModernInit", "4eb9", "61000dd461000f82"),
            0x45E: ("ForgeModernVintReturn", "4ef9", "52b8fe0c4cdf7fff4e73"),
            0x1370: ("ForgeModernPlaySound", "4ef9", "11c0ffe14e75"),
            0x1376: ("ForgeModernPlaySound2", "4ef9", "11c0ffe24e75"),
            0x13C4: ("ForgeModernPauseRequest", "4eb9", "11fc00feffe0"),
            0x140A: ("ForgeModernUnpauseRequest", "4eb9", "11fc00ffffe0"),
            0x141E: ("ForgeModernUnpauseRequest", "4eb9", "11fc00ffffe0"),
            0x547A: ("ForgeModernUnpauseRequest", "4eb9", "11fc00ffffe0"),
        },
        0xED0DE, 0xED050, 0xED0E8, 0xF5100,
        4011, 0x137A, "f2883990453ba7deedc682b3970be0d2c73fea99a566a30d43362c2769ac7041",
        "b9788df25eb06f84bacdb03b620c256a72001c533c08770faa7a93826ef985e1",
        # Relative branches keep all backend/router bytes identical. The only
        # absolute internal pointer is the separately checked ACK callback.
        HANDOFF_SHA256, ROUTER_SHA256, dict(ROUTINE_SHA256),
        0x200000, "53DB", "1e8d2df3382042f15102491dbfa622e5f3ccd3f47f865af83f8c1a69930b87ad",
    ),
}


def expected_live_hooks(variant: BuildVariant = BuildVariant.PRODUCTION) -> dict[int, bytes]:
    layout = LAYOUT_PROFILES[variant]
    return {address: bytes.fromhex(op) + layout.router[label].to_bytes(4, "big") +
            bytes.fromhex("4e71") * ((len(bytes.fromhex(original)) - 6) // 2)
            for address, (label, op, original) in layout.live_hooks.items()}


def modern_symbols(path: Path) -> dict[str, int]:
    """Read AS's complete listing symbol table (including folded long names)."""
    return {key: int(value, 16) & 0xFFFFFF for key, value in re.findall(
        r"([\w.]+)\s*:\s*([0-9A-F]+) [C\-]", path.read_text(errors="replace"))}


def assembled_modern_driver(path: Path) -> bytes:
    """Join modern AS object records, excluding the earlier Z80 startup stub.

    Current upstream AS splits the driver into two contiguous records. Require
    complete records in order: no overlaps, holes, or unaccounted Z80 payload.
    """
    data = path.read_bytes()
    if data[:2] != b"\x89\x14":
        raise BuildError("Invalid modern AS object header")
    position, output, found = 2, bytearray(), False
    while position < len(data):
        kind = data[position]
        position += 1
        if kind == 0:
            break
        if kind == 0x80:
            position += 3
            continue
        cpu = kind
        if kind == 0x81:
            cpu, _, granularity = data[position:position + 3]
            position += 3
            if granularity != 1:
                raise BuildError("Unsupported modern AS object granularity")
        start = int.from_bytes(data[position:position + 4], "little")
        length = int.from_bytes(data[position + 4:position + 6], "little")
        position += 6
        segment = data[position:position + length]
        position += length
        if len(segment) != length:
            raise BuildError("Truncated modern AS object segment")
        if cpu == 0x51:
            if start == 0:
                if found:
                    raise BuildError("Duplicate modern Z80 driver")
                found = True
            if found:
                if start != len(output):
                    raise BuildError("Noncontiguous modern Z80 driver")
                output.extend(segment)
    if not found:
        raise BuildError("Missing modern Z80 driver")
    return bytes(output)


def verify_modern_driver(
    data: bytes, assembled: bytes | None = None, *, variant: BuildVariant = BuildVariant.PRODUCTION,
) -> dict[str, int | str]:
    layout = LAYOUT_PROFILES[variant]
    from .driver import LOADER_READ, saxman_decode

    helper = layout.handoff["ForgeModernSaxGetByte"]
    if data[helper:helper + len(LOADER_READ)] != LOADER_READ or data.count(LOADER_READ) != 1:
        raise BuildError("Modern loader fix changed or is duplicated")
    if data[layout.sax_helper:layout.driver_start] != bytes.fromhex("4ef9") + helper.to_bytes(4, "big") + bytes.fromhex("4e714e71"):
        raise BuildError("Modern loader trampoline changed")
    length = int.from_bytes(data[layout.driver_length:layout.driver_length + 2], "big")
    if length != layout.compressed_size or layout.driver_start + length > layout.driver_limit:
        raise BuildError("Modern compressed driver exceeds its audited reserved region/length")
    packed = data[layout.driver_start:layout.driver_limit]
    if hashlib.sha256(packed).hexdigest() != layout.driver_sha256:
        raise BuildError("Modern compressed driver/padding differs from audited bytes")
    loaded = saxman_decode(packed[:length])
    if len(loaded) != layout.loaded_size or hashlib.sha256(loaded).hexdigest() != layout.loaded_sha256:
        raise BuildError("Modern loaded Z80 bytes differ from audited driver")
    if assembled is not None and loaded != assembled:
        raise BuildError("Modern loaded Z80 bytes differ from assembler object")
    return {"z80_compressed_bytes": length, "z80_loaded_bytes": len(loaded),
            "z80_loaded_sha256": hashlib.sha256(loaded).hexdigest()}


def _verify_modern(
    path: Path, *, strict_regression: bool = False, variant: BuildVariant = BuildVariant.PRODUCTION,
) -> dict[str, str | int]:
    """Audit the live router, frozen backends, and every unchanged stock byte."""
    from .source import genesis_checksum

    try:
        data = path.read_bytes()
    except OSError as exc:
        raise BuildError(f"Cannot read modern MD+ ROM {path}: {exc}") from exc
    profile = VERIFICATION_PROFILES[variant]
    layout = LAYOUT_PROFILES[variant]
    if len(data) != profile.size:
        raise BuildError(f"Modern MD+ ROM size is {len(data)}, expected {profile.size}")
    stored, calculated = genesis_checksum(data)
    if stored != calculated:
        raise BuildError(f"Modern checksum mismatch: stored {stored:04X}, calculated {calculated:04X}")
    if int.from_bytes(data[0x1A4:0x1A8], "big") != len(data) - 1:
        raise BuildError("Modern ROM header end does not cover the appended code and padding")
    signatures = {
        "overlay_address_signatures": data.count(bytes.fromhex("0003f7fa")),
        "command_address_signatures": data.count(bytes.fromhex("0003f7fe")),
        "command_write_signatures": sum(data.count(bytes.fromhex("33fc") + command.to_bytes(2, "big")
                                                     + bytes.fromhex("0003f7fe")) for _, command in COMMANDS),
        "overlay_open_signatures": data.count(bytes.fromhex("33fccd540003f7fa")),
        "overlay_close_signatures": data.count(bytes.fromhex("33fc00000003f7fa")),
    }
    if signatures != {
        "overlay_address_signatures": 42, "command_address_signatures": 21,
        "command_write_signatures": 21, "overlay_open_signatures": 21,
        "overlay_close_signatures": 21,
    }:
        raise BuildError(f"Unexpected MD+ signature in modern MD+: {signatures}")
    # Both audited final banks end in the last SFX's SMPS stop byte. Check the
    # observed end and gap explicitly, in addition to the full baseline digest.
    if (not 0 < layout.sound_end < layout.implementation
            or data[layout.sound_end - 1] != 0xF2
            or any(data[layout.sound_end:layout.implementation])):
        raise BuildError("Modern sound-data end or trailing bank padding changed")
    if data[PLAY_MUSIC_ADDRESS:PLAY_MUSIC_ADDRESS + 18] != layout.hook_bytes or data.count(layout.hook_bytes) != 1:
        raise BuildError("Modern PlayMusic absolute jump/footprint changed or is duplicated")
    if data[layout.implementation:layout.implementation + 18] != NATIVE_PLAY_MUSIC:
        raise BuildError("Modern native mailbox implementation changed")
    extension = data[layout.implementation:layout.implementation_end]
    if extension != expected_modern_extension():
        raise BuildError("Modern backend differs from exact audited instructions/transactions")
    callback = bytes.fromhex("4ef9") + layout.router["ForgeModernComplete"].to_bytes(4, "big")
    if data[layout.completion:layout.completion + 6] != callback:
        raise BuildError("Modern ACK completion callback changed")
    handoff = bytearray(data[layout.implementation_end:layout.router["ForgeModernPlayMusic"]])
    relative = layout.completion - layout.implementation_end
    handoff[relative:relative + 6] = bytes.fromhex("4238f1134e75")
    if hashlib.sha256(handoff).hexdigest() != layout.handoff_sha256:
        raise BuildError("Modern handoff differs from audited instructions")
    input_hook = bytes.fromhex("4ef9") + layout.handoff["ForgeModernInput"].to_bytes(4, "big")
    if data[0x1084:0x10E0] != input_hook + bytes(0x10E0 - 0x1084 - len(input_hook)):
        raise BuildError("Modern input trampoline/footprint changed")
    for address, expected in expected_live_hooks(variant).items():
        if data[address:address + len(expected)] != expected:
            raise BuildError(f"Modern live hook/footprint changed at {address:06X}")
    router = data[layout.router["ForgeModernPlayMusic"]:layout.router_end]
    if hashlib.sha256(router).hexdigest() != layout.router_sha256:
        raise BuildError("Modern live router differs from audited instructions")
    routines = list(layout.router.items())
    for (name, start), (_, end) in zip(routines[:-1], routines[1:], strict=True):
        if hashlib.sha256(data[start:end]).hexdigest() != layout.routine_sha256[name]:
            raise BuildError(f"Modern routine differs from audited instructions: {name}")
    driver = verify_modern_driver(data, variant=variant)
    if any(data[layout.router_end:]):
        raise BuildError("Unexpected data after modern implementation (expected zero padding)")

    # Reconstruct the stock hook/header, then normalize only the EXACTLY audited
    # input/loader/driver regions above. Require the digest of all remaining
    # stock bytes, including both sides of the driver growth padding. No broad
    # range is ignored: each normalized byte was already checked independently.
    stock = bytearray(data[:layout.stock_size])
    stock[PLAY_MUSIC_ADDRESS:PLAY_MUSIC_ADDRESS + 18] = NATIVE_PLAY_MUSIC
    for address, (_, _, original) in layout.live_hooks.items():
        baseline = bytes.fromhex(original)
        stock[address:address + len(baseline)] = baseline
    stock[0x18E:0x190] = bytes.fromhex(layout.stock_checksum)
    stock[0x1A4:0x1A8] = (layout.stock_size - 1).to_bytes(4, "big")
    for start, end in layout.changed_regions:
        stock[start:end] = bytes(end - start)
    if hashlib.sha256(stock).hexdigest() != layout.stock_masked_sha256:
        raise BuildError("Modern MD+ changed bytes outside the audited stock regions")
    result = {
        "size": len(data), "header_checksum": f"{stored:04X}",
        "md5": hashlib.md5(data, usedforsecurity=False).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "play_music_address": f"{PLAY_MUSIC_ADDRESS:06X}",
        "implementation_address": f"{layout.implementation:06X}",
        "native_implementation_end": f"{(DISPATCH_ADDRESS + layout.delta):06X}",
        "dispatch_address": f"{(DISPATCH_ADDRESS + layout.delta):06X}",
        "implementation_end": f"{layout.implementation_end:06X}",
        "extension_sha256": hashlib.sha256(extension).hexdigest(),
        "command_transactions": 21,
        "handoff_end": f"{layout.router['ForgeModernPlayMusic']:06X}",
        "router_address": f"{layout.router['ForgeModernPlayMusic']:06X}",
        "router_end": f"{layout.router_end:06X}",
        "router_sha256": hashlib.sha256(router).hexdigest(),
        **driver, **signatures,
    }
    if strict_regression and (
        result["header_checksum"], result["md5"], result["sha256"]
    ) != (profile.checksum, profile.md5, profile.sha256):
        raise BuildError(f"Modern ROM differs from the audited variant target: {result}")
    return result


def verify_modern(
    path: Path, *, strict_regression: bool = False, variant: BuildVariant = BuildVariant.PRODUCTION,
) -> dict[str, str | int]:
    """Verify a selected ROM and retain the underlying diagnostic on failure."""
    try:
        return _verify_modern(path, strict_regression=strict_regression, variant=variant)
    except BuildError as exc:
        raise BuildError(f"{variant.value.capitalize()} verification failed for {path}: {exc}") from exc


def build_modern(
    output: Path | None = None, *, variant: BuildVariant = BuildVariant.PRODUCTION,
) -> dict[str, str | int]:
    output = output or variant.rom_path
    # A custom output must not defeat flavour isolation, including via the
    # historical Production symlink or a path inside the other prepared tree.
    resolved = output.resolve()
    for other in BuildVariant:
        if other is variant:
            continue
        reserved = [other.rom_path]
        if other is BuildVariant.PRODUCTION:
            reserved.append(MODERN_ROM_PATH)
        if (resolved.is_relative_to(other.prepared_dir.resolve())
                or any(resolved == path.resolve() or
                       (output.exists() and path.exists() and output.samefile(path)) for path in reserved)):
            raise BuildError(f"ROM output belongs to {other.value}: {output}")
    lua = require_program("lua")
    run([lua, "-e", 'local major, minor = _VERSION:match("(%d+)%.(%d+)"); '
         'assert(tonumber(major) > 5 or (tonumber(major) == 5 and tonumber(minor) >= 3), '
         '"Modern MD+ build requires Lua 5.3 or newer")'])
    prepared_dir = variant.prepared_dir
    preparation = prepare_modern(variant=variant)
    run([lua, "modern_build.lua"], cwd=prepared_dir)
    built = prepared_dir / "s2built.bin"
    result = verify_modern(built, strict_regression=True, variant=variant)
    verify_modern_driver(built.read_bytes(), assembled_modern_driver(prepared_dir / "forge-s2.p"), variant=variant)
    symbols = modern_symbols(prepared_dir / "s2.lst")
    layout = LAYOUT_PROFILES[variant]
    for name, address in (layout.handoff | layout.router |
                          {n: a for n, (a, _) in RAM_STATE.items()}).items():
        if symbols.get(name) != address:
            raise BuildError(f"Modern audited symbol moved: {name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, output)
    if variant is BuildVariant.PRODUCTION and output == ROM_PATH:
        # Preserve the old development filename without a second ROM copy.
        MODERN_ROM_PATH.unlink(missing_ok=True)
        MODERN_ROM_PATH.symlink_to(ROM_PATH.name)
    return {**preparation, **result}
