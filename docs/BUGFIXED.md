# Bugfixed source policy

## Base and current status

The base is `sonicretro/s2disasm` REV01 at immutable commit
`380f37a731bfc720bb0371a35a593184a7ec5e43`.

The maintained builds have distinct policies and verification profiles:

| Build | Source policy | Forge MD+ |
| --- | --- | --- |
| Stock Production reference | Untouched pinned REV01 | None |
| Stock Bugfixed reference | Curated game fixes described here | None |
| Production MD+ | Pristine retail policy | Hardware-qualified Stage 5 |
| Bugfixed MD+ | Curated policy, audio and six layouts | Hardware-qualified; targeted door scope below |

`rom-bugfixed` and its package integrate curated gameplay fixes with Forge
MD+. The exact current door candidate `0951` / `e9f56f0e...` is
**hardware-qualified on MiSTer Mega Drive core `26.06.03` for the targeted
door-data/runtime-workaround scope and regression sanity below**.
Production remains the default hardware-qualified build with its exact
Stage 5 identity. **The released v3.0.1 Bugfixed identity `C145` / `f33a1946...`
is hardware-qualified on MiSTer Mega Drive core `26.06.03` for the targeted
level-data and regression sanity scope below.** The v3.0.0 Obj82-corrected
`d1668976...` and intermediate selective-audio `b04c2fd3...` identities retain
their own targeted qualification on that core. The preceding Obj2B qualification
and earlier broad 1P/2P results remain historical evidence for their exact ROMs.
See the [v3.0.1 release record](releases/v3.0.1.md) for release-preparation evidence.

Historical preparation, identity and Forge-validation sections below retain their
released pre-door addresses, hashes and test results. The post-v3.0.1 door section
explicitly describes all current changes to those tables; historical evidence is
not rewritten as candidate evidence.

## Released v3.0.1 selective level data

Version 3.0.1 freezes the post-v3 selective audio and level-data work. The level
changes add only the three approved EHZ2 placements, the ARZ2 progression
pathswapper with its bubble generator retained, and the WFZ1 conveyor correction.
The exact `b04c2fd3...` audio-polish candidate remains the historical
hardware-qualified pre-level-data baseline. **The released `f33a1946...` identity
is software-validated and hardware-qualified on MiSTer Mega Drive core `26.06.03`
for the selected level-data changes and regression sanity scope recorded below.**
Neither the pin nor Production changes.

### Provenance and exact selected semantics

The reference is `Utility Project Files/Fixed Files/` in the immutable pinned
dependency. Upstream introduced it in
[`1fe74ae94d6233b34e4fd10bd8d4282cb1ca8305`](https://github.com/sonicretro/s2disasm/commit/1fe74ae94d6233b34e4fd10bd8d4282cb1ca8305),
"Added Fixed Files folder". Use EHZ2 only from the current
[`380f37a731bfc720bb0371a35a593184a7ec5e43`](https://github.com/sonicretro/s2disasm/commit/380f37a731bfc720bb0371a35a593184a7ec5e43),
"Fix fixed EHZ2 object layout", which also revised the ARZ2 reference.
`Fixed Files.txt` is the authoritative explanation of the intended changes;
the Sonic Jam origins below are upstream's attribution, not an independent
comparison against a Jam ROM.

Indices below are zero-based retail indices. Forge stores only operation,
index and entry-count metadata. Actual six-byte placements, including their
flags, are read from the hash-checked pinned dependency at build time.

| Layout/index | Reference index | Operation | Old/new count | Purpose |
| --- | --- | --- | --- | --- |
| EHZ2/29 | 29 | Insert | 0/1 | Cave-entrance wall |
| EHZ2/64 | 65 | Insert | 0/1 | Wall/spring floor clip guard |
| EHZ2/142 | 144 | Insert | 0/1 | Corridor pathswapper |
| ARZ2/119 | 118 | Insert | 0/1 | Loop approached from below |
| WFZ1/127 | 127 | Replace | 1/1 | Working conveyor |

All selected entries have zero orientation/remember flags. EHZ2's wall/spring
guard and corridor pathswapper, and ARZ2's pathswapper, are attributed to Sonic
Jam in upstream notes. The cave wall has no such attribution. Obj74 derives
half-width/radius `$08/$08` for subtype `$00`, and `$10/$60` for `$1B`.
Obj03 uses bit 2 for a Y-crossing switch and the low two bits for its radius;
ARZ2's `$26` selects the `$80` radius, while EHZ2's `$01` selects an X-crossing
switch with `$40` radius. Other subtype bits are preserved exactly.

EHZ2 has precisely those three insertions and no replacements/deletions.
Its prepared target equals the complete current pinned reference. In
[issue #111](https://github.com/sonicretro/s2disasm/issues/111), the reported symptom
was a signpost preventing the capsule spawn. The upstream diagnosis identifies
an invisible wall at `$1490` incorrectly stored after the prison at `$2B50`.
The loader scans by camera X, so that unsorted placement corrupts traversal.
Comparing the parent revision to the pin shows the wall moving from the tail
to its sorted position and removal of a trailing `$FFFF,0,0` boundary entry.
The current reference has no embedded boundary, sorted X coordinates, and every
retail signpost/capsule entry unchanged. Its final capsule remains byte-identical
to the pinned retail entry. This proves the source-layout regression is absent.
Separately, the targeted hardware test reported normal boss/capsule progression on the exact
level-data candidate.

The complete ARZ2 reference has exactly two differences: deletion of retail
entry 33 (bubble generator) and a single pathswapper insertion at retail index
119 (reference index 118). Forge derives the selective target from retail and
inserts only that pathswapper. The bubble remains at
index 33, byte-identical. Removing the inserted entry reproduces every retail
byte, including all other objects and their order. The target intentionally
differs from the complete Fixed File.

WFZ1 has exactly one changed byte: the conveyor subtype. Obj72 computes its
horizontal half-width by masking `$7F`, then shifting a **byte** left four.
`$90` therefore wraps to zero width, and the unsigned horizontal range test
always returns. `$09` gives half-width `$90` (288 pixels total), a `$30` vertical
range, and grounded transport at +2 pixels per update. Retail `$90` also sets
the high-bit vertical range to `$70`, but its zero horizontal width disables
transport. The compiled test executes both initializations and proves grounded
movement for `$09`, no movement for `$90`, and no transport while airborne.

### File hashes and preparation isolation

All names below are under `level/objects/`; references use the same relative
name under `Utility Project Files/Fixed Files/`.

| File | Retail/reference/target bytes |
| --- | --- |
| `EHZ_2.bin` | 948 / 966 / 966 |
| `ARZ_2.bin` | 1,332 / 1,332 / 1,338 |
| `WFZ_1.bin` | 942 / 942 / 942 |

SHA-256 locks:

| File/stage | SHA-256 |
| --- | --- |
| EHZ2 retail | `7b3384fe361309fd2a36961116bf8d89c22399acb88fa7d632a467cc062c1560` |
| EHZ2 reference and target | `ba2b2db75688f309847a90172991f151e233d41c272fbd5eb3462f3650c00e5d` |
| ARZ2 retail | `08f21b09e76d4920e5861d9cdc25329ee304ea69e3171d8551b5c5c729d82297` |
| ARZ2 reference | `2b52c83cdc3a87bf594292c9a2769c7d99595a04159231ed9879588d6d59f39e` |
| ARZ2 selective target | `30fea857b2209a2b33f1befec90c446081356a8203f9e665874746bda0720ad2` |
| WFZ1 retail | `b5afcb63c936ae62d860292a3ec4a7c4e7ff5cb24cf88130e4a6ae231bb737c4` |
| WFZ1 reference and target | `570e79e93a71296f69f91413b6f615de83c662ab3d6f9e31ff864cc001b9cbab` |

`level_data.py` parses entries, checks both input hashes and the reference
semantic shape (operation, retail index and old/new entry counts), derives actual
payloads from that diff, applies only selected reference edits to retail, checks
the selected payload diff and target hash, and returns validated outputs. Authoritative `apply_policy`
validates all eight outputs before any write. Every tracked file is hashed
before and after; only the five existing source/audio files and these three
object files may change. The dependency and complete Fixed Files reference tree
stay pristine. No object-entry payload is vendored into Forge, including tests
and documentation. The independent reconstruction helper separately checks the
immutable checkout commit and its own input/target hash locks, derives expected
entries using explicit retail/reference slices and validates all intervening
unchanged entries. It never imports the production policy, semantic diff or
transformation result. Reversal uses those independently derived dependency
entries; the complete frozen pre-level ROM hashes still guard every byte.

CPZ1/2, DEZ1 and OOZ2 remain retail in this task. Every ring file, HTZ leftover
seesaw, MTZ object cleanup and every other unselected input remain pristine.
The bubble deletion is rejected. Spin Dash/Credits source transformations and
their compiled operands remain unchanged; Sky Chase/Death Egg remain excluded.
`FixMusicAndSFXDataBugs=0`, `FixDriverBugs=0` and
`ForgeFix2PSpritePageFlip=0` remain enforced. The `$FFF100-$FFF5FF` RAM hole
and Forge allocations remain unchanged.

### Complete symbol movement and ROM accounting

Both stock and MD+ independently produce this identical movement map:

| Labels | Before -> after | Delta |
| --- | --- | --- |
| `Objects_EHZ_1`, `Objects_EHZ_2`, `Off_Objects` | Existing addresses unchanged | 0 |
| `Objects_MTZ_1` | `$E7534 -> $E7546` | +18 |
| `Objects_MTZ_2` | `$E79C0 -> $E79D2` | +18 |
| `Objects_MTZ_3` | `$E7EEE -> $E7F00` | +18 |
| `Objects_WFZ_1` | `$E8548 -> $E855A` | +18 |
| `Objects_WFZ_2` | `$E88FC -> $E890E` | +18 |
| `Objects_HTZ_1` | `$E8902 -> $E8914` | +18 |
| `Objects_HTZ_2` | `$E8C68 -> $E8C7A` | +18 |
| `Objects_HPZ_1` | `$E9280 -> $E9292` | +18 |
| `Objects_HPZ_2` | `$E9394 -> $E93A6` | +18 |
| `Objects_OOZ_1` | `$E93A0 -> $E93B2` | +18 |
| `Objects_OOZ_2` | `$E9814 -> $E9826` | +18 |
| `Objects_MCZ_1` | `$E9C8E -> $E9CA0` | +18 |
| `Objects_MCZ_2` | `$E9FA0 -> $E9FB2` | +18 |
| `Objects_CNZ_1` | `$EA31E -> $EA330` | +18 |
| `Objects_CNZ_2` | `$EA9D8 -> $EA9EA` | +18 |
| `Objects_CPZ_1` | `$EAFD2 -> $EAFE4` | +18 |
| `Objects_CPZ_2` | `$EB36E -> $EB380` | +18 |
| `Objects_DEZ_1` | `$EB830 -> $EB842` | +18 |
| `Objects_DEZ_2` | `$EB854 -> $EB866` | +18 |
| `Objects_ARZ_1` | `$EB85A -> $EB86C` | +18 |
| `Objects_ARZ_2` | `$EBCA4 -> $EBCB6` | +18 |
| `Objects_SCZ_1` | `$EC1DE -> $EC1F6` | +24 |
| `Objects_SCZ_2` | `$EC34C -> $EC364` | +24 |
| `Objects_Null` | `$EC352 -> $EC36A` | +24 |
| `paddingSoFar`, stock | `$1000FB -> $1000E3` | -24 |
| `paddingSoFar`, MD+ | `$FFA3B -> $FFA23` | -24 |

There are exactly 24 moved object labels plus the assembly padding counter;
no added or removed symbols. Restoring those 25 values reproduces each complete
pre-level symbol-map SHA-256: stock
`fa3e71943d4f3e2ed5ba99c31fa021f83e6f9356be100fa188a1b2135fcf9625`, MD+
`8ec6707534a3f112a41e9df92d224f7f58b4eda01eb072616bc297549db6bf3b`.
All other symbols, including code, sound, Z80, bank targets and RAM, match.

Object entries are uncompressed `BINCLUDE` data with separately emitted
six-byte `$FFFF,0,0` boundaries. No compressor or compressed asset changes.
The last boundary ends at `$EC36A` before and `$EC382` after. The existing
`align $1000` still places `SoundDriverLoad` at `$ED000`: zero padding decreases
from 3,222 (`$C96`) to 3,198 (`$C7E`) bytes. This absorbs all 24 added bytes.
ROM size remains 2 MiB; the header ROM end remains `$1FFFFF`.

Each ROM differs from its exact audio baseline in **17,041 bytes**:

| Exhaustive category | Changed bytes | Explanation |
| --- | --- | --- |
| `$18E-$18F` | 2 | Recalculated header checksum |
| `$E6E00-$E6E43` | 35 | 32 moved relative pointer words in the 34-entry table |
| `$E717A-$EC37D` | 17,004 | Selected edits, shifted pristine entries/boundaries and shorter zero padding |

The two EHZ pointers remain unchanged. Pointer deltas are +18 for layouts
after EHZ2 through ARZ2, and +24 for SCZ/null. The audit checks all 34 emitted
words, every compiled object file against its retail/selected input and every
intervening boundary. It reverses the four insertions and WFZ subtype byte,
restores pointer words and checksum, then requires the exact complete old ROM:
stock `869869560951eaad0fc327057e50e8ae3cf4ea04c877ff81e8c22a0b17cc02fa`, MD+
`b04c2fd39e804719db599cca014966b19f07b16140688ee265c1dc759cb2212b`.
There are no unexplained bytes. `build/level-data-diff.json` records category
counts, all movements, file positions/sizes and alignment evidence.

Sound data `$F5100-$107FEB` remain identical. The Forge driver remains 4,011
compressed / 4,986 loaded bytes, with loaded SHA-256
`f2883990453ba7deedc682b3970be0d2c73fea99a566a30d43362c2769ac7041`.
The compressed region/padding hash remains
`b9788df25eb06f84bacdb03b620c256a72001c533c08770faa7a93826ef985e1`.
All eight Z80 bank-switch targets and their existing Production/Bugfixed
relocation audit remain unchanged. Forge remains `$108000-$1086BF`, exclusive
end `$1086C0`; final sound end remains `$107FEC`. All hooks and RAM allocations
remain fixed. Only Bugfixed identities and its exact masked-stock digest change.
The latter is `1e8d2df3382042f15102491dbfa622e5f3ccd3f47f865af83f8c1a69930b87ad`.

### Released v3.0.1 identities and software validation

| Build | Size | Checksum | MD5 |
| --- | --- | --- | --- |
| Stock Bugfixed | 2,097,152 | `53DB` | `ae378a1f8b41d9e804a0d05cb21f7951` |
| Bugfixed MD+ | 2,097,152 | `C145` | `50e81d88e257f8d14608e57801b628c5` |
| Production MD+ | 2,097,152 | `BE41` | `9eb40c0601a7c424a0d1ce168b5f40f2` |

Current SHA-256 identities:

- Stock Bugfixed: `9ff0b7b577de237cf2fe9e13415a943b7d30e228a12b96b851793c95ece7184f`.
- Bugfixed MD+: `f33a1946a609b8045bb56ffce2aba05196190965fed6ddf5f8eb3b80c52a0c52`.
- Production MD+: `bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`.

The Production compatibility symlink retains its existing target. Both variants
retain 21 adjacent open/write/close MD+ transactions, 42 `$0003F7FA` signatures,
21 `$0003F7FE` signatures and 21 opens/closes. Startup checksum precedes every
overlay access, and checksum failure never opens it. PCM/sector/manifest rules
are unchanged.

Run `tests/check_level_data_binary.py` after all four builds. Its pinned-input
checks independently exercise pristine/reference/semantic/target failures before
writes, exact selected placements, capsule/signpost preservation, the retained
bubble, all exclusions, complete symbol maps and full ROM reconstruction.
The audio audit first reconstructs the audio baseline, then still reconstructs
both released v3 ROMs and compares selected data against upstream fixed semantics.
The README's existing compiled CPU, strict identity, independent stock,
integration and negative-control checks remain required for both variants.

Validation passed: Ruff, Markdownlint, compileall, all 90 unit tests, manifest
validation and `git diff --check`; all four stock/MD+ builds; both strict MD+
profiles; all three backend/handoff/live CPU suites for both variants;
Production `fixBugs=1` rejection; independent stock and Bugfixed integration
audits; the five-test selective-audio audit; and the three-test level-data audit.
A disposable Linux copy included the uncommitted source and new tests, fetched
the pinned dependency with one `make bootstrap` and reused no dependency,
prepared-source or ROM outputs. It reproduced all four ROMs byte-for-byte and
passed the same compiled audits. Existing emulator libraries are tooling
prerequisites, rather than ROM/source inputs. Audio/packaging code and inputs
did not change; unit tests still exercise synthetic FFmpeg conversions.

## Post-v3.0.1 CPZ/DEZ door candidate

This phase adopts the independently confirmed door research as one atomic policy:
select all nine pinned Fixed Files `$00 -> $02` Obj2D replacements and retire
both Bugfixed-only runtime `$03` overrides. The exact `0951` / `e9f56f0e...`
candidate is **hardware-qualified on MiSTer Mega Drive core `26.06.03` for the
targeted door-data/runtime-workaround scope and regression sanity recorded below**.
Version metadata stays `3.0.1`; the released identities
and their hardware evidence above remain frozen. OOZ2 remains deferred.
Issue #26 (intermittent Special Stage results text corruption) remains unrelated
and open; these tests do not establish any result for that issue.

### Data derivation and source change

| Layout | Retail/reference indices | Replacements | Total entries |
| --- | --- | --- | --- |
| CPZ1 | 60, 136 | 2 | 153 |
| CPZ2 | 42, 104, 154, 155 | 4 | 202 |
| DEZ1 | 0, 1, 3 | 3 | 5 |

Indices are identical in retail and reference. Adjacent replacements form one
semantic edit of count two in CPZ2 and DEZ1. Independent byte comparison proves
that these are every Obj2D placement in these files, every difference changes
only subtype `$00` to `$02`, and there are no unrelated edits or `$03` targets.
Positions, flags, IDs, ordering and lengths remain unchanged. Forge stores hashes,
operation/index/count metadata and purpose only. The complete six-byte records
are derived from the pinned dependency at build and audit time, never vendored.

CPZ_1 hashes:

- Pristine: `672c6b5ed672b889ad8629662f8e569fafca953046bfeeff999207bae17a4046`.
- Reference/target: `79635ca9a52ca5052bcd2ad86bd9059d5815aadfe7391d170f2538442c47a66d`.

CPZ_2 hashes:

- Pristine: `316c884cb1a26233eb1c67682d679d8e0fa4a3d353f76b4ca740ae705507f61b`.
- Reference/target: `0aeb9a4ef43f778976ea0c53493fbcc0df509c073d6291b28fa383e9a483a8a2`.

DEZ_1 hashes:

- Pristine: `7418dacc85fae3b501637a3ff9bb93840f70f271916984530cdc03561c211492`.
- Reference/target: `3d93d7b360bc05b417976d1d08f5aaa8f78f2fd69c492eef0ac22aa12d62e578`.

The authoritative `apply_policy` validates all source and layout outputs before
writing any. Pristine/reference hashes, complete reference edit shapes, selected
edit shapes and target hashes remain mandatory. Its eleven changed files include
the previous eight unchanged decisions plus these three layouts. EHZ2, selective
ARZ2 with its bubble generator, WFZ1 and selective audio retain their released
states. All other Fixed Files, driver fixes, global audio fixes and alternate
2P sprite machinery remain excluded.

In `Obj2D_Init`, remove precisely `move.b #3,subtype(a0)` from each of the
Chemical Plant and Death Egg art-selection branches, together with its enclosing
`if fixBugs` and obsolete hack comments. Each instruction occupied six bytes in
v3.0.1 Bugfixed, at `$011910` and `$01192A`. Exact contexts include the distinct
zone-art assignments and width stores; missing, duplicate, changed or already
transformed contexts fail closed. The generic
`move.b subtype(a0),mapping_frame(a0)` remains. Production retains the pristine
source, including both conditional stores; `fixBugs=0` omits them from its ROM.
The dependency checkout is untouched. The new curated `s2.asm` SHA-256 is
`3623acc2b4e00be962c432b27601615328e4f926071cbc6a460d9650eadd2773`.

### Compiled layout and complete reconstruction

The movement follows emitted code and the existing alignments, independently
observed in stock and MD+ listings:

| Region/symbol | Released v3.0.1 | Candidate | Consequence |
| --- | --- | --- | --- |
| `Obj2D_Init` | `$0118C8` | `$0118C8` | Entry unchanged |
| Between removed stores | — | — | Surviving instructions move -6 |
| `Obj2D_Main` | `$011986` | `$01197A` | Later code/maps move -12 |
| Player assets / `ArtUnc_Sonic` | `$050580` | `$050560` | `$20` alignment changes shift to -32 |
| `Off_Rings` | `$0E4900` | `$0E4800` | `$100` alignment changes shift to -256 |
| `Off_Objects` | `$0E6E00` | `$0E6C00` | `$200` alignment changes shift to -512 |
| End of object boundaries | `$0EC382` | `$0EC182` | More padding before loader |
| `SoundDriverLoad` | `$0ED000` | `$0ED000` | `$1000` alignment absorbs movement |
| Sound end / Forge base | `$107FEC` / `$108000` | Unchanged | No Forge relocation |
| Forge end | `$1086C0` | `$1086C0` | Code/transactions unchanged |

Alignment padding changes from 26 to 6 bytes at player assets, 254 to 30 before
rings, 296 to 40 before objects, and 3198 to 3710 before the loader. Total padding
increases by 12 bytes; both ROMs remain 2 MiB. The complete symbol dictionaries
are checked against the frozen release, including assembler values and the
legacy listing parser's address-shaped artifacts. Named movements comprise
12,766 values at -12, one at -6, 2,369 at -32, 37 at -256, 29 at -512 and
`paddingSoFar` at +12. Three non-address assembly constants and both MD+ hardware-register symbols
remain unchanged.

`tests/door_data_evidence.py` independently reverses the compiled candidate;
it imports no forward policy/parser/transformation. It copies every surviving
byte through seven disjoint movement intervals, checks all new alignment bytes
are zero, restores the two instructions and nine pinned retail subtypes, and
inverts address operands derived from actual listing emissions and symbol
references. Every other byte is retained for the final full-image hash check.
There are 2,362 absolute address operands, 60 word branch displacements, two
short branch displacements and one Obj2D index word. No broad masked region or
unexplained replacement blob is accepted. Checksums are restored and recalculated.
Both full v3.0.1 MD5/SHA-256 identities are recovered exactly: stock `53DB` /
`9ff0b7b5...`, MD+ `C145` / `f33a1946...`.

Each candidate differs at 808,214 byte positions from its released counterpart,
accounted for by the two removals, relocation/corresponding pointers, alignment,
nine subtype bytes and checksum. The payload-free generated report
`build/door-data-diff.json` records every fixup site/expression, movement interval
and complete before/after symbol dictionary. Mutation tests cover code, assets,
new padding, selected data, audio, Z80 and Forge, with repaired checksums.
The previous level-data and audio audits first reverse this door phase, then run
their unchanged historical reconstructions and symbol hashes. They do not redefine
v3.0.1 or the earlier baselines.

All bytes from `$0ED000` to ROM end match v3.0.1 in each variant, including the
loader, compressed Z80, sound banks, selective audio and Forge. Early/live hooks,
all eight Z80 bank targets, payload bounds, sound end, Forge base/end and RAM are
also checked independently by existing suites. The adapter changes only its
Bugfixed curated-source hash, strict identity, stock checksum and whole-stock
digest (`87d7102c04607783e2f6b4af02800bb0dd008e9beb1bdbae297a02610198882c`); its address profile stays fixed.
The `$FFF100-$FFF5FF` hole, Forge
allocations, delayed overlay activation, routing and 21 transactions are unchanged.

### CPU evidence and candidate identities

The seven-test door audit executes actual compiled Obj2D initialization for all
nine placements in stock and MD+, the reconstructed release and Production.
Retail `$00` selects frame 0, the wrong four-piece HTZ mapping for these zones;
v3.0.1 forces `$03` even when given `$02`; the candidate preserves `$02`.
Compiled frames 2 and 3 are identical 18-byte mappings. The remaining object
state matches after accounting for the deliberate frame/subtype and relocated
mapping pointer.

Compiled `Obj2D_Main` and `Obj2D_CheckCharacter` execute opening and closing to
both limits, Sonic/Tails triggers, controlled-character exclusion and horizontal/
vertical rectangle boundaries at every placement. Collision call arguments remain
width 19, heights 32/33 and the same X position; movement state matches throughout.
HTZ, both MTZ zone IDs and ARZ retain generic subtype behavior, tested for subtypes
0–3 and both horizontal orientations. This establishes software equivalence;
the harness does not model console bus timing or replace hardware testing.

| Identity | Stock Bugfixed candidate | Bugfixed MD+ candidate |
| --- | --- | --- |
| Size | 2,097,152 bytes | 2,097,152 bytes |
| Stored/calculated checksum | `9BE7` / `9BE7` | `0951` / `0951` |
| MD5 | `bd93d95a110be99e9eb9bafb3d31806f` | `5d3e5979d3f110d2761da3166b14b7cf` |

Candidate SHA-256 values:

- Stock: `909e5f229fc4052f3c3c3c9a97c3a6b345117990796b0226dffbc98f88f00bc7`.
- MD+: `e9f56f0efd72844918918f2efdecf6183f5bdabb47f235b61cc511a16942d3b5`.

Production remains `BE41`, MD5 `9eb40c0601a7c424a0d1ce168b5f40f2`, SHA-256
`bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`.

### Software validation and clean reproduction

Validation passed in the working tree and a disposable Linux copy:

| Suite | Tests |
| --- | --- |
| Unit tests (including synthetic FFmpeg conversion) | 92 |
| Production binary identity | 2 |
| Backend CPU, Production / Bugfixed | 7 / 7 |
| Handoff CPU, Production / Bugfixed | 14 / 14 |
| Live CPU, Production / Bugfixed | 15 / 15 |
| Production `fixBugs=1` negative control | 1 |
| Independent stock Bugfixed audit | 14 |
| Bugfixed Forge integration | 6 |
| Selective audio / historical level data | 5 / 3 |
| Door source/data/CPU/asset audit | 7 |
| Total | 202 |

Ruff, Markdownlint, compileall, manifest validation, both strict MD+ profiles and
`git diff --check` pass. All four maintained references build successfully.
The clean copy includes uncommitted source/tests, fetches its own pinned upstream
checkout and reuses no dependency, prepared source or ROM output. Emulator/lint
executables are tooling prerequisites shared with the working environment.
All four clean ROMs match byte-for-byte, including after deterministic rebuild
and isolation tests. The full compiled suites and quick checks pass there too.

The clean-copy results are retained pre-hardware evidence. This hardware
qualification/status update does not claim a new clean Linux rebuild: the
existing clean copy's 47 source/test/configuration and build-definition inputs,
all four ROMs and passing logs for 202 tests were reconfirmed against the current
candidate. The documentation changes do not alter those build inputs.
The full working-tree validation was rerun for this qualification/status update;
all four builds, both strict verifiers, quick checks and the same 202 tests passed.

The tracked/proposed-file asset scan finds no raw or hexadecimal copies of any
of the eighteen old/new door records, and no generated binary/audio/package
files. Review confirms that metadata and documentation do not re-encode full
placements as field tuples. All ROMs, listings, CPU/diff reports and the named
`Sonic 2 - Addryu Mega-CD Remix MD+ (Bugfixed) - Door Data Test.md` remain under
ignored `build/`. No commit, push, tag, merge or publication is part of this phase.

### Targeted door-data MiSTer hardware qualification

Lloyd reported the following hardware results on MiSTer FPGA, Mega Drive core
`26.06.03`, using this exact Bugfixed MD+ Door Data Test ROM:

- Size: 2,097,152 bytes.
- Stored/calculated checksum: `0951` / `0951`.
- MD5: `5d3e5979d3f110d2761da3166b14b7cf`.
- SHA-256: `e9f56f0efd72844918918f2efdecf6183f5bdabb47f235b61cc511a16942d3b5`.

The generated/current candidate matched this complete identity and passed its
strict verifier before this qualification record was updated.

| Target | Coverage | Hardware result |
| --- | --- | --- |
| CPZ1 | 2/2 affected Obj2D doors found and exercised | PASS |
| CPZ2 | 4/4 affected Obj2D doors deliberately located, including route-dependent placements | PASS |
| DEZ | 3/3 affected Obj2D doors found and exercised | PASS |

**Chemical Plant Act 1:** closed collision and open traversal were correct;
opening/closing behaviour was normal, with no clipping or sticking observed.
Act progression and transition were normal.

**Chemical Plant Act 2:** closed collision and open traversal were correct;
opening/closing behaviour was normal, with no clipping or sticking observed.
No door-related progression fault was observed.

**Death Egg:** closed/open collision and traversal were normal, with no clipping
or visual/object corruption observed. Progression through Mecha Sonic and the
Death Egg Robot succeeded, and the ending transition triggered successfully.

Regression sanity on the same exact candidate:

| Check | Result |
| --- | --- |
| Pause/unpause | PASS |
| MD+ -> native -> MD+ restoration | PASS |
| Soft reset | PASS |
| Level Select | PASS |
| Sprite/object corruption | None observed |

**Non-blocking CPZ2 observation:** brief slowdown was noticed while an
invincibility monitor effect was active. It is likely ordinary Mega Drive
slowdown under additional invincibility/object load, but this is an interpretation,
not a software-proven stock-normal result. It was not reproduced as a door fault;
no evidence currently ties it to this candidate. It is not established as a
hardware regression and supplies no evidence about issue #26, whose status
remains unrelated and open.

**No targeted hardware regression was observed. This exact `e9f56f0e...`
candidate is hardware-qualified on MiSTer Mega Drive core `26.06.03` for the
targeted door-data/runtime-workaround scope and regression sanity above.**

This was not a new complete Sonic 2 playthrough, a comprehensive 2P soak or a
retest of every Bugfixed feature. It does not hardware-qualify OOZ2 or establish
any result for issue #26. Earlier v3.0.1 hardware evidence remains attached to
its exact released identities; version metadata remains `3.0.1`.

### Historical pre-qualification MiSTer checklist

The following checklist was prepared before the qualification results above;
it remains historical test-planning evidence, not a claim that every suggested
check was performed.

Use the exact `0951` / `e9f56f0e...` Door Data Test candidate with the existing
lawfully prepared MD+ audio. Record the core version and ROM hash. A complete
game playthrough is unnecessary; level select may be used. Frames 2 and 3 are
visually identical, so looking for a changed appearance alone is insufficient.

The route hints below are approximate aids from pinned object order and nearby
object types, not a claimed hardware walkthrough. Count distinct sliding barriers;
if a route skips one, mark it untested and revisit it through another route.

- **Chemical Plant Act 1 — two barriers:** look for the narrow striped vertical
  sliding doors in the running corridors. The first is in the middle portion of
  the act, around the speed-booster/checkpoint section. The later one is among
  platforms before the descending staircase section toward the act's end.
  Approach from the permitted side, pass through, move away and return where
  possible. Check normal opening/closing, solidity from the blocked side and
  progression to the signpost and Act 2.
- **Chemical Plant Act 2 — four barriers:** check the earlier corridor door near
  the checkpoint section, the middle door around the speed-booster/spring area,
  and both doors in the later platform/corridor section (the last pair share
  roughly the same horizontal part of the level and can be route-dependent).
  Check both routes where accessible, door clearance, collision and normal
  progression through the remaining water/platform section and boss/capsule.
- **Death Egg — three barriers:** follow the short interior approach into the
  Silver Sonic encounter, through its exit and along the approach to the final
  boss sequence. Count the three sliding barriers along this progression. Check
  that they appear intact, trigger normally and never trap Sonic or obstruct the
  transition between encounters. Complete the boss approach as practical.
- At each tested door, check for broken tiles, stray sprites, flicker or object
  corruption while opening, fully open and closing. Re-enter the area when the
  route permits, including with Tails nearby if playing Sonic and Tails.
- During CPZ movement, confirm native jump/Spin Dash/ring SFX coexist with MD+
  music; pause/unpause before and after a door. Exercise an available temporary
  native-music event and its MD+ restoration. Check the DEZ boss-music hand-off
  as practical, then reset and verify normal startup/music.

Record all nine doors as pass, fail or not reached, plus music/pause/reset results.
At checklist preparation, hardware qualification was pending. The completed
targeted results and their qualification boundary are recorded above.

## Research only: OOZ2 push springs and Obj48 distinction

The complete Fixed File changes precisely two entries, both **Obj45**:

| Retail index | Object | Subtype correction | Selected status |
| --- | --- | --- | --- |
| 139 | Obj45 push spring | `$30 -> $02` | Excluded |
| 140 | Obj45 push spring | `$30 -> $02` | Excluded |

Their complete placements and flags are derived from the pinned dependency
only. Both sit in the later launcher-network section. They are compressible
push springs, not members of Obj48's controlled ball-transport mechanism.

Pinned Obj45 shifts subtype right three to choose orientation. With the current
Bugfixed guard, `$30 >> 3 = 6`, masked by 2 gives 2: horizontal routine, frame
10, width 20. Its strength bit 1 is clear, selecting `-$1000`; X-flip makes it
launch left. Retail's `$E` mask leaves the invalid table offset 6, which happens
to branch to horizontal initialization as upstream explains. `$02` selects
vertical routine, frame 0, width 16, bit 1 set selecting weak `-$A00` upward
launch, no twirl, no plane change and no transverse-speed cancellation. The
upper `$30` bits determine orientation here; they are not ignored. Compiled
initialization confirms both routine/frame/width/strength results. The guard
already prevents the invalid table lookup but does not provide `$02` behaviour.

Pinned Obj48 and `OOZ/Cannon.xml` do confirm the anticipated names:
0 = In Top, 1 = In Right, 2 = In Bottom, 3 = In Left. Obj48 masks `$F` for its
render-property table, derives launch velocity from `(subtype + 1) & 3`
(subtracting 2 for X-flip), and uses bit 7 for last-cannon release. For a
hypothetical unflipped Obj48, `$30` acts like 0, with rightward exit;
`$02` gives leftward exit. Bits 4/5 in `$30` have no further Obj48 effect.
Those rules do **not** explain the actual Obj45 placements.

Executing pinned KosDec shows both springs just left of a wall beginning at
X `$1E40`: foreground chunks `$24` and `$26`. The upper placement is beneath
primary-solid blocks at Y `$0210-$021F`; the lower is above a primary-solid
floor at Y `$0360`. Geometry supports investigating an upward spring at the
lower placement, but does not establish a universally safe upward route at
the upper one, especially across collision planes. Nearby ball-launcher
directions cannot prove a push-spring correction. No independent official later
version evidence is available in the pinned checkout/history. **Recommendation:**
keep this deferred; test a separate Obj45-specific candidate at both placements
before approving it. Do not justify it as an Obj48 direction-bit correction.

### Targeted level-data MiSTer hardware qualification

Lloyd reported successful targeted testing on **MiSTer FPGA, Mega Drive core
`26.06.03`**, using the ROM presented as
`Sonic 2 - Addryu Mega-CD Remix MD+ (Bugfixed) - Level Data Test.md`.
The generated `build/sonic2-mdplus-bugfixed.md` was independently checked against
the strict verification profile and existing clean Linux build evidence before
recording this qualification. Its exact identity is:

- Size: `2,097,152` bytes.
- Stored and calculated checksum: `C145`.
- MD5: `50e81d88e257f8d14608e57801b628c5`.
- SHA-256: `f33a1946a609b8045bb56ffce2aba05196190965fed6ddf5f8eb3b80c52a0c52`.

The reported hardware observations are separate from the source-policy and
compiled/automated evidence above:

| Targeted check | Reported hardware observation | Result |
| --- | --- | --- |
| EHZ2 cave wall (retail index 29) | Wall above the first cave prevented the high rolling-jump wall clip | PASS |
| EHZ2 wall/spring guard (retail index 64) | Invisible wall prevented the Super Sonic floor clip | PASS |
| EHZ2 corridor pathswapper (retail index 142) | Lower corridor passed the rare stuck-in-floor/wall check | PASS |
| EHZ2 boss/capsule | Progression behaved normally | PASS |
| ARZ2 pathswapper (retail index 119) | Normal loop progression and the problematic approach from below passed | PASS |
| ARZ2 bubble generator (retail index 33) | Deliberately retained generator behaved normally | PASS |
| WFZ diagonal conveyor (retail index 127) | Previously non-functional conveyor moved/carried Sonic as intended | PASS |

EHZ2 was exercised normally and aggressively around all three selected areas.
The WFZ result is for **object `$72`, the diagonal conveyor**, not the later
vertical platform/conveyor machinery. ARZ2's upstream bubble-generator removal
is deliberately excluded; this test confirms the retained generator's behaviour.

Regression sanity on the same exact ROM also passed: native SFX over MD+
music, pause/unpause, MD+ -> temporary native music -> MD+ restoration, and reset.
No obvious object corruption was observed.

**No hardware regression was observed in the targeted scope. This exact
`f33a1946...` released v3.0.1 identity is hardware-qualified on MiSTer Mega Drive
core `26.06.03` for the selected level-data changes and checks reported above.**

The additional qualification evidence chain is:

1. Released v3 `d1668976...` and selective-audio `b04c2fd3...` retain their own
   exact-ROM hardware evidence. Earlier broad Bugfixed/Forge 1P/2P integration
   results remain historical evidence for the ROMs actually tested.
2. Source-policy checks select only the three EHZ2 insertions, ARZ2 pathswapper
   with its bubble retained, and WFZ diagonal conveyor subtype correction.
3. Compiled/binary audits account for every changed byte and symbol, reconstruct
   both complete pre-level ROMs, and establish unchanged unrelated integration
   machinery; automated suites and clean Linux reproduction pass.
4. The exact `C145` / `f33a1946...` Level Data Test candidate passed the targeted
   MiSTer observations above, adding the hardware evidence for these changes.

This is not a new complete Sonic 2 playthrough or a comprehensive retest of every
previous Bugfixed feature. No adoption or hardware testing of unselected Fixed
Files is claimed: CPZ/DEZ door replacements, OOZ launcher/push-spring data,
ARZ2 bubble removal, unrelated object cleanup, ring cleanup and every other
unselected substitution remain excluded.

## Post-v3 selective audio-data candidate

This section records the historical intermediate selective-audio stage. Its
`6AD6` / `b04c2fd3...` identity precedes the level-data changes; the final released
v3.0.1 Bugfixed identity is `C145` / `f33a1946...` above. The audio corrections
described here remain selected in v3.0.1.

The pinned upstream commit is unchanged. `FixMusicAndSFXDataBugs` remains
globally disabled in `s2.asm` and the separate `build.lua` compressed-song
environment. `FixDriverBugs` remains zero. Exactly these two inputs are selected
through `bugfixed.apply_policy()`; the Forge adapter does not recreate them:

- **Spin Dash Release:** select the upstream fixed FM5 header transpose `$10`
  instead of `$90`, leaving the entire remaining SFX unchanged. Upstream commit
  `8914322db1c269f263b77448466288530fd3ed63`, titled
  "Restored vanilla overflow behaviour to zFMSetFreq", explains that retail
  overflow hides this malformed transpose. This corrects data; an audible
  Spin Dash difference with the current driver is not assumed.
- **Credits:** select positive `$C` at the EHZ 2P PSG2-to-CNZ PSG2 transition
  (`$D0->$DC`), instead of negative `$C`, preventing invalid frequency-table
  access. The following `$E8`, call, `$18` and note sequence stay unchanged.
  Upstream's fixed path omits the later `$C*2` compensation. Forge changes that
  command's operand to zero: `E9 18 -> E9 00`. The current Z80 handler adds the
  argument to the transpose and returns, so zero preserves the corrected pitch.
  Retaining its two-byte width preserves every song/SFX address and pointer.

At this intermediate stage, Sky Chase and Death Egg remained excluded. No Z80
fixes, Fixed Files, alternate 2P sprite mechanism, level-data polishing, door-data
or launcher-data changes were introduced. MD+ routes, transactions, WAV
conversion and loop points stay unchanged. Production remains byte-identical to v3.0.0.

Preparation hash-checks five pristine files, requires every contextual anchor
exactly once (existing page-flip counts are retained), computes all five outputs
and checks all five exact post-policy hashes before writing anything. Missing,
duplicated, unexpected and already-patched inputs fail closed. Every other
tracked input must remain unchanged. The pristine and post-policy tables below
include the two new audio files; the previous three hashes are unchanged.

### Compiled evidence and complete v3 diff

`tests/check_audio_data_binary.py` checks both stock Bugfixed and Bugfixed MD+.
It reconstructs the full v3 images by reversing only the three data operands
and restoring the old header checksums, then requires the released SHA-256
identities. No byte outside those exact changes is masked. It also freezes the
complete parsed v3 symbol maps: 23,349 stock symbols and 23,467 MD+ symbols,
including all ROM, sound-data, Forge, Z80 and RAM addresses.

| ROM offset | v3 | Candidate | Meaning |
| --- | --- | --- | --- |
| `$106712` | `F4` | `0C` | Credits: `E9 F4 -> E9 0C` |
| `$10674E` | `18` | `00` | Credits: `E9 18 -> E9 00` |
| `$107449` | `90` | `10` | Spin Dash Release FM5 header transpose |
| Stock `$00018F` | `EC` | `6C` | Checksum `FDEC -> FD6C` |
| MD+ `$00018E` | `6B` | `6A` | Checksum high byte |
| MD+ `$00018F` | `56` | `D6` | Checksum low byte: `6B56 -> 6AD6` |

These are the complete diffs: four stock bytes and five MD+ bytes. Both ROMs
remain 2,097,152 bytes. All symbol maps are identical to v3; Forge stays at
`$108000-$1086C0`, sound data ends at `$107FEC`, Z80 banks and RAM do not move.
Compressed and loaded driver identities remain exactly as recorded below.
There is no finished-ROM patch or unexplained difference.

Both driver payloads start at `$0ED0E8`, with identical bytes before and after:

- Stock: 3,942 compressed bytes, SHA-256
  `20f87dc2d04ea396781d1136af4c448be60f8c984adafcb507bc24be81cfd702`;
  4,872 loaded bytes, SHA-256
  `bb6d42f875017b434f54ab76d02b476d0efbdc13db23e327d07080cfc84a477f`.
- MD+: 4,011 compressed bytes, SHA-256
  `392dd33e5c34d555d993dce0dd33133d36737faa3b6c1e473b3278a75713af33`;
  4,986 loaded bytes, SHA-256
  `f2883990453ba7deedc682b3970be0d2c73fea99a566a30d43362c2769ac7041`.

The compressed-region-with-padding MD+ hash remains
`b9788df25eb06f84bacdb03b620c256a72001c533c08770faa7a93826ef985e1`.
The eight bankswitch expansions retain their targets and the same 34-byte
Production-to-Bugfixed relocation audit; this phase adds no Z80 relocation.

Disposable standalone assemblies of pristine upstream Spin Dash/Credits with
`FixMusicAndSFXDataBugs=1` provide independent compiled references. The Spin
Dash block `$107441-$107482` is exactly 65 fixed upstream bytes. The Credits
block `$105797-$106E91` is exactly 5,882 bytes. Its fixed upstream reference is
two bytes shorter; the test checks every Credits label's resulting two-byte
shift and all 173 emitted pointers, restores only those pointer addresses and
inserts `E9 00` at `$10674D`. The entire normalized reference then equals the
candidate. These reference wrappers are deleted and are not supported variants.
Both stock and MD+ contain identical complete selected data blocks.

The unchanged compiled `cfChangeTransposition` handler is `DD 86 05 DD 77 05 C9`.
Z80 execution checks zero adjustment for every possible starting transpose and
the corrected `$D0 + $0C = $DC`, `$DC + $E8 = $C4`, `$C4 + $18 = $DC` sequence.
The surrounding Credits bytes are protected by the complete v3 reconstruction
and upstream-reference equality, including the original call/note sequence.

Excluded complete compressed song blocks retain their exact v3 bytes:

| Song | ROM span (exclusive end) | Bytes | SHA-256 |
| --- | --- | --- | --- |
| Sky Chase | `$103A6F-$103D8C` | 797 | `a34c80a453485677040838040f8835cf19b085e7cfbb7aa695018a51bc2e1aa0` |
| Death Egg | `$10236B-$1026ED` | 898 | `d997397b4a712631bf47cef97466d282072ecbd69d658dc90328ffcc0be97427` |

The audit writes the complete byte accounting to ignored
`build/selective-audio-diff.json`. Existing stock and MD+ integration audits,
all three CPU suites for each flavour, and the Production `fixBugs=1` negative
control remain required. CI runs the new selective compiled-data audit too.

### Exact candidate identities

Both identities have software validation. The Bugfixed MD+ identity also passed
the targeted MiSTer hardware qualification recorded below.

| Field | Stock Bugfixed | Bugfixed MD+ |
| --- | --- | --- |
| Size | `2,097,152` | `2,097,152` |
| Stored/calculated checksum | `FD6C` | `6AD6` |
| MD5 | `4cf0dd1f1698c87d2728a071797b1acb` | `ef060d788f896099075e370195120ff2` |

Stock Bugfixed SHA-256:
`869869560951eaad0fc327057e50e8ae3cf4ea04c877ff81e8c22a0b17cc02fa`.
Bugfixed MD+ SHA-256:
`b04c2fd39e804719db599cca014966b19f07b16140688ee265c1dc759cb2212b`.

Production remains checksum `BE41`, MD5 `9eb40c0601a7c424a0d1ce168b5f40f2`,
SHA-256 `bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`.
Historical v3.0.0 qualification belongs to `d1668976...`. This intermediate
candidate's qualification comes from its own targeted hardware results below.
`docs/releases/v3.0.0.md` is unchanged; v3 did not contain these selective
audio-data fixes.

### Targeted MiSTer hardware qualification

Lloyd reported successful targeted testing of this exact Bugfixed MD+ candidate
on **MiSTer FPGA, Mega Drive core `26.06.03`**:

- Stored and calculated checksum: `6AD6`.
- MD5: `ef060d788f896099075e370195120ff2`.
- SHA-256: `b04c2fd39e804719db599cca014966b19f07b16140688ee265c1dc759cb2212b`.

The reported hardware results were:

- Repeated Spin Dash release testing passed: multiple Spin Dashes, different
  charge lengths and movement directions, combined with other ordinary SFX.
  It sounded normal, with no malformed burst, missing sound, stuck FM channel
  or other audible regression. The current Sonic 2 sound driver's vanilla
  overflow behaviour already masks the malformed `$90` transpose, so this
  result confirms no regression; the source/compiled audit establishes the
  corrected data. It does not establish an audible change from the correction.
- Credits was played all the way through to the end, exercising both the
  corrected PSG2 transition region and the later formerly compensating region.
  Playback sounded normal throughout, with no invalid pitch, garbage notes,
  discontinuity or stuck PSG observed.
- Ordinary native SFX were tested extensively: jump, rings, item boxes,
  badniks, Spin Dash and normal gameplay effects.
- Both acts of Emerald Hill were played, including the boss fight, and part of
  Chemical Plant Act 1 was played. MD+ level playback and native SFX coexistence
  remained correct.
- MD+ -> native -> MD+ ownership transitions remained correct. The
  invincibility round trip passed. Pause/unpause was tested repeatedly and passed.
- The Death Egg sequence passed: MD+ zone music -> native Metal Sonic boss
  music -> restoration to MD+ zone music -> native final-boss music -> ending
  transition.
- The level-select cheat remained functional.

**No hardware regression was observed. This exact `b04c2fd3...` candidate is now
hardware-qualified on MiSTer Mega Drive core `26.06.03` for the selective post-v3
audio-data polish and the targeted scope reported above.**

The selective audio qualification evidence chain is:

1. v3.0.0 Bugfixed `d1668976...` remains the historical released
   hardware-qualified baseline.
2. Post-v3 software work selectively corrects only Spin Dash Release and Credits
   data through the authoritative policy.
3. Exact binary accounting establishes only the three intended data operands
   and header checksum changes: five changed bytes in Bugfixed MD+.
4. The exact `b04c2fd3...` candidate then passed the targeted hardware scope above.
5. That exact candidate is now hardware-qualified for the selective post-v3
   audio-data polish.

This candidate did not undergo a new full-game playthrough or comprehensive 2P
soak. Earlier broad 1P/2P results remain historical evidence for their exact ROMs.

## Initial policy

Enable `fixBugs = 1` for ordinary upstream main-game inline corrections,
including code, objects, rendering, collision, camera and mappings, except for
the exclusions below. Use the corrected upstream branches directly; do not
reimplement individual fixes or add a broad set of feature switches.

Excluded or deferred:

- **Z80 driver fixes:** generated `s2.sounddriver.asm` sets `FixDriverBugs = 0`.
  Forge's own Stage 4 additions are retained and separately audited below.
- **Global music/SFX data fixes:** generated `s2.asm` sets
  `FixMusicAndSFXDataBugs = 0`; unchanged, hash-locked `build.lua` also sets it
  to zero for compressed songs. Only Spin Dash Release and Credits are selected
  by exact source transformations below. Sky Chase and Death Egg remain excluded.
- **Complete 2P sprite-table page flip:** `ForgeFix2PSpritePageFlip = 0` gates
  all eleven associated conditionals. Alternate tables consume all of
  `$FFF100-$FFF5FF`, reserved for Forge MD+ state.
- **Upstream Fixed Files:** select only the audited EHZ2, selective ARZ2 and WFZ1
  object edits above. All other object/ring/data inputs and the complete reference
  tree remain byte-identical. Further replacements require individual review.

The no-MD+ reference runs upstream `build.lua` without Forge includes. Bugfixed
MD+ starts from that exact curated source policy, then applies Forge. Production
continues to prepare pristine `fixBugs = 0` source. In addition to curated game
code, only the two selected sound/music files and three selected object layouts
change; `FixDriverBugs` and `FixMusicAndSFXDataBugs` remain zero.
These exclusions cover music/SFX **data**
fixes and Z80 driver **logic** fixes. Enabled main-game 68000 fixes can still
change when or how native sound and music requests are queued, restored,
suppressed or faded.

### Significant included game changes

The broad upstream main-game rule includes policy choices beyond local operand
corrections:

- Oil Ocean's advanced background restoration and reconstruction, plus the
  Spin Dash camera-history correction and its paired-byte state representation.
- Runtime workarounds for malformed CPZ/DEZ door data and OOZ spring data.
- Tails' rolling-deceleration change, the CPZ boss liquid-hitbox approximation,
  and ARZ boss arrow and AI-Tails behaviour.
- Multisprite and display-priority corrections, including cases that select a
  fixed fallback priority; Beta-derived ARZ debug visibility; and removal of
  the unusable CNZ debug-menu object entry.

The enabled upstream MCZ boss drill-detachment fix contains a mistaken operand
in its facing-right path. Forge corrects that operand from `sub5_x_pos(a0)` to
`sub2_x_pos(a0)` under the same upstream `fixBugs` branch. This is a narrow
correction to the upstream bugfix implementation, not a retail Sonic 2 source
change. The compiled regression exercises both boss orientations.

### ARZ Rising Pillar downstream correction

MiSTer playtesting found that a normal Sonic jump no longer cleared the early
ARZ Act 1 rising pillars. Upstream's `Obj2B` fix correctly improves
rendering/culling: it enables `render_flags.explicit_height`, increases
`width_pixels` from `$10` to `$1C`, and increases display `y_radius` from `$18`
to `$20`. Horizontal collision already uses retail `$1B`. However, passing the
larger radius directly to `SolidObject` also enlarges its vertical collision
half-height by eight pixels throughout the rise.

Forge corrects this unintended collision side effect of the upstream culling
fix, based on observed gameplay and code behaviour. This is a second narrow
downstream correction alongside MCZ, not a reversion of the culling fix or an
upstream-author-confirmed diagnosis. The authoritative `bugfixed.py` policy
retains all three display settings and changes only the collision input:

```asm
    moveq   #0,d2
    move.b  y_radius(a0),d2
    if fixBugs
    ; Forge: retain the culling fix, with retail-equivalent collision height.
    subq.w  #8,d2
    endif
    move.w  d2,d3
    addq.w  #1,d3
```

The pristine `s2.asm` hash below and one exact contextual anchor guard this
transformation. Missing, duplicated or already-corrected anchors fail closed.
There is no finished-ROM patch. No clean, readable size-neutral replacement
was found for the zero-extended byte load plus subtraction; ordinary
`SUBQ.W #8,D2` emits `5142` and adds exactly two bytes of compiled code.

| Display radius | Jumping collision `d2` | Walking collision `d3` |
| --- | --- | --- |
| `$20` | `$18` | `$19` |
| `$24` | `$1C` | `$1D` |
| `$28` | `$20` | `$21` |
| `$2C` | `$24` | `$25` |
| `$30` | `$28` | `$29` |
| `$34` | `$2C` | `$2D` |
| `$38` | `$30` | `$31` |

Compiled tests execute actual initialization and `Obj2B_Main` through the
`SolidObject` entry in retail, stock Bugfixed and Bugfixed MD+. They check every
row, `d1=$1B`, preserved display state, and an actual four-pixel rising step.
The larger radius therefore remains available to rendering/culling. Targeted
MiSTer revalidation of the revised ROM confirmed normal visibility/culling
in both ARZ acts, alongside restored collision behaviour.

| Correction layout observation | Before | Revised |
| --- | --- | --- |
| `Obj2B_Init` | `$25E2A` | `$25E2A` |
| `Obj2B_Main` | `$25E58` | `$25E58` |
| Added collision instruction | None | `$25E68`, two bytes |
| `loc_25ACE` through `loc_25C64` | `$25E82-$26018` | `$25E84-$2601A` |
| Mapping table through exclusive end | `$26022-$2648A` | `$26024-$2648C` |
| Seven jump stubs through exclusive end | `$2648A-$264B4` | `$2648C-$264B6` |
| Existing four-byte alignment padding | 4 bytes | 2 bytes |
| Routine-table word at `$25E28` | `$011E` | `$0120` |
| ARZ debug mapping at `$429E0` | `$2B026022` | `$2B026024` |
| Next object `Obj2C` | `$264B8` | `$264B8` |
| MCZ `Obj57_FallApart` / return | `$317F2` / `$3187C` | Unchanged |
| Pre-loader / aligned loader | `$EC36A` / `$ED000` | Unchanged |
| Forge base / sound banks / RAM | Existing audited maps below | Unchanged |

All 65 changed symbol-table entries (including mapping aliases and piece
boundaries) advance by two bytes. The seven emitted jump stubs also advance by
two. The unmoved routine table and ARZ debug entry update their pillar
targets as shown above. The next object and every existing downstream layout-audit symbol retain
their addresses. Alignment absorbs the insertion before MCZ; the ROM remains
2 MiB. Stock and MD+ were audited independently. The complete compressed Z80
regions, loaded identities and 34-byte bankswitch analysis remain unchanged.

The research-only sections above review the deferred CPZ/DEZ runtime workaround
and OOZ spring corrections. Doors use `$02` in the actual Fixed Files; the runtime
forces `$03`. The OOZ guard and the Obj45 data corrections are not equivalent.
Neither deferred change is part of v3.0.1.

### Complete 2P exclusion

The generated policy decouples seven positive conditions in `s2.asm`: the
`Vint0_noWater` upload path, two normal VInt uploads, `H_Int`, `BuildSprites_2P`,
`BuildSprites_P2`, and the completion signal in `BuildSprites_P2_NextLevel`.

It also decouples **both negative `~~fixBugs` companion conditions** in
`Vint0_noWater`. With `~~ForgeFix2PSpritePageFlip`, retail V-scroll updates and
the P2 HInt scroll copy remain active along with the retail sprite upload.
The compiled `Vint0_noWater` region is byte-identical to stock Production.
This avoids a partial hybrid of the retail and page-flipped VInt paths.

Two conditions in `s2.constants.asm` follow the same flag: alternate-table
allocation and page-state allocation. The listing contains none of
`Sprite_Table_Alternate`, `Sprite_Table_P2_Alternate`,
`Current_sprite_table_page` or `Sprite_table_page_flip_pending`.
It emits the original `$500`-byte unused reservation starting at `$FFF100`.
`Underwater_palette` remains `$FFF080`, `Game_Mode` remains `$FFF600`, and the
sprite-table spill area remains the retail `$80` bytes. The Forge RAM hole is
available for later integration; it is not allocated to Forge in this reference.

## Obj82 collision preservation

This follow-up leaves the hardware-qualified Obj2B correction exactly as above.
Upstream's Obj82 culling fix enables `explicit_height`, retains width `$1C`
and enlarges pillar display `y_radius` from `$30` to `$32`. Its existing
`subq.w #2,d3` restores retail walking collision `$31`, but jumping collision
`d2` remains `$32`. Forge moves the compensation before `move.w d2,d3`,
subtracting from `d2` so both collision values derive from retail `$30`.
Rendering/culling still uses the stored `$32` radius. Frame zero skips the
subtraction. Obj82 was discovered through source/compiled analysis, then
validated on MiSTer after correction. Obj2B was originally discovered from
observed hardware gameplay behaviour. The targeted released-v3 ROM results below
qualify the corrected behaviour without claiming a hardware reproduction of
the preceding Obj82 jumping-height difference.

Exact source before (between the unchanged width setup and SolidObject call):

```asm
    moveq   #0,d2
    move.b  y_radius(a0),d2
    move.w  d2,d3
    addq.w  #1,d3
    if fixBugs
    tst.b   mapping_frame(a0) ; is this a pillar?
    beq.s   .notPillar       ; if not, branch
    subq.w  #2,d3

.notPillar:
    endif
    jsrto   JmpTo23_SolidObject
```

Exact source after (only instruction order and subtraction destination change):

```asm
    moveq   #0,d2
    move.b  y_radius(a0),d2
    if fixBugs
    tst.b   mapping_frame(a0) ; is this a pillar?
    beq.s   .notPillar       ; if not, branch
    subq.w  #2,d2

.notPillar:
    endif
    move.w  d2,d3
    addq.w  #1,d3
    jsrto   JmpTo23_SolidObject
```

The authoritative policy validates the pristine source hash and requires one
exact contextual anchor, including `addi.w #$B,d1` and the SolidObject call.
Missing, duplicate, already-corrected and unexpected anchors fail closed;
unit tests check both the hash gate and contextual gate. The Forge adapter
continues to consume `apply_policy` and validate the post-policy source hash.

### Compiled evidence and layout

Stock Bugfixed and Bugfixed MD+ independently emit the same reordered sequence
at `$02A700-$02A712` (exclusive end), **18 bytes before and after**:

```text
Before: 7400 1428 0016 3602 5243 4A28 001A 6702 5543
After:  7400 1428 0016 4A28 001A 6702 5542 3602 5243
```

The unchanged SolidObject call at `$02A712` is `6100 01A6`. Ten instruction
bytes differ; the only other ROM difference is the checksum low byte at
`$00018F` (stock `ED->EC`, MD+ `57->56`). Exact instruction byte changes:

| Address | Before | After |
| --- | --- | --- |
| `$02A706` | `36` | `4A` |
| `$02A707` | `02` | `28` |
| `$02A708` | `52` | `00` |
| `$02A709` | `43` | `1A` |
| `$02A70A` | `4A` | `67` |
| `$02A70B` | `28` | `02` |
| `$02A70C` | `00` | `55` |
| `$02A70D` | `1A` | `42` |
| `$02A70E` | `67` | `36` |
| `$02A710` | `55` | `52` |

Complete listing symbol-table comparisons find one changed entry in each
Bugfixed build: `last_btst_converted.notPillar`, `$02A712->$02A70E` (-4),
because that local branch target now precedes the two `d3` instructions.
No symbol is added or removed. All other symbol values, downstream object
addresses, alignment/padding, mappings, sound banks, RAM and Forge locations
are unchanged. No frozen address values were updated.

Compiled tests initialize valid subtypes `$10` and `$11` and execute
`Obj82_Main` to the real `SolidObject` entry in all three images:

| Image / valid frame | Explicit height | Width | Display radius | `d1` | `d2` | `d3` |
| --- | --- | --- | --- | --- | --- | --- |
| Retail pillar / 1 | Off | `$1C` | `$30` | `$27` | `$30` | `$31` |
| Corrected stock Bugfixed pillar / 1 | On | `$1C` | `$32` | `$27` | `$30` | `$31` |
| Corrected Bugfixed MD+ pillar / 1 | On | `$1C` | `$32` | `$27` | `$30` | `$31` |
| Retail non-pillar / 0 | Off | `$20` | `$08` | `$2B` | `$08` | `$09` |
| Both corrected non-pillar images / 0 | On | `$20` | `$08` | `$2B` | `$08` | `$09` |

The valid non-pillar tests use `$00` and `$01`; no two-pixel subtraction occurs.
Display state remains unchanged at the collision call. Executing the saved
merged stock Bugfixed output independently confirms the uncorrected pillar
inputs `d1=$27,d2=$32,d3=$31`; no extra upstream fixture is retained.
Obj2B's compiled initialization, all seven heights, horizontal collision and
actual rising-step tests remain unchanged and pass in all three images.

### Identity transition and reproduction

Both stock and MD+ Bugfixed remain 2,097,152 bytes with matching stored and
calculated checksums. The identities before this follow-up are historical:

| Field | Stock before | Stock after |
| --- | --- | --- |
| Checksum | `FDED` | `FDEC` |
| MD5 | `46c95382536445188cdb0d63e4d7e305` | `9a0fd894e5fd5e85a354d2578fab7421` |

Stock SHA-256 before:
`51263146131fa2dd70b2fa4c4b5701c6eb7d72d6683bf032358163716bf4ac81`.
Stock SHA-256 after:
`7e8fe718aea8344dfe32931097977c0661bc0dbc9c41cba60e7b7a5e12be933f`.

| Field | MD+ before | MD+ after |
| --- | --- | --- |
| Checksum | `6B57` | `6B56` |
| MD5 | `cbcae2d2153ff7814347bd0013aefde5` | `517f2be577e365296e900cfc04a77782` |

MD+ SHA-256 before:
`f80d983bdc44d5d89f3f7556e644a5b0ff5bf6e519ddacf0a3df73d4406449dc`.
MD+ SHA-256 after:
`d16689760d3c913ff795c7f3b1c3c98b8ad789fb95efdbd50efaa4cd7f95f621`.

The masked curated digest changes from
`1eccd7628d0481f119dcc8c3cabd5772a6d0f4625d6bd6dc0b2b828ee553dee4` to
`66d560a1698458738f98226f8e1460ba80724b0241cb7fab54777ec2e57ca71e`.
Deleted-output rebuilds and a disposable Linux copy with freshly fetched inputs
reproduce all four ROMs. Production MD+ and retail stock remain byte-identical.
All Forge code, RAM, sixteen routes, 21 transactions, signature counts and
stop/ACK, pause, extra-life and speed-shoes CPU regressions remain unchanged.
Complete compressed and loaded Bugfixed Forge Z80 bytes are identical before
and after, with the hashes and 34-byte address-derived analysis below unchanged.
Packages coexist; the revised Bugfixed ROM is included while all sixteen WAVs,
its CUE and the complete Production package retain their previous bytes.

### Obj82 hardware-test placements

These are all Obj82 entries in the normal pinned `level/objects/ARZ_1.bin`
and `ARZ_2.bin`; all Obj82 entries stay pristine within the selective ARZ2 target. `ChkLoadObj`
loads six-byte entries and masks Y with `$FFF`; each listed ID byte is `$82`.
`Obj82_Init` selects property byte offset `(subtype >> 3) & $E` and mapping
frame `offset >> 1`. All entries below select offset 2, frame 1, width `$1C`
and Bugfixed radius `$32`, so **every placement exercises this correction**.
Coordinates are the loaded object centres in level pixels, shown in hexadecimal.

| Act | Object-list byte offset | X | Y | Subtype | Property offset / frame | `$32` pillar |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `$0210` | `$17A0` | `$0525` | `$10` | 2 / 1 | Yes |
| 1 | `$0234` | `$1815` | `$0541` | `$10` | 2 / 1 | Yes |
| 2 | `$0012` | `$0340` | `$0520` | `$11` | 2 / 1 | Yes |
| 2 | `$001E` | `$03C0` | `$0520` | `$11` | 2 / 1 | Yes |
| 2 | `$0024` | `$0440` | `$0520` | `$11` | 2 / 1 | Yes |
| 2 | `$002A` | `$04C0` | `$0520` | `$11` | 2 / 1 | Yes |
| 2 | `$0036` | `$0540` | `$0520` | `$11` | 2 / 1 | Yes |
| 2 | `$017A` | `$0CE5` | `$0616` | `$10` | 2 / 1 | Yes |
| 2 | `$032A` | `$1682` | `$0648` | `$11` | 2 / 1 | Yes |
| 2 | `$0336` | `$1704` | `$062C` | `$10` | 2 / 1 | Yes |
| 2 | `$0378` | `$1870` | `$0510` | `$11` | 2 / 1 | Yes |
| 2 | `$038A` | `$18F0` | `$0510` | `$11` | 2 / 1 | Yes |
| 2 | `$03D2` | `$1A68` | `$076E` | `$11` | 2 / 1 | Yes |
| 2 | `$041A` | `$1C00` | `$04C0` | `$10` | 2 / 1 | Yes |
| 2 | `$0474` | `$1F50` | `$0254` | `$10` | 2 / 1 | Yes |

Subtype `$10` becomes stationary movement type 0 after initialization. `$11`
becomes type 1: standing starts the `$1E`-tick wait, then type 2 falls under
gravity. Unused property entries 4/6 have no valid mapping and are not test cases.
There are no frame-zero Obj82 placements in these two object lists.

Repeatable targeted MiSTer checklist for the exact released-v3 MD+ SHA-256:

- Start with Act 2's `$0340-$0540`, Y `$0520` group; compare ordinary jump contact
  and clearance against retail before standing triggers the falling behaviour.
- Check standing/walking contact and side collision there; confirm the waiting
  and falling transitions still work and visibility/culling remains normal.
- Check stationary subtype `$10` in Act 1 at `$17A0,$0525` and `$1815,$0541`,
  then Act 2 at `$0CE5,$0616` (or the other stationary entries above). Compare
  jumping contact with retail and confirm standing height and culling.
- Recheck the already-qualified Obj2B rising pillars, plus ARZ MD+ playback,
  pause/unpause and one native-music transition. Record the tested hash, core
  version and results separately from the qualification results below.

## Reproducible preparation and build

```sh
make bootstrap
make build-stock-modern
make build-stock-bugfixed
# Equivalent new CLI command:
python3 -m tools.mdplus_builder build-stock-bugfixed
```

Both stock references use the same dependency checkout. The dedicated
`tools/mdplus_builder/bugfixed.py` policy creates a disposable clone of committed
inputs, checks its exact revision and pristine state, then verifies SHA-256
before changing these five source files and the three object layouts listed above:

| Mutated source file | Pristine SHA-256 |
| --- | --- |
| `s2.asm` | `448630bb22c08b5281d143438296e5b9045f6539699ec3724147a7f945c938b9` |
| `s2.constants.asm` | `8de5f4a4e6abc56ea2504afe2f4d58cc8a7a3bfa80e3f3c9f1372231a3ca16cd` |
| `s2.sounddriver.asm` | `ff34692c633f96d50073c24f6ebb72df5c739892c31be6b19b2ae604e76232c7` |
| `sound/sfx/BC - Spin Dash Release.asm` | `fbf3022dda86cddabc84b5aad0849e80bdb1ef5bdf600ca83a5db157c0976f94` |
| `sound/music/9E - Credits.asm` | `df894c3f4a07b3869c6745ece8890500639ccef724d1b0233ecd84b977953914` |

The read-only `build.lua` audit requires SHA-256
`be0f24531604d40159f7b333f9ee7284d15a096ad6bcc3127808b97a2c136175` and the
expected zero-valued compressed-song setting. Exact contextual patterns and
occurrence counts reject unexpected structure even after hash validation.
All tracked files are hashed before and after preparation; only these eight
listed inputs may change. All eight outputs must match explicit post-policy hashes
before any write. The three existing curated hashes stay unchanged. The normal
Lua build must leave those prepared inputs unchanged too. The immutable dependency checkout is never modified.

Run upstream's normal Lua build, including its existing compression, header
checksum and length finalization. Forge performs no finished-ROM patching.
Publish only the verified ROM and listing:

- `build/sonic2-stock-bugfixed.md`
- `build/sonic2-stock-bugfixed.lst`

There is no package command for this development reference. It has its own
`verify_stock_bugfixed()` verifier, independent of `BuildVariant.BUGFIXED`.
The untouched `verify_stock_modern()` audit is unchanged.

## Audited reference identity

| Field | Stock Bugfixed reference |
| --- | --- |
| Size | `2,097,152` bytes |
| Stored / calculated Mega Drive checksum | `53DB` / `53DB` |
| MD5 | `ae378a1f8b41d9e804a0d05cb21f7951` |
| SHA-256 | `9ff0b7b577de237cf2fe9e13415a943b7d30e228a12b96b851793c95ece7184f` |

The curated gameplay, selected audio and selected level data establish these constants.
Rebuilding from a pristine clone after freezing them, then deleting and recreating the published
output, reproduced the exact ROM. An independent clean Linux copy fetched the
pinned source afresh and reproduced all four ROMs byte-for-byte. The policy
does not adjust padding to obtain a desired identity.

The curated code advances the position before the existing loader alignment by
`$600`; the selected objects add `$18` more, for a total `$618` advance from
retail. The same `$1000` boundary is crossed:

| Layout stage | Stock | Curated |
| --- | --- | --- |
| Before loader alignment | `$EBD6A` | `$EC382` |
| After existing `$1000` alignment | `$EC000` | `$ED000` |
| Nominal driver end | `$ED04C` | `$EE04C` |
| DAC start | `$ED100` | `$F5100` |
| Meaningful sound-data end | `$FFFEC` | `$107FEC` |
| Power-of-two ROM padding | `$100000` | `$200000` |

The sound-bank placement after that alignment leaves meaningful data beyond
1 MiB. Unchanged upstream power-of-two padding then yields a 2 MiB ROM. This
size change results from the combined fixes and alignment cascade, not from a
single zone correction.
Listings contain assembler timestamps, so reproducibility means identical ROM
bytes and audited symbols, not byte-identical listing files.

Stock Production remains 1,048,576 bytes, checksum `D951`, MD5
`9feeb724052c39982d432a7851c98d3e`, SHA-256
`193bc4064ce0daf27ea9e908ed246d87ec576cc294833badebb590b6ad8e8f6b`.
Production MD+ remains 2,097,152 bytes, checksum `BE41`, MD5
`9eb40c0601a7c424a0d1ce168b5f40f2`, SHA-256
`bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`.

## Stock compiled evidence

After building both stock references and both MD+ flavours, run:

```sh
PYTHONPATH=. python3 tests/check_stock_bugfixed_binary.py
```

The audit checks actual pinned source preparation, strict identity, deliberate
ROM mutations (including repaired checksums), RAM allocation and compiled retail
sprite behaviour, plus the compiled Obj2B rendering/collision tests above.
It deletes and rebuilds the reference and checks that both
MD+ prepared trees/ROMs, the compatibility symlink, stock Production outputs and
the dependency checkout are unchanged. Existing Production CPU suites and the
current adapter's `fixBugs=1` negative control remain required.

### Z80 relocation evidence

`FixDriverBugs` is zero in the source and listing. Both loaded drivers are
4,872 bytes. Exact raw equality is prevented by relocated ROM data: **34 bytes
differ, all within the nine bank-bit instructions of eight existing bankswitch
macro expansions**. The audit verifies every expansion against its actual ROM
symbol address, then proves every other loaded byte identical to retail.
No arbitrary differences are masked. Retail Saxman EOF behaviour produces the
same loaded bytes as complete decompression for both images.

| Driver evidence | Stock Production | Stock Bugfixed |
| --- | --- | --- |
| Compressed length | 3,940 bytes | 3,942 bytes |

The listing's `Snd_Driver_End = $EE04C` is the nominal upstream reserved
boundary. The actual curated compressed payload is `$F66` bytes, so its
exclusive end is `$ED0E8 + $F66 = $EE04E`, two bytes past that nominal symbol.
The compiled audit checks the length word at `$ED050`, the payload size and
both boundaries without changing the upstream symbol.

Loaded SHA-256 values:

- Stock Production: `5fd429a9e64fe5b2975dae05bb44ced601f1662df1006dd5a8d1c8e505d79e75`
- Stock Bugfixed: `bb6d42f875017b434f54ab76d02b476d0efbdc13db23e327d07080cfc84a477f`

The affected bankswitch operands are `SoundIndex` (four sites), `SndDAC_Start`,
`Snd_Sega`, `MusicPoint1` and `MusicPoint2`. This preserves retail driver
behaviour while correctly addressing the moved data.

### Layout and source-pattern audit

The compiled audit writes the full symbol delta table to
`build/stock-bugfixed-layout.json` and exact adapter-pattern occurrence counts to
`build/stock-bugfixed-pattern-audit.json`. These generated reports and listings
must remain ignored.

The early hooks (`PlayMusic`, `PlaySound`, `PlaySound2`, `sndDriverInput`,
`VintRet`) and post-checksum initialization site at `$382` retain their addresses
and existing source patterns. All exact patterns used by
`_prepare_modern_source()` still occur with the same counts, including the
complete `sndDriverInput` region, pause writes and driver insertion points.
The three pristine hashes necessarily differ after policy preparation; the
Production adapter must continue rejecting those changed inputs.

The loader and compressed-driver start move by `$1000`: `SaxDec_GetByte` becomes
`$ED0DE`, `Snd_Driver` becomes `$ED0E8`, and the compressed-length word becomes
`$ED050`. DAC and music/SFX banks move by `$8000`. In particular, `MusicPoint2`
now starts at **`$100000`**, so Bugfixed Forge starts at `$108000` instead.
The independent integration audit below checks those relocated inputs.

## Forge MD+ software validation

Production preparation is pinned pristine REV01 → Forge adapter →
`build/prepared-modern/`. Bugfixed preparation is pinned pristine REV01 →
`bugfixed.apply_policy()` → exact post-policy hash checks → Forge adapter →
`build/prepared-bugfixed/`. The shared authoritative policy includes both downstream corrections.
`SOURCE_MODERN_DIR` lives in `common.py` to avoid a circular import; no broader
repository reorganisation is involved.

`LayoutProfile` records source policy and hashes, sound-data end, extension
base, live hooks, loader and compressed-driver boundaries, loaded/packed Z80
identities, instruction digests and reference-baseline identity.
`VerificationProfile` independently freezes each ROM identity. One maintained
set of Forge assembly files uses generated layout constants and assertions.
Production's existing constants remain compatibility aliases.

### Post-policy integrity and replaced regions

| File | Required curated SHA-256 before Forge adaptation |
| --- | --- |
| `s2.asm` | `a5e234708be87f5b984d05f6bd4596a28ee792e210822cacd8ed346a9ea8f61f` |
| `s2.constants.asm` | `e6fac75b24da9ecbd2a11ab7d474a3fe1426afa134ef41d9170202f95e77ac54` |
| `s2.sounddriver.asm` | `ce96d9dda766fefa33de23ddccea373b58aceb92ec2a91fba30d998105d667a8` |
| `sound/sfx/BC - Spin Dash Release.asm` | `e405419ccfe906a004c02f8f1ca5e4a56eef68b7315f227b6e25bab029be944a` |
| `sound/music/9E - Credits.asm` | `16a3c7b4e515bbbfc16eb85727dd63d9ff31977b1fb6fcac5868eead1d657843` |

Each adapter accepts only its selected profile's hashes. The Bugfixed generated
include requires `fixBugs=1`, `ForgeFix2PSpritePageFlip=0`, `FixDriverBugs=0`
and `FixMusicAndSFXDataBugs=0`; both variants assert the same RAM boundaries and
allocation. Pristine Production hash checks and its naive `fixBugs=1` negative
control remain enforced.

Exact replacement patterns and counts match in both source policies for
`PlayMusic`, `PlaySound`, `PlaySound2`, `VintRet`, post-checksum GameInit calls,
pause/unpause stores, `SaxDec_GetByte`, RAM reservation and Z80 insertion points.
Those replaced bodies contain no newly enabled curated correction. Their
intended Forge behavior is exercised by the same compiled CPU suites.
The complete `sndDriverInput` source region is also textually unchanged, but its
`if fixBugs` branch selects three SFX slots in curated assembly. Forge retains
that correction: both compiled SFX loops are exactly the same bytes from
`MOVEQ #2,D1` through `DBF` and `RTS`. CPU tests fill all three slots, block each
occupied slot, and prove Music1 and the Z80 voice pointer remain untouched.
The downstream MCZ correction and revised ARZ collision survive; the full reference audit
protects every other curated gameplay byte outside Forge's exact mutations.

### Safe extension and complete address map

The curated listing's final sound object emits `$F2` at `$107FEB`.
`finishBank` only checks that data fit in the `$100000-$107FFF` bank; it emits
no padding or object. The listing reaches `$107FEC`, then upstream power-of-two
`cnop` advances to `$1FFFFF`, followed by its final zero byte and `EndOfRom` at
`$200000`. Every stock byte in `$107FEC-$1FFFFF` is zero. There are no subsequent
upstream tables or generated objects before padding. The next `$8000` boundary
is therefore exactly `$108000`.

Forge occupies only `$108000-$1086BF`, leaving `$107FEC-$107FFF` and
`$1086C0-$1FFFFF` zero. Its end remains inside the existing 2 MiB padding, so the
same upstream padding semantics determine ROM size. Both the source location
assertion and full reference reconstruction guard against overlap.

| Label (ForgeModern prefix) | Production | Bugfixed |
| --- | --- | --- |
| `NativeMusic` | `$100000` | `$108000` |
| `NativeSecond` | `$10000C` | `$10800C` |
| `NativeEnd` | `$100012` | `$108012` |
| `Dispatch` | `$100012` | `$108012` |
| `End` | `$1002B6` | `$1082B6` |
| `BeginHandoff` | `$1002B6` | `$1082B6` |
| `QueueStop` | `$1002BC` | `$1082BC` |
| `CheckReady` | `$1002E8` | `$1082E8` |
| `Input` | `$10032A` | `$10832A` |
| `SaxGetByte` | `$10039C` | `$10839C` |
| `HandoffEnd` | `$1003A8` | `$1083A8` |
| `PlayMusic` | `$1003A8` | `$1083A8` |
| `Route` | `$1003B8` | `$1083B8` |
| `Request` | `$1004B4` | `$1084B4` |
| `DiscardMusic` | `$1004EE` | `$1084EE` |
| `Return` | `$100508` | `$108508` |
| `Complete` | `$10050A` | `$10850A` |
| `PlayPending` | `$10051A` | `$10851A` |
| `ClearTrack` | `$10053C` | `$10853C` |
| `RouteFade` | `$100552` | `$108552` |
| `RouteStop` | `$100562` | `$108562` |
| `Pause` | `$100572` | `$108572` |
| `Unpause` | `$100592` | `$108592` |
| `Speed` | `$1005BA` | `$1085BA` |
| `ExtraLife` | `$1005C4` | `$1085C4` |
| `DuckStart` | `$1005CC` | `$1085CC` |
| `DuckService` | `$1005DE` | `$1085DE` |
| `PlaySound` | `$100614` | `$108614` |
| `PlaySound2` | `$100638` | `$108638` |
| `PauseRequest` | `$100658` | `$108658` |
| `UnpauseRequest` | `$10066A` | `$10866A` |
| `VintReturn` | `$10067C` | `$10867C` |
| `Init` | `$100692` | `$108692` |
| `Reset` | `$10069E` | `$10869E` |
| `RouterEnd` | `$1006C0` | `$1086C0` |

The absolute completion callback is at `$100300` / `$108300`, targeting
`ForgeModernComplete`. Command primitives start at `$100094` / `$108094`, each
26 bytes: Immediate, Fade, Resume, VolumeLow, VolumeNormal, followed by the
sixteen manifest routes in their established order. All backend and router
bytes match across layouts because their branches are relative; the handoff's
absolute callback is independently checked before normalizing its six bytes.

### Curated live hooks and original bytes

All spans below are half-open. Pause locations were read from the curated
listing/binary; they do not retain their Production addresses.

| Curated address/span | Original bytes | Forge replacement |
| --- | --- | --- |
| `$000382-$00038A` | `61000dd461000f82` | Init JSR + NOP, after checksum |
| `$00045E-$000468` | `52b8fe0c4cdf7fff4e73` | VInt return JMP + two NOPs |
| `$00135E-$001370` | `4a38ffe0660611c0ffe04e7511c0ffe44e75` | PlayMusic JMP + six NOPs |
| `$001370-$001376` | `11c0ffe14e75` | PlaySound JMP |
| `$001376-$00137C` | `11c0ffe24e75` | PlaySound2 JMP |
| `$0013C4-$0013CA` | `11fc00feffe0` | PauseRequest JSR |
| `$00140A-$001410` | `11fc00ffffe0` | UnpauseRequest JSR |
| `$00141E-$001424` | `11fc00ffffe0` | UnpauseRequest JSR |
| `$00547A-$005480` | `11fc00ffffe0` | UnpauseRequest JSR |
| `$0ED0DE-$0ED0E8` | `101e53476602584f4e75` | SaxGetByte JMP + two NOPs |

`sndDriverInput` at `$001084-$0010E0` becomes `4ef90010832a` plus 86 zero
bytes. Its exact curated original footprint is:

```text
41f900ffffe043f900a01b800c2900800008662c10280000670642280000600a
10280004671a422800041200040100fe650a0601007f13410003600413400008
720210301001670e4a3110096608423010011380100951c9ffea4e75
```

The compressed-length word at `$0ED050` changes from `0f66` (3,942) to `0fab`
(4,011). The checksum word changes from `53DB` to `C145`; the header ROM end
remains `$001FFFFF`. All other loader bytes remain curated-reference-identical.

### Forge Z80 identity and complete relocation audit

| Field | Bugfixed Forge value |
| --- | --- |
| Compressed start | `$0ED0E8` |
| Compressed bytes | 4,011 (`$FAB`) |
| Actual exclusive payload end | `$0EE093` |
| Nominal assembler `Snd_Driver_End` | `$0EE04C` |
| Audited reserved region | `$0ED0E8-$0F5100` (exclusive end) |
| Loaded bytes | 4,986 (`$137A`) |
| Loaded SHA-256 | `f2883990453ba7deedc682b3970be0d2c73fea99a566a30d43362c2769ac7041` |
| Compressed region + padding SHA-256 | `b9788df25eb06f84bacdb03b620c256a72001c533c08770faa7a93826ef985e1` |

The payload exceeds the nominal reservation label by `$47` bytes; it fits in
existing growth padding. `$0EE093-$0F50FF` is zero. DAC/music/SFX data from
`$0F5100` through `$107FEB` remain byte-identical to curated stock.

Both Forge loaded drivers have the same size and internal Z80 label addresses.
All 34 differing bytes occur in the following eight complete 15-byte bank-switch
expansions. Each begins `AF 1E 01 21 00 60`; its nine following `73`/`77` opcodes
encode actual target-symbol bits 15 through 23. The audit checks each full
expansion for both ROMs, then proves all remaining loaded bytes equal, including
the deliberate Forge additions. `FixDriverBugs` remains zero.

| Loaded offset | Target | Production → Bugfixed target | Changed loaded offsets |
| --- | --- | --- | --- |
| `$009C` | SoundIndex | `$0FEE91` → `$106E91` | `$00A2-$00A7` |
| `$00D4` | SndDAC_Start | `$0ED100` → `$0F5100` | `$00DA-$00DB` |
| `$062E` | SoundIndex | `$0FEE91` → `$106E91` | `$0634-$0639` |
| `$0701` | Snd_Sega | `$0F1E8C` → `$0F9E8C` | `$0707` |
| `$0982` | SoundIndex | `$0FEE91` → `$106E91` | `$0988-$098D` |
| `$0C76` | MusicPoint1 | `$0F0000` → `$0F8000` | `$0C7C` |
| `$0C86` | MusicPoint2 | `$0F8000` → `$100000` | `$0C8C-$0C91` |
| `$0F48` | SoundIndex | `$0FEE91` → `$106E91` | `$0F4E-$0F53` |

For each six-byte difference group, `73 73 73 73 73 77` becomes
`77 77 77 77 77 73`; at `$00DA-$00DB`, `73 77` becomes `77 73`; each single
changed byte is `77` → `73`. There are no other differences.

### Full curated baseline and frozen MD+ identity

The verifier restores exact curated hook bytes and header fields, then zeros
only `$001084-$0010E0`, `$0ED050-$0ED052`, `$0ED0DE-$0F5100` and
`$108000-$1086C0` (exclusive ends). Before normalization, it checks every byte
in these regions using exact trampolines/footprints, length, compressed and
loaded driver hashes, exact backend transactions, handoff digest plus callback,
and router/routine digests. It requires zero padding after Forge.

The full 2 MiB stock reference with those same spans zeroed hashes to
`1e8d2df3382042f15102491dbfa622e5f3ccd3f47f865af83f8c1a69930b87ad`.
The compiled audit also restores actual stock bytes and reproduces the complete
unmasked curated SHA-256
`9ff0b7b577de237cf2fe9e13415a943b7d30e228a12b96b851793c95ece7184f`.
No broad trailing region or gameplay range is ignored. Mutation tests repair
the header checksum and still require rejection outside and inside these spans.

Bugfixed MD+ identity:

- Size: `2,097,152` bytes.
- Stored and calculated checksum: `C145`.
- MD5: `50e81d88e257f8d14608e57801b628c5`.
- SHA-256: `f33a1946a609b8045bb56ffce2aba05196190965fed6ddf5f8eb3b80c52a0c52`.

The first controlled build and a rebuild from deleted prepared/ROM output
reproduce this identity. Production remains at checksum `BE41` and SHA-256
`bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`.
Stock Bugfixed remains at checksum `53DB` and its frozen identity above.

Both variants retain exactly 21 adjacent open/write/close transactions: 42
`$0003F7FA` signatures, 21 `$0003F7FE` signatures, 21 opens and 21 closes.
Startup tests execute the checksum and prove no overlay write precedes it;
a failing checksum never opens the overlay. The curated executable code around
the aperture is protected by the reference audit. Software tests do not model
MiSTer bus timing or audible playback.

Run `tests/check_bugfixed_binary.py` after both stock and MD+ builds. Run the
three existing compiled CPU suites with `FORGE_TEST_VARIANT=bugfixed` as well
as their default Production selection; see the README for exact commands.
They cover backend writes, native fallback, private stop/ACK, routing,
stop/fade/pause/unpause, extra life, speed shoes, SFX queues, VInt and reset/init.
The independent stock audit and Production `fixBugs=1` negative control remain
required. Packages retain the same sixteen WAVs, manifest and CUE policy.

### MiSTer hardware qualification and historical evidence

The **pre-correction** Bugfixed MD+ ROM was tested on Mega Drive core
`26.06.03`: 2,097,152 bytes, checksum `6886`, MD5
`2a3f1072c77082b5f3aa80634e4cdd90`, SHA-256
`8101cf55fcd20ee573be524b1e5e05f5aaecc31560832ffdc136543a5d8e26d6`.
This is historical evidence, not the released-v3 qualified identity. The old stock
Bugfixed reference was checksum `FB1C`, MD5 `3481d68b32dce3b0a01d291eea49c460`,
SHA-256 `80be4afa7b11141dfdf7a36ac3ba4af24c71985dda77b8a6a46f9ae1745b4404`.
Both old Bugfixed identities are superseded by the ARZ policy correction.

The pre-correction hardware results were:

- Complete full-game 1P playthrough; cold boot and warm reset; native/MD+
  transitions; title/native audio; invincibility transition/recovery; Special
  Stage; boss transition/recovery; level completion and act/zone transitions;
  extra life; pause/unpause; death/restart; speed shoes; and attract mode.
  Speed shoes changed gameplay speed without changing MD+ music speed, and
  attract mode sampled EHZ, EHZ 2P, CPZ, ARZ and CNZ MD+ tracks. Multiple
  native-to-MD+ and MD+-to-native-to-MD+ transitions passed. No stuck, doubled
  or missing audio occurred.
  The only reported issue was the early ARZ pillar collision regression.
- Comprehensive 2P soak covering all four 2P zones and acts, more than five
  minutes per act, every item box including player-position swap, correct
  MD+ routing and repeated loops. No sprite glitches, state/input problems or
  audio issues were reported.

The subsequent correction is local to `Obj2B`. The software/layout audit
proved unrelated Forge, Z80, sound, RAM and 2P integration machinery unchanged,
so the earlier broad hardware results remain relevant integration evidence.
They are not a claim that the revised hash repeated the full-game playthrough
or the complete four-zone 2P soak.

The exact Obj2B-corrected Bugfixed MD+ ROM was then revalidated on **MiSTer FPGA,
Mega Drive core `26.06.03`**:

- Size: `2,097,152` bytes.
- Stored and calculated checksum: `6B57`.
- MD5: `cbcae2d2153ff7814347bd0013aefde5`.
- SHA-256: `f80d983bdc44d5d89f3f7556e644a5b0ff5bf6e519ddacf0a3df73d4406449dc`.

Targeted revised-ROM hardware results:

- **ARZ Acts 1 and 2:** ordinary ground-level Sonic jumps clear rising columns
  again; partly and fully raised states behave correctly; visibility/culling
  is normal; standing on a rising column and side collision work correctly.
  These results confirm restored retail-equivalent collision while retaining
  the upstream rendering/culling fix.
- **Audio/lifecycle:** ARZ MD+ playback and looping, MD+-to-invincibility-to-MD+
  transition/recovery, extra life and speed shoes all passed.
- **EHZ 2P sample:** normal play, MD+ playback and looping, and the
  player-position swap item box all passed, with no glitches observed.

**This exact preceding Obj2B hash was hardware-qualified on MiSTer Mega Drive core
`26.06.03`.** The qualification rests on the earlier broad 1P/2P integration
testing, discovery of the isolated ARZ collision regression, the narrow Obj2B
correction, software proof that unrelated integration machinery stayed
unchanged, and successful targeted hardware revalidation of the revised hash.
The pre-correction `8101cf55...` ROM remains historical evidence. Neither that
hash nor the preceding `f80d983b...` qualification is substituted for the
released v3 identity's targeted results below.

#### Released v3 Obj82 hardware qualification

Lloyd reported successful targeted ARZ testing of this exact Bugfixed MD+ ROM
on **MiSTer FPGA, Mega Drive core `26.06.03`**:

- Size: `2,097,152` bytes.
- Stored and calculated checksum: `6B56`.
- MD5: `517f2be577e365296e900cfc04a77782`.
- SHA-256: `d16689760d3c913ff795c7f3b1c3c98b8ad789fb95efdbd50efaa4cd7f95f621`.

The reported hardware results were:

- **Obj82 Act 1, subtype `$10`:** normal jump/contact behaviour, standing,
  walking across the pillar, side collision and correct visibility/culling.
- **Obj82 Act 2, subtype `$11`:** normal jump/contact behaviour, standing,
  walking, side collision, the wait/fall sequence, falling, standing on top
  while falling and correct visibility/culling.
- **Obj2B Act 1 regression check:** standing on top while the pillar rises.
  Lloyd confirmed that the reported rising-pillar observation belongs to this
  Obj2B check; Obj82 subtype `$10` initializes as stationary movement type 0.
- **Audio/lifecycle:** ARZ MD+ playback and looping; pause/unpause;
  MD+ -> invincibility -> MD+ transition/recovery; Act 2 transition to boss
  music; and boss music -> ARZ MD+ restoration.

**No hardware regression was observed. This exact `d1668976...` released v3 hash is
hardware-qualified on MiSTer Mega Drive core `26.06.03`.** The source and
compiled tests establish retained display/culling radius `$32`, jumping
collision `d2=$30` and walking collision `d3=$31`; upstream previously passed
`d2=$32,d3=$31`. The hardware results validate the corrected gameplay and
integration behaviour. The local, size-neutral change leaves Forge placement,
Z80 bytes, audio implementation, Production and the Obj2B correction unchanged.

The qualification evidence chain is:

1. Broad full-game 1P and comprehensive 2P Forge integration testing of
   `8101cf55...` on core `26.06.03`.
2. The hardware-observed Obj2B regression was identified and corrected.
3. The exact `f80d983b...` hash passed targeted Obj2B-era hardware qualification.
4. Obj82's partial collision compensation was identified through source and
   compiled analysis.
5. The size-neutral Obj82 correction restored both retail collision inputs;
   software audits established unchanged unrelated integration behaviour.
6. The exact `d1668976...` hash passed the targeted ARZ tests reported above.
7. The released v3 exact hash is hardware-qualified on that evidence chain.

The released v3 hash did not undergo another full 1P playthrough or comprehensive
2P soak. Those broader results remain evidence from the earlier exact ROM;
the v3-ROM hardware evidence is the targeted ARZ and audio/lifecycle scope
reported here.
