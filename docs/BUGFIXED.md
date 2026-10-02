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
| Bugfixed MD+ | Exact curated policy described here | Hardware-qualified on MiSTer core `26.06.03`, separate layout |

`rom-bugfixed` and its package now integrate curated gameplay fixes with Forge
MD+. Production remains the default hardware-qualified build with its exact
Stage 5 identity. **The revised Bugfixed MD+ hash is hardware-qualified on
MiSTer Mega Drive core `26.06.03`.** The exact identity and evidence chain are
recorded below.

## Initial policy

Enable `fixBugs = 1` for ordinary upstream main-game inline corrections,
including code, objects, rendering, collision, camera and mappings, except for
the exclusions below. Use the corrected upstream branches directly; do not
reimplement individual fixes or add a broad set of feature switches.

Excluded or deferred:

- **Z80 driver fixes:** generated `s2.sounddriver.asm` sets `FixDriverBugs = 0`.
  Forge's own Stage 4 additions are retained and separately audited below.
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

The no-MD+ reference runs upstream `build.lua` without Forge includes. Bugfixed
MD+ starts from that exact curated source policy, then applies Forge. Production
continues to prepare pristine `fixBugs = 0` source. No upstream sound/music
source data is changed; `FixDriverBugs` and `FixMusicAndSFXDataBugs` remain zero.
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
| Stored / calculated Mega Drive checksum | `FDED` / `FDED` |
| MD5 | `46c95382536445188cdb0d63e4d7e305` |
| SHA-256 | `51263146131fa2dd70b2fa4c4b5701c6eb7d72d6683bf032358163716bf4ac81` |

The corrected MCZ and ARZ source established these revised constants. Rebuilding from a
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
| `s2.asm` | `bcfdb7a6738bb673d59f42e7d5b77db7f8998bea40fe367c6221c317799da3d6` |
| `s2.constants.asm` | `e6fac75b24da9ecbd2a11ab7d474a3fe1426afa134ef41d9170202f95e77ac54` |
| `s2.sounddriver.asm` | `ce96d9dda766fefa33de23ddccea373b58aceb92ec2a91fba30d998105d667a8` |

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
(4,011). The checksum word changes from `fded` to `6B57`; the header ROM end
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
`1eccd7628d0481f119dcc8c3cabd5772a6d0f4625d6bd6dc0b2b828ee553dee4`.
The compiled audit also restores actual stock bytes and reproduces the complete
unmasked curated SHA-256
`51263146131fa2dd70b2fa4c4b5701c6eb7d72d6683bf032358163716bf4ac81`.
No broad trailing region or gameplay range is ignored. Mutation tests repair
the header checksum and still require rejection outside and inside these spans.

Bugfixed MD+ identity:

- Size: `2,097,152` bytes.
- Stored and calculated checksum: `6B57`.
- MD5: `cbcae2d2153ff7814347bd0013aefde5`.
- SHA-256: `f80d983bdc44d5d89f3f7556e644a5b0ff5bf6e519ddacf0a3df73d4406449dc`.

The first controlled build and a rebuild from deleted prepared/ROM output
reproduce this identity. Production remains at checksum `BE41` and SHA-256
`bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`.
Stock Bugfixed remains at checksum `FDED` and its frozen identity above.

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
This is historical evidence, not the final qualified identity. The old stock
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

The exact revised Bugfixed MD+ ROM was then revalidated on **MiSTer FPGA,
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

**This exact revised hash is now hardware-qualified on MiSTer Mega Drive core
`26.06.03`.** The qualification rests on the earlier broad 1P/2P integration
testing, discovery of the isolated ARZ collision regression, the narrow Obj2B
correction, software proof that unrelated integration machinery stayed
unchanged, and successful targeted hardware revalidation of the revised hash.
The pre-correction `8101cf55...` ROM is historical evidence and is not the
final qualified identity.
