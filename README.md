# Sonic 2 MD+ Forge

[![CI](https://github.com/lloydsmart/sonic2-mdplus-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/lloydsmart/sonic2-mdplus-forge/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/lloydsmart/sonic2-mdplus-forge)](https://github.com/lloydsmart/sonic2-mdplus-forge/releases)
[![License](https://img.shields.io/github/license/lloydsmart/sonic2-mdplus-forge)](LICENSE)

Sonic 2 MD+ Forge is a reproducible build system for creating MD+ variants of
Sonic the Hedgehog 2 for the Mega Drive. It combines external soundtrack
arrangements with original Mega Drive audio where appropriate. The first and
currently supported soundtrack is Addryu's Sonic the Hedgehog 2 Mega-CD Remix;
the architecture is intended to allow additional soundtrack variants in future,
but no other profiles are currently supported.

The project does **not** contain or distribute a ROM, Sega assets, the Addryu
soundtrack, or proprietary binaries.

## Support Addryu — buy the soundtrack

**To use this builder, buy Addryu's
[Sonic the Hedgehog 2 [Mega-CD Remix] album on Bandcamp](https://addryu.bandcamp.com/album/sonic-the-hedgehog-2-mega-cd-remix)
and download your purchase in WAV format.** Please support the artist whose
work makes this soundtrack possible.

We do not condone unauthorized distribution of Addryu's work. Do not share or
upload the purchased tracks, converted or trimmed WAVs, or a finished package
containing them. Purchasing the album does not grant permission to redistribute
it, and this project's GPL license does not cover the music. The builder does
not download audio; you supply your own legitimately purchased files.

## Build status

The normal build uses current `sonicretro/s2disasm` REV01 with Forge's MD+
implementation. Its required Stage 5 MiSTer FPGA hardware gate has passed:
boot, native title/menu audio, Addryu transitions, ordinary SFX, pause/resume,
speed shoes, extra life, warm reset, level select, and Death Egg/ending were
verified. All 16 Addryu cues and the manifest loops retain their earlier
hardware verification. The optional missing-WAV robustness test was not run.

The current release is **v3.0.1**. Production remains the unchanged default,
using the exact hardware-tested Stage 5 ROM. Version 2.0.0 made it the default;
v3.0.0 retired the public legacy fallback interfaces. This patch release freezes
the merged selective Bugfixed corrections without changing the public interface.
See the [v3.0.1 release record](docs/releases/v3.0.1.md).

Bugfixed integrates the frozen [curated source policy](docs/BUGFIXED.md) with
Forge MD+, using isolated outputs and its own audited ROM identity and layout.
The released v3.0.1 Bugfixed identity `C145` / `f33a1946...` adds only Spin
Dash Release and Credits audio-data corrections plus the selected EHZ2 walls/
pathswapper, ARZ2 progression pathswapper and WFZ1 diagonal conveyor correction.
ARZ2's bubble generator is deliberately retained. The exact identity is
**hardware-qualified on MiSTer Mega Drive core `26.06.03` for the targeted
level-data and regression sanity scope**; no new full-game 1P playthrough or
comprehensive 2P soak is claimed.

The v3.0.0 Obj82-corrected `d1668976...` and intermediate selective-audio
`b04c2fd3...` identities retain their own historical hardware evidence. Global
music/SFX data fixes, Sky Chase/Death Egg audio-data changes, Z80 driver fixes,
the alternate 2P sprite mechanism and every other Fixed Files substitution
remain excluded. CPZ/DEZ door replacements and OOZ2 push springs remain deferred.
Production retains its exact Stage 5 identity.

## What the build does

1. Fetches [`sonicretro/s2disasm`](https://github.com/sonicretro/s2disasm), pinned
   to `380f37a731bfc720bb0371a35a593184a7ec5e43` in `config/dependencies.json`.
2. Prepares a disposable source clone and builds REV01 with upstream's Lua
   build and native tools. Dependency source checkouts remain inputs.
3. Adds the verified MD+ implementation. Sixteen fixed Addryu cues use MD+;
   other music and all SFX use the native driver. Every MD+ command uses a
   short-lived overlay transaction after Sonic's startup checksum.
4. Verifies the ROM's checksum, exact instruction signatures, loaded Z80
   driver, size, MD5 and SHA-256 against the selected variant's audited baseline.
5. Normalizes user-supplied WAVs to 44.1 kHz signed 16-bit stereo PCM, trims
   them on exact 75 Hz sector boundaries, validates them, and generates a CUE.
6. Creates an ignored `dist/` package ready to copy to MiSTer.

## Prerequisites

The supported host is a current Debian-like Linux system, including RetroNAS:

```sh
sudo apt install git make gcc python3 lua5.3 ffmpeg
```

Lua 5.3 or newer must be available as `lua`. No third-party Python packages are
required for normal builds. Network access fetches one pinned source dependency
for the production build. The repository supplies tooling and metadata, not a
ROM or soundtrack. Audio must be supplied locally from your lawful purchase.

## Quick start

Clone this repository, then place your lawfully obtained Addryu WAVs under an
ignored directory:

```text
inputs/audio/
  Addryu - Sonic the Hedgehog 2 -Mega-CD Remix- - 01 Emerald Hill Zone.wav
  Addryu - Sonic the Hedgehog 2 -Mega-CD Remix- - 02 Chemical Plant Zone.wav
  Addryu - Sonic the Hedgehog 2 -Mega-CD Remix- - 03 Aquatic Ruin Zone.wav
  ... (all 16 album WAVs listed in config/tracks.json)
```

Run:

```sh
make doctor
make all INPUT_DIR="$PWD/inputs/audio"
```

The default manifest builds all 16 hardware-verified Addryu cues at:

```text
dist/Sonic 2 - Addryu Mega-CD Remix MD+/
  Sonic 2 - Addryu Mega-CD Remix MD+.md
  Sonic 2 - Addryu Mega-CD Remix MD+.cue
  track03.wav
  track05.wav
  track07.wav
  track08.wav
  track09.wav
  track10.wav
  track11.wav
  track12.wav
  track13.wav
  track14.wav
  track15.wav
  track26.wav
  track27.wav
  track28.wav
  track29.wav
  track31.wav
  SHA256SUMS.json
```

Copy that directory to MiSTer's Mega Drive library and launch the `.md` file
with a Main/MegaDrive core version that supports MD+. Do not launch the CUE
directly.

## Repeatable commands

Run the stages independently:

```sh
make bootstrap
python3 -m tools.mdplus_builder validate-manifest --manifest config/tracks.json
make source
make rom
make audio INPUT_DIR="$PWD/inputs/audio"
make package
```

`make rom` prepares fresh committed input each time and writes the canonical
`build/sonic2-mdplus.md`. `make source` is useful for inspecting generated source
in `build/prepared-modern/`, but a separate preparation is not required before
building. Edits to that generated directory are replaced on the next build.

`make package` uses the canonical ROM and prepared `build/audio/` WAVs. It
requires an exact production ROM match, so an old legacy ROM left under the
canonical name is rejected; run `make rom` after upgrading. The Addryu manifest,
track filenames, loop coordinates, matching ROM/CUE basenames and package
layout are unchanged. `SHA256SUMS.json` covers every packaged ROM, WAV and CUE.

To use a local clone containing the exact current source pin:

```sh
python3 -m tools.mdplus_builder bootstrap --local-source "$HOME/src/s2disasm"
```

The builder clones committed input; it does not modify that local checkout.
The module CLI is also available as `sonic2-mdplus` after installation.
Run `make help` or add `--help` to an individual CLI command for its options.

## Bugfixed build flavour

Both flavours share the immutable pinned `build/source-modern/` dependency and
all current MD+ source transformations. They prepare and build independently:

| Output | Production (default) | Bugfixed |
| --- | --- | --- |
| Prepared source | `build/prepared-modern/` | `build/prepared-bugfixed/` |
| ROM | `build/sonic2-mdplus.md` | `build/sonic2-mdplus-bugfixed.md` |
| Package | `dist/Sonic 2 - Addryu Mega-CD Remix MD+/` | `dist/Sonic 2 - Addryu Mega-CD Remix MD+ (Bugfixed)/` |

Build or package Bugfixed with:

```sh
make bootstrap
make source-bugfixed
make rom-bugfixed
python3 -m tools.mdplus_builder verify-rom \
  --bugfixed --strict-regression build/sonic2-mdplus-bugfixed.md
make package-bugfixed
# Or run all stages with locally purchased audio:
make all-bugfixed INPUT_DIR="$PWD/inputs/audio"
```

The CLI adds `--bugfixed` to `prepare-source`, `build-rom`, `verify-rom`,
`package` and `all`. Omitting it selects Production. Compatibility aliases
remain Production-only; the historical `build/sonic2-modern-mdplus.md` symlink
still points only to Production. The separate `build-stock-bugfixed` target is
a development reference with no MD+ support or package command.

Bugfixed packaging reuses `build/audio/` and the unchanged track manifest.
Its ROM and CUE basenames are both
`Sonic 2 - Addryu Mega-CD Remix MD+ (Bugfixed)`. The two package directories
coexist, as do both prepared directories and ROMs. Custom `build-rom --output`
paths cannot target the other flavour's reserved ROM or prepared directory.
`clean` still removes all ignored build and distribution outputs.

Internally, `BuildVariant` selects isolated paths, package naming, strict ROM
identity and an audited layout profile. Production adapts pristine pinned REV01.
Bugfixed first applies the authoritative `bugfixed.apply_policy()` transformation,
checks all eight post-policy source/object hashes, then applies the shared Forge adapter.
Its backend starts at `$108000`, after the curated sound banks; Production
stays at `$100000`. Each profile checks its own hooks, loader, compressed driver
and reference baseline. Both preserve the same Forge RAM allocation and all
21 short-lived MD+ command transactions, activated only after startup checksum.

Released v3.0.1 Bugfixed MD+ is 2,097,152 bytes, checksum `C145`, MD5
`50e81d88e257f8d14608e57801b628c5`, SHA-256
`f33a1946a609b8045bb56ffce2aba05196190965fed6ddf5f8eb3b80c52a0c52`.
Its approved level-data edits add 24 uncompressed bytes, absorbed by existing
alignment; sound, Z80, Forge and RAM stay fixed. Software and clean Linux
validation pass; targeted MiSTer qualification on core `26.06.03` also passed
for the selected EHZ2 fixes and boss/capsule progression, ARZ2 loop progression
and retained bubble generator, and WFZ diagonal conveyor (object `$72`). Native
SFX over MD+, pause/unpause, temporary native music and MD+ restoration, and
reset passed, with no obvious object corruption observed. This adds targeted
evidence for the level-data changes; no new full-game playthrough or comprehensive
retest of previous Bugfixed features is claimed. See the
[level-data audit and hardware results](docs/BUGFIXED.md#targeted-level-data-mister-hardware-qualification).

The historical hardware-qualified pre-level-data Bugfixed baseline has checksum
`6AD6`, MD5
`ef060d788f896099075e370195120ff2`, SHA-256
`b04c2fd39e804719db599cca014966b19f07b16140688ee265c1dc759cb2212b`.
This exact post-v3 candidate passed targeted MiSTer hardware qualification on
Mega Drive core `26.06.03`. Repeated Spin Dash releases and complete Credits
playback sounded normal; extensive native SFX, MD+/native ownership transitions,
invincibility, repeated pause/unpause, both Emerald Hill acts and boss, part of
Chemical Plant Act 1, the Death Egg sequence through the ending transition and
level select passed. No hardware regression was observed. Vanilla driver
overflow already masks Spin Dash's malformed `$90` transpose; hardware confirms
no regression while the source/compiled audit establishes the data correction.
No new full-game playthrough or comprehensive 2P soak is claimed.
Exactly Spin Dash Release
transpose and Credits pitch data are corrected; the obsolete Credits compensation
is neutralised without moving data. `FixMusicAndSFXDataBugs` remains globally zero.
Sky Chase, Death Egg and Z80 driver fixes remain excluded. See the
[compiled audio audit and hardware results](docs/BUGFIXED.md#post-v3-selective-audio-data-candidate).
The revised curated policy retains upstream's ARZ Rising Pillar culling fix
(explicit height, width `$1C`, display radius `$20`) while subtracting eight
pixels only from its vertical collision half-height, restoring retail jumps at
every rising stage. This narrowly corrects the gameplay regression found on
MiSTer. Production, MD+ routes, WAV processing and loop policy remain unchanged.

Obj82 has a separate correction discovered through source/compiled analysis: upstream enlarges
its pillar display radius `$30->$32` and compensates walking collision `d3`,
but jumping collision `d2` remains `$32`. Forge subtracts two from `d2` before
deriving `d3`, retaining `$32` rendering/culling and retail collision `$30/$31`.
The change is 18 bytes before and after, with no downstream address movement.
The released v3 `d1668976...` ROM passed targeted MiSTer ARZ testing: Act 1 subtype
`$10` and Act 2 subtype `$11` jump/contact, standing, walking, side collision and
culling checks, plus Act 2 waiting/falling and standing while falling. ARZ MD+
playback/looping, pause/unpause, invincibility recovery and Act 2 boss-music
transition/restoration also passed, alongside an Act 1 Obj2B regression check
of standing on top while the pillar rises. No hardware regression was observed.

The preceding Obj2B-corrected MD+ SHA-256
`f80d983bdc44d5d89f3f7556e644a5b0ff5bf6e519ddacf0a3df73d4406449dc`
passed targeted ARZ and EHZ 2P tests on core `26.06.03`. The earlier
`8101cf55...` identity passed a full 1P playthrough and comprehensive 2P soak,
with the Obj2B pillar issue reported. Those remain historical integration
evidence. The released v3 `d1668976...` qualification follows the local size-neutral
Obj82 correction and successful targeted ARZ tests; it does not claim another
full 1P playthrough or comprehensive 2P soak. The
[concrete ARZ placements](docs/BUGFIXED.md#obj82-hardware-test-placements)
remain documented for repeat testing.

See [software validation and layout evidence](docs/BUGFIXED.md#forge-md-software-validation)
for source integrity, exact hooks and bank relocations, and
[MiSTer qualification evidence](docs/BUGFIXED.md#mister-hardware-qualification-and-historical-evidence)
for the hardware results and their exact ROM identities.

## Earlier implementations

Earlier Forge releases used `msu-md-sonic2` and a separately built ASL assembler.
That implementation and its fallback commands are retired. Git history and the
existing `v2.0.0` tag preserve the final legacy-capable state; historical release
and migration documents describe those earlier versions.

## Compatibility and development commands

The existing `bootstrap-modern`, `prepare-modern` and `build-modern` Make/CLI
commands remain aliases for production bootstrap, preparation and building.
`build-modern` writes `build/sonic2-mdplus.md`; the old
`build/sonic2-modern-mdplus.md` name is a relative symlink to that same file.
There is no separate modern candidate or second ROM copy.

`make build-stock-modern` remains an independent audit of untouched upstream
REV01 after bootstrap. It builds in a disposable clone and verifies:

- Output: `build/sonic2-stock-modern.md`
- Size: `1,048,576` bytes; checksum: `D951`
- MD5: `9feeb724052c39982d432a7851c98d3e`
- SHA-256: `193bc4064ce0daf27ea9e908ed246d87ec576cc294833badebb590b6ad8e8f6b`

`make build-stock-bugfixed` uses the same bootstrapped dependency to build the
curated no-MD+ reference. It publishes `build/sonic2-stock-bugfixed.md` and
`build/sonic2-stock-bugfixed.lst`, enforcing a separate strict identity.
See [Bugfixed source policy](docs/BUGFIXED.md) for inclusions, exclusions,
audited hashes and integration constraints. Neither stock output is selected
for packaging.
Internal `hybrid_modern*.asm` names and `source_modern` configuration retain
historical names to keep maintenance changes small. See the
[Stage 6 interface audit](docs/STAGE6_CUTOVER.md),
[production architecture](docs/MODERN_STAGE5.md) and
[preceding handoff stage](docs/MODERN_STAGE4.md) for development details.

## Audio normalization policy

Supply the original WAV files from your lawful soundtrack download; manual
sample-rate or bit-depth conversion is not required. The builder probes each
source with FFprobe and normalizes it to the MD+ output format.

Native 44.1 kHz, signed 16-bit stereo PCM WAVs use a sample-preserving copy and
trim path, without resampling or dithering. Other sample rates are converted
once with FFmpeg's SoX Resampler at precision 33. Reduction to signed 16-bit
PCM, including conversion after a speed change, uses explicit high-pass
triangular dithering. Expanding lower-bit integer PCM does not add dither. Mono
input is expanded by copying each final mono sample exactly to left and right
with no gain change; input with more than two channels is rejected rather than
applying an unspecified downmix. Source input is intentionally WAV-only; other
containers are rejected rather than treated as an implicit compatibility
promise.

All trimming and sector calculations occur after conversion in the final
44.1 kHz domain. Without an explicit end sector, only complete 588-frame CD
sectors are retained and the incomplete trailing fragment is reported.

## ROM verification

The source build is the authoritative path; a clean cartridge ROM is not used
as build input. If you want to confirm the provenance of your own dump:

```sh
python3 -m tools.mdplus_builder verify-clean-rom \
  "/path/to/Sonic The Hedgehog 2 (World).md"
```

`verify-clean-rom` recognises both supported canonical World revisions:
Rev 0 (`24AB4C3A`) and Rev 1 (`7B905383`). Generated ROM verification is
stricter:

```sh
python3 -m tools.mdplus_builder verify-rom \
  --strict-regression build/sonic2-mdplus.md
```

The production build and packaging enforce the exact Stage 5 identity:

- Size: `2,097,152` bytes; Mega Drive checksum: `BE41`
- MD5: `9eb40c0601a7c424a0d1ce168b5f40f2`
- SHA-256: `bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`
- 21 complete MD+ command transactions; unchanged Stage 3 backend and Stage 4 Z80

`verify-rom` defaults to Production; `--bugfixed` selects its independent
profile and exact Bugfixed identity documented above. Strict verification and
packaging reject stock ROMs and ROMs from earlier implementations.

## Adding tracks and loop points

Edit a working copy of `config/tracks.json`; do not guess loop values. The
manifest refuses to build an enabled looping track without valid start/end
sectors. An optional `trim_start_sector` removes whole CD sectors from the
start of the processed 44.1 kHz audio before the output WAV is written; loop
start/end sectors remain relative to the generated WAV after that trim. See
[docs/TRACKS.md](docs/TRACKS.md) for candidate
detection, sector/sample arithmetic, speed-shoes tracks, listening tests, and
MiSTer verification.

## Limitations

The [sixteen Addryu cues](docs/TRACKS.md#fixed-rom-routing) are fixed in the ROM,
independent of manifest flags, CUE contents, and files on disk. Missing WAVs for
those cues are incomplete-package errors; they never select native music.
The default package includes all sixteen Addryu-owned cues, each verified on
MiSTer hardware.

Unarranged cues, including title/options, bosses, invincibility, drowning, act
clear, ending and credits, use the original Sonic 2 soundtrack. No second
soundtrack or conversion of native music to WAV is needed. MD+ speed variants
are disabled: speed shoes change physics while Addryu music keeps playing at
normal speed. Native speed controls retain the original driver behavior.

See [production architecture](docs/MODERN_STAGE5.md) for queue semantics,
handoff ordering, RAM allocation and hardware coverage limits. The
[earlier architecture](docs/HYBRID_AUDIO.md) is retained as a historical record.

## Validation and clean Linux regression

Install development checks if needed:

```sh
python3 -m venv build/emulation-venv
build/emulation-venv/bin/pip install -e '.[lint,emulation]'
npm ci --ignore-scripts
```

Run the repository checks (put the virtual environment on PATH for Ruff):

```sh
PATH="$PWD/build/emulation-venv/bin:$PATH" ruff check .
npm run lint:markdown
python3 -m compileall -q tools tests
python3 -m unittest discover -s tests -v
python3 -m tools.mdplus_builder validate-manifest --manifest config/tracks.json
git diff --check
```

From a fresh checkout, with no `build/` or `dist/` outputs, repeat the quick start
using your existing lawful audio input directory. `make all` fetches the source,
regenerates the ROM and audio, and creates the complete package. For example,
from a checkout containing committed changes:

```sh
git clone --no-hardlinks . build/clean-linux
cd build/clean-linux
make doctor
python3 -m tools.mdplus_builder validate-manifest --manifest config/tracks.json
make all INPUT_DIR=/absolute/path/to/your/purchased/audio
python3 -m tools.mdplus_builder verify-rom --strict-regression build/sonic2-mdplus.md
```

That disposable checkout has its own `build/` and `dist/`; source and generated
outputs from the original checkout are not reused. For uncommitted development,
copy all tracked and nonignored new files into a disposable directory instead.
Keep the copy under ignored `build/`; include no existing generated output.

Back in the original checkout, build production and stock once, then
run the explicit compiled binary suites:

```sh
make bootstrap
make build-stock-modern
make build-stock-bugfixed
make rom
PYTHONPATH=. build/emulation-venv/bin/python tests/check_production_binary.py
PYTHONPATH=. build/emulation-venv/bin/python tests/check_modern_binary.py
PYTHONPATH=. build/emulation-venv/bin/python tests/check_modern_handoff_binary.py
PYTHONPATH=. build/emulation-venv/bin/python tests/check_modern_live_binary.py
PYTHONPATH=. build/emulation-venv/bin/python tests/check_modern_fixbugs.py
make source-bugfixed
make rom-bugfixed
python3 -m tools.mdplus_builder verify-rom \
  --bugfixed --strict-regression build/sonic2-mdplus-bugfixed.md
sha256sum build/sonic2-mdplus.md build/sonic2-mdplus-bugfixed.md
FORGE_TEST_VARIANT=bugfixed PYTHONPATH=. build/emulation-venv/bin/python tests/check_modern_binary.py
FORGE_TEST_VARIANT=bugfixed PYTHONPATH=. build/emulation-venv/bin/python tests/check_modern_handoff_binary.py
FORGE_TEST_VARIANT=bugfixed PYTHONPATH=. build/emulation-venv/bin/python tests/check_modern_live_binary.py
PYTHONPATH=. build/emulation-venv/bin/python tests/check_bugfixed_binary.py
PYTHONPATH=. build/emulation-venv/bin/python tests/check_stock_bugfixed_binary.py
PYTHONPATH=. build/emulation-venv/bin/python tests/check_audio_data_binary.py
PYTHONPATH=. build/emulation-venv/bin/python tests/check_level_data_binary.py
```

The binary suites check the exact production identity and execute compiled
68000/Z80 instructions for the backend, handoff and live routing.
`fixBugs=1` must be rejected by the fixed-layout assembly assertion. These tests
do not model audible mixing, SD-card access or console bus timing.
The Bugfixed binary check proves independent strict identity, exact curated
source preparation, safe extension placement, hooks, all eight complete Z80
bank-switch expansions and full 2 MiB curated-baseline reconstruction. It also
rebuilds from deleted Bugfixed outputs and checks isolation in both build orders.
CI runs the same three CPU suites against each variant; their default invocation
remains Production. The stock Bugfixed audit independently checks the frozen
source policy, exclusions, compiled gameplay, RAM and retail Z80 evidence.
The selective audio audit reconstructs both complete v3 Bugfixed images, freezes
all symbol addresses and compares selected compiled data with pristine upstream
fixed-data assemblies. The level audit first reconstructs both pre-level ROMs
exactly, enumerates all symbol movement and verifies every compiled object file,
pointer and boundary against its selected or pristine input. Generated reports
and listings remain under ignored `build/`.

For source-policy changes, run the same reference builds and compiled checks in
a disposable clean Linux copy, with one `make bootstrap` and no reused build
outputs. Audio conversion and packaging need not be repeated when their code
and inputs are unchanged.

The production ROM is byte-identical to the hardware-tested Stage 5 image, so
its passed hardware gate also covers this release. The
[short MiSTer RC checklist](docs/STAGE6_CUTOVER.md#short-mister-rc-checklist)
is available to confirm discovery and playback from the newly generated package.

## Copyright

Read [docs/LEGAL.md](docs/LEGAL.md). In short: publish the scripts and metadata,
not the generated game or audio. `build/`, `dist/`, ROMs, WAVs, CUEs, and common
disc-image formats are ignored on purpose.

The original tooling in this repository is licensed under
[GPL-3.0-only](LICENSE). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
for dependency licensing and trademark notices. Contributions are covered by
[CONTRIBUTING.md](CONTRIBUTING.md), the [Code of Conduct](CODE_OF_CONDUCT.md),
and the [security policy](SECURITY.md).
