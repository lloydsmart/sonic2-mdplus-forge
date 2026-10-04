# Changelog

All notable changes to this project will be documented here.

The format is based on Keep a Changelog, and the project uses Semantic
Versioning for its own tooling releases.

## [Unreleased]

### Fixed

- Derive selected level-object records from hash-checked pinned Fixed Files at
  build time; retain only semantic shape metadata in Forge. Remove copied object
  payloads from source, tests and documentation, while preserving exact ROM
  identities and independent complete-ROM reconstruction evidence.
- Apply only the three approved EHZ2 object insertions, the ARZ2 loop-progression
  pathswapper and the WFZ1 conveyor subtype correction through the authoritative
  Bugfixed policy. Retain ARZ2's bubble generator and every other unselected
  object/ring input. Lock retail, pinned reference and selective target hashes;
  audit semantic changes and the EHZ2 issue-#111 capsule regression.
- Account for all 17,041 changed bytes in each Bugfixed ROM and all 25 changed
  symbol values. Existing alignment absorbs 24 added object bytes; sound, Z80,
  Forge, RAM and Production remain unchanged. Freeze stock Bugfixed at `53DB` /
  `9ff0b7b5...` and Bugfixed MD+ at `C145` / `f33a1946...` after software and clean
  Linux validation. The exact MD+ candidate passed targeted MiSTer qualification;
  preserve the exact
  `b04c2fd3...` selective-audio candidate as the qualified pre-level baseline.
- Select only Spin Dash Release transpose and Credits PSG pitch corrections for
  Bugfixed. Neutralise the obsolete Credits compensation without moving data.
  Keep `FixMusicAndSFXDataBugs` globally disabled; Sky Chase, Death Egg, Z80
  driver fixes and, at that pre-level phase, Fixed Files remain excluded.
  Production stays byte-identical.
- Lock pristine and post-policy hashes for both selected inputs; compare complete
  compiled data with upstream fixed semantics and reconstruct both v3 Bugfixed
  baselines from the exact three changed operands and header checksums. Freeze
  the new software-validated identities; the exact Bugfixed MD+ candidate also
  passed the targeted MiSTer qualification below.

### Changed

- Document research-only door and OOZ2 findings: actual door references select
  `$02`, contrary to the runtime `$03` comment; the two OOZ2 corrections affect
  Obj45 push springs, not Obj48 ball launchers. Keep both deferred.
- Hardware-qualify the exact Level Data Test Bugfixed MD+ candidate on MiSTer
  FPGA, Mega Drive core `26.06.03`: checksum `C145`, MD5
  `50e81d88e257f8d14608e57801b628c5`, SHA-256
  `f33a1946a609b8045bb56ffce2aba05196190965fed6ddf5f8eb3b80c52a0c52`.
  All three selected EHZ2 fixes and boss/capsule progression, ARZ2 pathswapper
  progression from normal and below-loop approaches with its bubble generator
  retained, and WFZ object `$72` diagonal conveyor transport passed. Native SFX
  over MD+, pause/unpause, MD+ -> temporary native music -> MD+ restoration and
  reset passed; no obvious object corruption or hardware regression was observed
  in the targeted scope. This adds qualification for the selected level-data
  changes; earlier broad evidence remains tied to its exact ROMs. No new full-game
  playthrough or comprehensive retest of previous Bugfixed features is claimed.
  All unselected Fixed Files remain excluded. See the
  [level-data hardware results](docs/BUGFIXED.md#targeted-level-data-mister-hardware-qualification).
- Hardware-qualify the exact post-v3 Bugfixed MD+ candidate on MiSTer FPGA,
  Mega Drive core `26.06.03`: checksum `6AD6`, MD5
  `ef060d788f896099075e370195120ff2`, SHA-256
  `b04c2fd39e804719db599cca014966b19f07b16140688ee265c1dc759cb2212b`.
  Repeated Spin Dash releases sounded normal across charge lengths, directions
  and ordinary SFX combinations, with no audible regression. Vanilla driver
  overflow already masks the malformed `$90` transpose; the source/compiled
  audit establishes the data correction, without claiming an audible change.
  Credits playback through the end exercised both corrected PSG2 regions and
  sounded normal, with no invalid pitch, garbage notes, discontinuity or stuck
  PSG. Extensive native SFX, both Emerald Hill acts and boss, part of Chemical
  Plant Act 1, MD+/native coexistence and ownership transitions, invincibility,
  repeated pause/unpause, the Death Egg music sequence through the ending
  transition and level select all passed. No hardware regression was observed.
  Exact binary accounting established only the intended data operands and
  header checksum changes before this targeted hardware qualification.
  Retain v3.0.0 `d1668976...` as the released hardware-qualified baseline;
  these selective audio-data fixes are post-v3. No new full-game playthrough
  or comprehensive 2P soak is claimed for this candidate. See the
  [complete hardware results](docs/BUGFIXED.md#targeted-mister-hardware-qualification).

## [3.0.0] - 2026-10-03

### Changed

- Freeze the validated Production and curated Bugfixed flavours for v3.0.0.
  Removing the public `--legacy` and `*-legacy` interfaces from v2.0.0 is a
  breaking tooling change under Semantic Versioning, requiring a major release.
  Production retains its exact hardware-qualified Stage 5 ROM and audio policy.

### Added

- Integrate the frozen curated gameplay policy with Forge MD+ in the Bugfixed
  flavour. Reuse the authoritative policy, lock its three post-policy hashes,
  relocate Forge to `$108000` and independently audit the moved pause hooks,
  loader and Z80 bank switches. Freeze the new 2 MiB ROM at checksum `6B57`,
  SHA-256 `f80d983bdc44d5d89f3f7556e644a5b0ff5bf6e519ddacf0a3df73d4406449dc`.
- Verify the full curated 2 MiB baseline outside exact Forge mutations, run all
  three compiled CPU suites against both layouts, and check deterministic
  rebuilding and package coexistence. The preceding Obj2B-corrected Bugfixed ROM
  was software-verified and hardware-qualified on MiSTer Mega Drive core
  `26.06.03`. Production remains the default hardware-qualified build with its
  exact Stage 5 identity, names and compatibility symlink.
- Establish the curated no-MD+ `build-stock-bugfixed` reference, including the
  downstream MCZ right-drill operand correction and its compiled orientation
  tests. Its source policy, strict identity and exclusions remain frozen during
  MD+ integration: Z80 fixes, music/SFX data fixes, the complete alternate 2P
  sprite mechanism and Fixed Files remain deferred.
- Provide isolated Bugfixed preparation, ROM and package commands selected by
  `--bugfixed`, sharing the pinned dependency and unchanged prepared audio.
- Add GitHub release and license badges to the README alongside the existing CI
  badge.

### Fixed

- Preserve retail Obj82 pillar jumping and walking collision (`$30/$31`) while
  retaining upstream's `$32` display radius and explicit-height culling fix.
  Upstream already compensates walking collision; reorder that compensation to
  act on `d2` before deriving `d3`. Guard the source anchor and run compiled
  retail/stock/MD+ pillar and non-pillar regressions. The 18-byte sequence stays
  size-neutral; only its local branch label moves, with no downstream movement.
  Obj82 was identified through source/compiled analysis, then validated after
  correction on hardware; Obj2B was originally identified from observed gameplay.
- Rebaseline stock Bugfixed to checksum `FDEC`, SHA-256
  `7e8fe718aea8344dfe32931097977c0661bc0dbc9c41cba60e7b7a5e12be933f`,
  and Bugfixed MD+ to `6B56`, SHA-256
  `d16689760d3c913ff795c7f3b1c3c98b8ad789fb95efdbd50efaa4cd7f95f621`.
  Update the curated source and masked-reference digests; preserve Obj2B,
  Production, Forge placement/protocols, Z80, audio and historical hardware
  qualification evidence for the preceding exact identities.
- Hardware-qualify the exact current `6B56` / `d1668976...` Bugfixed MD+ ROM on
  MiSTer Mega Drive core `26.06.03` after targeted ARZ Act 1 `$10` and Act 2 `$11`
  contact, standing, walking, side collision and culling checks, Act 2 waiting/
  falling checks, and ARZ playback/looping, pause, invincibility and boss-music
  transition/restoration checks. An Act 1 Obj2B standing-while-rising regression
  check also passed. No hardware regression was observed. Retain
  the preceding `f80d983b...` Obj2B qualification and earlier broad 1P/2P results
  as historical evidence; no new full-game playthrough or comprehensive soak
  is claimed for the current hash.
- Correct the unintended vertical-collision side effect of upstream's ARZ
  Rising Pillar culling fix, exposed by MiSTer playtesting. Retain explicit
  height and the larger display dimensions; subtract eight only for collision.
  Guard the curated source transformation and execute compiled regressions at
  all seven rising heights. The two-byte insertion is absorbed by existing
  local alignment; Forge placement, Z80 bytes and Production remain unchanged.
- Rebaseline stock Bugfixed to checksum `FDED`, SHA-256
  `51263146131fa2dd70b2fa4c4b5701c6eb7d72d6683bf032358163716bf4ac81`,
  and Bugfixed MD+ to `6B57`, SHA-256
  `f80d983bdc44d5d89f3f7556e644a5b0ff5bf6e519ddacf0a3df73d4406449dc`.
  Recalculate the strict curated masked baseline. Preserve the pre-correction
  full 1P and comprehensive 2P evidence on Mega Drive core `26.06.03` as
  historical results. Targeted revalidation of the revised exact hash passed
  in both ARZ acts, with audio/lifecycle checks and an EHZ 2P regression sample;
  the preceding Obj2B-corrected Bugfixed MD+ ROM was hardware-qualified on that
  core.

### Removed

- Retire the `msu-md-sonic2` / separately built ASL fallback, its dependency
  pins, `--legacy` selection, legacy-only options and `*-legacy` Make targets.
  Remove its source converter, ASM helpers, ROM verifier and exclusive tests.
  At retirement, CI validated only stock upstream and the production
  implementation; it now also verifies both curated Bugfixed references.
- Preserve the production commands, compatibility aliases, strict checks and
  byte-identical hardware-tested Stage 5 ROM. Earlier implementations remain
  available in Git history and the existing `v2.0.0` tag.

## [2.0.0] - 2026-09-25

### Changed

- Promote the hardware-verified current-s2disasm REV01 implementation to the
  default bootstrap, source, ROM, full-build, verification and packaging paths.
  The canonical ROM is `build/sonic2-mdplus.md`, byte-identical to Stage 5
  (`BE41`, SHA-256 `bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`).
  Keep explicit `--legacy` / `*-legacy` fallback commands and the prior ROM
  identity under `build/sonic2-legacy-mdplus.md`. Retain modern command aliases
  and the old modern filename as a symlink to the canonical ROM.
- Require the selected implementation's exact regression identity when packaging,
  including rejection of a stale legacy ROM under the canonical output name.
  Preserve all audio inputs, Addryu routing, loop metadata and package names.
- Prepare legacy source in a disposable clone, retaining dependency inputs.
  CI now builds and verifies both ROMs and executes the compiled CPU suites;
  include the production Lua wrapper in Python package data.

### Added

The entries below record the migration stages before the production cutover
described above.

- Initially experimental Stage 5 modern live MD+ routing with acknowledged native-to-MD+
  ownership transfer, native temporary cues, pause/resume, fade/stop, and
  255-VInt extra-life ducking through all six upstream paths. Fixed-size
  PlaySound/PlaySound2, VInt, reset and direct pause hooks preserve upstream
  layout. The Stage 3 primitives and Stage 4 Z80 image remain byte-identical.
  Exact binary audits and compiled CPU tests cover the new layer. Its original
  output was `build/sonic2-modern-mdplus.md`; Stage 6 promoted the same ROM to
  the default described above and retained that filename as a compatibility symlink.
  The required MiSTer FPGA hardware gate has passed, covering native/MD+
  transitions, SFX, controls, progression, warm reset and Death Egg/ending.
  The optional missing-WAV robustness test was not run.

- Inert Stage 4 modern music-only Z80 handoff using private F7 and ACK A5.
  At that stage, native gameplay and the disconnected Stage 3 MD+ backend were preserved.
  Hash-locked preparation audits all three changed upstream files. Compiled
  CPU tests cover the loader, paused handoff, SFX preservation/progress,
  mailbox contention, retries and RAM boundaries. Stage 5 subsequently added
  ownership and connected live routing.
- Targeted modern three-slot SFX copy correction, required to preserve Music1,
  and Saxman loader correction, required to load every modified Z80 byte.
  Global `fixBugs=1` remains unsupported. At Stage 4, these changes were confined
  to the experimental modern path; the then-production legacy transformer and
  ROM remained unchanged.

- Internal Stage 3 modern MD+ backend with the production sixteen-track Addryu
  routing policy and five isolated control primitives in the appended Forge
  region. At Stage 3, gameplay remained entirely native; the backend stayed
  disconnected until Stage 4 added the handoff and Stage 5 added ownership/routing.
  Exact binary audits and direct CPU tests cover transactions, routes and
  unchanged native PlayMusic behaviour. Legacy remained the default at that stage.

- Internal `prepare-modern` and `build-modern` migration scaffold with a fixed
  PlayMusic trampoline and Forge-owned implementation in an appended ROM region.
  The Stage 2 seam kept all music native, with no runtime state or MD+ commands.
  Strict binary checks and CPU tests protect native mailbox, register and condition-code
  behaviour; stock modern and the then-default legacy MD+ builds remained separate.

- Initially experimental `bootstrap-modern` and `build-stock-modern` commands
  for pinned current sonicretro/s2disasm, using upstream's Lua build and exact
  stock REV01 size, MD5, and SHA-256 verification. At Stage 1, the modern build
  had no MD+ support; production MD+ commands still selected the legacy source.

## [1.0.0] - 2026-09-24

### Changed

- Trim Sky Chase Zone track 13 by 1162 sectors (15.493333 seconds), shifting its
  output loop coordinates from `11113 → 14082` to `9951 → 12920` while
  preserving the same 2969-sector source loop. The trimmed opening and loop
  were verified end-to-end on MiSTer hardware.

- Pin the Sonic source dependency to `lloydsmart/msu-md-sonic2` commit
  `b49afdb010090c282e1bb79f18f14a32d1bb7a99`, which contains the game-mode
  dispatch repair submitted upstream as ArcadeTV PR #5. Remove the duplicate
  forge-side source rewrite while preserving the exact audited ROM bytes.

- Mark all 16 enabled Addryu cues as MiSTer-hardware verified, preserving every
  loop point and WAV.
- Promote the repaired REV01 ROM to the audited strict regression baseline
  after a complete MiSTer hardware playthrough: checksum `2911`, SHA-256
  `315c69fb84dbca2a31ceffe3face70b4138317feed53feb7e23c6a5ab009205e`.

- Enable Aquatic Ruin Zone MD+ track 07 with the hardware-verified sector
  `828 → 4284` loop.

- Replace `as-sonic` with pinned maintained ASL 1.42 build 306, with bounded
  source syntax conversion preserving the exact hardware-verified ROM hash.

- Rename the project to Sonic 2 MD+ Forge and make its positioning ready for
  additional soundtrack variants without changing the current Addryu profile.

### Added

- Optional `trim_start_sector` audio-manifest support for sector-exact
  final-domain start trimming while keeping loop coordinates relative to the
  generated WAV, with matching native PCM and FFmpeg paths plus unit and
  manifest-integration coverage.

- Deterministic hybrid music: sixteen fixed Addryu cues use MD+, while other
  cues use Sonic 2's original soundtrack. Missing Addryu WAVs never change ROM
  routing; MD+ speed-shoes variants remain disabled.
- Ownership-aware pause, resume, fade and stop, with an acknowledged native
  music-only handoff that preserves SFX and consecutive MD+ transactions.

- Hardware-verified Chemical Plant loop metadata (`1900 → 5500`).
- Source-aware audio normalization with FFprobe reporting, sample-preserving
  native PCM handling, SoXR precision-33 resampling, explicit high-pass
  triangular dithering, and functional FFmpeg capability checks.
- Markdownlint with locked development dependencies and monthly Dependabot updates.
- File-sensitive CI lint steps for Python and Markdown, preserving the required test check.

- Prominent guidance to purchase Addryu's album from Bandcamp and not
  redistribute the original or converted soundtrack.
- Dependabot version updates for Python development dependencies.

- Reproducible, pinned Sonic 2 MD+ source conversion.
- Rev 1 ROM checksum, signature, size, and SHA-256 verification.
- WAV normalization, sector-aligned trimming, loop candidate detection, loop
  scoring, CUE generation, and MiSTer package assembly.
- Hardware-verified Emerald Hill loop metadata (`292 → 3892`).
- Unit tests, Ruff linting, and GitHub Actions checks.
- Legal, contribution, security, conduct, and third-party documentation.

### Fixed

- Restore the level-select cheat and Death Egg ending transition through the
  pinned `msu-md-sonic2` source's four-byte game-mode dispatch repair, submitted
  upstream as ArcadeTV PR #5. Both REV00 and REV01 passed MiSTer hardware
  verification; the repaired REV01 ROM is the audited production baseline.

- Eliminate 33 ASL MOVEQ sign-extension warning sites through guarded symbolic
  signed-byte conversion, preserving the exact ROM and intentional odd-address access.

- Process the final compressed Z80 driver byte; the first hybrid ROM otherwise
  omitted its handoff ACK store and return, causing the first level transition
  to fail on MiSTer. Builds now verify the entire loaded driver against assembly.
- Move handoff completion out of `QueueToPlay` into dedicated Z80 RAM so delayed
  68000 acknowledgement cannot starve normal SFX. Add CPU-level regression
  coverage for the loader, handoff, VInt paths and continued SFX dispatch.

- Keep the second music mailbox out of the SFX-copy loop, where the pinned
  source otherwise writes it into the Z80 voice-table pointer.

- Close the MD+ overlay immediately after every command transaction, avoiding
  corruption when live Sonic 2 code crosses the MD+ register window.
