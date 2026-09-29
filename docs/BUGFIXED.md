# Bugfixed source policy

## Base and current status

The base is `sonicretro/s2disasm` REV01 at immutable commit
`380f37a731bfc720bb0371a35a593184a7ec5e43`.

Three concepts remain separate:

| Build | Source policy | Forge MD+ |
| --- | --- | --- |
| Stock Production reference | Untouched pinned REV01 | None |
| Stock Bugfixed reference | Curated game fixes described here | None |
| Production / Bugfixed MD+ flavours | Current hardware-qualified Stage 5 source transformation | Existing integration |

The stock Bugfixed reference now exists. **`rom-bugfixed` and the Bugfixed MD+
package still produce exactly the Production ROM.** Users must not interpret
the packaged Bugfixed flavour as corrected gameplay. The next phase is MD+
integration against the curated reference and its audited layout.

## Initial policy

Enable `fixBugs = 1` for ordinary upstream main-game inline corrections,
including code, objects, rendering, collision, camera and mappings, except for
the exclusions below. Use the corrected upstream branches directly; do not
reimplement individual fixes or add a broad set of feature switches.

Excluded or deferred:

- **Z80 driver fixes:** generated `s2.sounddriver.asm` sets `FixDriverBugs = 0`.
  Forge's Stage 4 driver extensions and hardware-qualified handoff need a
  separate audit.
- **Music/SFX data fixes:** generated `s2.asm` sets
  `FixMusicAndSFXDataBugs = 0`; unchanged, hash-locked `build.lua` also sets it
  to zero for compressed songs. These separate assembly environments need an
  explicit audio-data audit.
- **Complete 2P sprite-table page flip:** `ForgeFix2PSpritePageFlip = 0` gates
  all eleven associated conditionals. Alternate tables consume all of
  `$FFF100-$FFF5FF`, reserved for Forge MD+ state.
- **Upstream Fixed Files:** no replacements are copied, and every other tracked
  input remains byte-identical. Object/ring/data replacements need individual
  selection and review.
- **Forge MD+ integration:** run upstream `build.lua` with no Forge includes,
  router, overlay transactions or Z80 extensions. Establish the reference
  layout before adapting the fixed-address MD+ integration.

No upstream sound/music source data is changed. The driver source receives only
the flag assignment above. Both MD+ prepared trees retain `fixBugs = 0` and the
existing Stage 4/5 transformations. These exclusions cover music/SFX **data**
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

When Fixed Files are evaluated later, review the CPZ/DEZ door runtime workaround,
which forces subtype 3, for retirement alongside the object-data corrections.
The OOZ spring
runtime guard safely bounds a malformed subtype, while the Fixed File changes
the spring subtype itself and therefore gameplay. Those two OOZ approaches are
not equivalent; the future Fixed Files phase must choose deliberately.

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
before changing these three files:

| Mutated source file | Pristine SHA-256 |
| --- | --- |
| `s2.asm` | `448630bb22c08b5281d143438296e5b9045f6539699ec3724147a7f945c938b9` |
| `s2.constants.asm` | `8de5f4a4e6abc56ea2504afe2f4d58cc8a7a3bfa80e3f3c9f1372231a3ca16cd` |
| `s2.sounddriver.asm` | `ff34692c633f96d50073c24f6ebb72df5c739892c31be6b19b2ae604e76232c7` |

The read-only `build.lua` audit requires SHA-256
`be0f24531604d40159f7b333f9ee7284d15a096ad6bcc3127808b97a2c136175` and the
expected zero-valued compressed-song setting. Exact contextual patterns and
occurrence counts reject unexpected structure even after hash validation.
All tracked files are hashed before and after preparation; only the three
listed files may change. The normal Lua build must leave those prepared inputs
unchanged too. The immutable dependency checkout is never modified.

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
| Stored / calculated Mega Drive checksum | `FB1C` / `FB1C` |
| MD5 | `3481d68b32dce3b0a01d291eea49c460` |
| SHA-256 | `80be4afa7b11141dfdf7a36ac3ba4af24c71985dda77b8a6a46f9ae1745b4404` |

The corrected MCZ source established these constants. Rebuilding from a
pristine clone after freezing them, then deleting and recreating the published
output, reproduced the exact ROM. An independent clean Linux copy fetched the
pinned source afresh and reproduced all four ROMs byte-for-byte. The policy
does not adjust padding to obtain a desired identity.

The combined enabled fixes advance the position before the existing loader
alignment by `$600`, crossing its `$1000` boundary:

| Layout stage | Stock | Curated |
| --- | --- | --- |
| Before loader alignment | `$EBD6A` | `$EC36A` |
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
Both current MD+ flavours remain 2,097,152 bytes, checksum `BE41`, MD5
`9eb40c0601a7c424a0d1ce168b5f40f2`, SHA-256
`bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`.

## Compiled evidence and future integration

After building both stock references and both MD+ flavours, run:

```sh
PYTHONPATH=. python3 tests/check_stock_bugfixed_binary.py
```

The audit checks actual pinned source preparation, strict identity, deliberate
ROM mutations (including repaired checksums), RAM allocation and compiled retail
sprite behaviour. It deletes and rebuilds the reference and checks that both
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
now starts at **`$100000`, the current Forge extension address**. Future
integration must deliberately place the extension and re-audit loader bounds,
bank selection, compression sizes and binary expectations. Matching source
patterns alone do not make the current fixed-address adapter safe for this ROM.

This reference has not been hardware-qualified as a gameplay release. Hardware
qualification and Forge MD+ integration belong to the next phase; this change
establishes the source policy and deterministic development baseline.
