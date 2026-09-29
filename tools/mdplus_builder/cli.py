from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .audio import (
    check_ffmpeg_audio_capabilities,
    convert_audio_file,
    detect_loops,
    prepare_audio,
    score_loop,
    validate_manifest,
    validate_wave,
)
from .common import (
    BUILD,
    DEFAULT_MANIFEST,
    DIST,
    BuildError,
    crc32,
    require_program,
)
from .modern import bootstrap_modern, build_modern, build_stock_modern, prepare_modern, verify_modern
from .package import assemble, cue_text
from .variants import BuildVariant

CLEAN_ROM_REVISIONS = {
    "24AB4C3A": "World Rev 0",
    "7B905383": "World Rev 1",
}


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _clean_rom_revision(value: str) -> str:
    try:
        return CLEAN_ROM_REVISIONS[value]
    except KeyError as exc:
        expected = ", ".join(
            f"{crc} ({revision})"
            for crc, revision in CLEAN_ROM_REVISIONS.items()
        )
        raise BuildError(
            f"CRC32 is {value}; expected one of: {expected}"
        ) from exc


def _add_variant(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--bugfixed", dest="variant", action="store_const", const=BuildVariant.BUGFIXED,
        default=BuildVariant.PRODUCTION,
        help="select the Bugfixed flavour (currently byte-identical to Production)",
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="sonic2-mdplus",
        description="Build legal, reproducible Sonic the Hedgehog 2 MD+ variants from user-supplied inputs.",
    )
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="check required host programs")

    p = commands.add_parser("bootstrap", help="fetch pinned production s2disasm source")
    p.add_argument("--local-source", type=_path, help="clone the Sonic source from an existing local checkout")

    p = commands.add_parser("bootstrap-modern", help="compatibility alias for bootstrap")
    p.add_argument("--local-source", type=_path, help="clone s2disasm from an existing local checkout")
    commands.add_parser("build-stock-modern", help="build and verify stock REV01 with upstream Lua (no MD+)")

    commands.add_parser("prepare-modern", help="compatibility alias for prepare-source")
    commands.add_parser("build-modern", help="compatibility alias for build-rom (same canonical output)")

    p = commands.add_parser("prepare-source", help="prepare the pinned MD+ source")
    _add_variant(p)

    p = commands.add_parser("build-rom", help="prepare, build and verify the REV01 MD+ ROM")
    _add_variant(p)
    p.add_argument("--output", type=_path, help="ROM output (default: selected flavour's build path)")

    p = commands.add_parser("verify-rom", help="verify a generated ROM's checksum and MD+ signatures")
    p.add_argument("rom", type=_path)
    p.add_argument("--strict-regression", action="store_true")
    _add_variant(p)

    p = commands.add_parser("verify-clean-rom", help="identify a supported clean Sonic 2 World ROM revision")
    p.add_argument("rom", type=_path)

    p = commands.add_parser("validate-manifest", help="validate track definitions and print the CUE")
    p.add_argument("--manifest", type=_path, default=DEFAULT_MANIFEST)

    p = commands.add_parser("prepare-audio", help="convert enabled user WAVs to MD+ format")
    p.add_argument("--manifest", type=_path, default=DEFAULT_MANIFEST)
    p.add_argument("--input-dir", type=_path, required=True)
    p.add_argument("--output-dir", type=_path, default=BUILD / "audio")

    p = commands.add_parser("convert-audio", help="normalize one WAV for loop analysis")
    p.add_argument("input", type=_path)
    p.add_argument("output", type=_path)
    p.add_argument("--end-sector", type=int)
    p.add_argument("--speed", type=float, default=1.0)

    p = commands.add_parser("validate-audio", help="validate PCM format and optional sector length")
    p.add_argument("wav", type=_path)
    p.add_argument("--end-sector", type=int)

    p = commands.add_parser("detect-loop", help="rank sector-aligned repeated-boundary candidates")
    p.add_argument("wav", type=_path)
    p.add_argument("--start-range", required=True, help="candidate start range in seconds, START:END")
    p.add_argument("--end-range", required=True, help="candidate end range in seconds, START:END")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--window-ms", type=int, default=300)

    p = commands.add_parser("validate-loop", help="score a defined sector-aligned loop boundary")
    p.add_argument("wav", type=_path)
    p.add_argument("--start-sector", type=int, required=True)
    p.add_argument("--end-sector", type=int, required=True)
    p.add_argument("--window-ms", type=int, default=300)
    p.add_argument("--max-score", type=float, help="fail when normalized RMS score exceeds this value")

    p = commands.add_parser("package", help="assemble the MiSTer-ready directory")
    _add_variant(p)
    p.add_argument("--manifest", type=_path, default=DEFAULT_MANIFEST)
    p.add_argument("--rom", type=_path, help="verified ROM to package (default: selected flavour's build path)")
    p.add_argument("--audio-dir", type=_path, default=BUILD / "audio")

    p = commands.add_parser("all", help="bootstrap, convert, build, prepare audio, and package")
    _add_variant(p)
    p.add_argument("--manifest", type=_path, default=DEFAULT_MANIFEST)
    p.add_argument("--input-dir", type=_path, required=True)
    p.add_argument("--local-source", type=_path)

    commands.add_parser("clean", help="remove ignored build and dist outputs")
    return root


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "doctor":
            result: dict[str, object] = {
                name: require_program(name) for name in ("git", "make", "gcc", "python3", "lua")
            }
            capabilities = check_ffmpeg_audio_capabilities()
            result["ffmpeg"] = capabilities.pop("ffmpeg")
            result["ffprobe"] = capabilities.pop("ffprobe")
            result["audio_conversion"] = capabilities
            _print_json(result)
        elif args.command in {"bootstrap", "bootstrap-modern"}:
            bootstrap_modern(local_source=args.local_source)
        elif args.command == "build-stock-modern":
            _print_json(build_stock_modern())
        elif args.command == "prepare-modern":
            _print_json(prepare_modern())
        elif args.command == "prepare-source":
            _print_json(prepare_modern(variant=args.variant))
        elif args.command == "build-modern":
            _print_json(build_modern())
        elif args.command == "build-rom":
            _print_json(build_modern(args.output, variant=args.variant))
        elif args.command == "verify-rom":
            _print_json(verify_modern(args.rom, strict_regression=args.strict_regression, variant=args.variant))
        elif args.command == "verify-clean-rom":
            value = crc32(args.rom)
            revision = _clean_rom_revision(value)
            _print_json({"path": str(args.rom), "crc32": value, "revision": revision})
        elif args.command == "validate-manifest":
            manifest = validate_manifest(args.manifest)
            print(cue_text(manifest), end="")
        elif args.command == "prepare-audio":
            _print_json(prepare_audio(args.manifest, args.input_dir, args.output_dir))
        elif args.command == "convert-audio":
            _print_json(
                convert_audio_file(
                    args.input,
                    args.output,
                    end_sector=args.end_sector,
                    speed=args.speed,
                )
            )
        elif args.command == "validate-audio":
            _print_json(validate_wave(args.wav, end_sector=args.end_sector))
        elif args.command == "detect-loop":
            rows = detect_loops(
                args.wav,
                args.start_range,
                args.end_range,
                top=args.top,
                window_ms=args.window_ms,
            )
            _print_json(
                [
                    {
                        "score": round(score, 8),
                        "start_sector": start,
                        "start_seconds": start / 75,
                        "end_sector": end,
                        "end_seconds": end / 75,
                        "loop_seconds": (end - start) / 75,
                    }
                    for score, start, end in rows
                ]
            )
        elif args.command == "validate-loop":
            score = score_loop(
                args.wav,
                args.start_sector,
                args.end_sector,
                window_ms=args.window_ms,
            )
            _print_json({"normalized_rms_score": score, "lower_is_better": True})
            if args.max_score is not None and score > args.max_score:
                raise BuildError(f"Loop score {score:.8f} exceeds limit {args.max_score:.8f}")
        elif args.command == "package":
            print(assemble(args.manifest, rom_path=args.rom, audio_dir=args.audio_dir, variant=args.variant))
        elif args.command == "all":
            bootstrap_modern(local_source=args.local_source)
            build_modern(variant=args.variant)
            prepare_audio(args.manifest, args.input_dir)
            print(assemble(args.manifest, variant=args.variant))
        elif args.command == "clean":
            for directory in (BUILD, DIST):
                if directory.exists():
                    shutil.rmtree(directory)
                    print(f"removed {directory}")
        else:
            raise AssertionError(args.command)
        return 0
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
