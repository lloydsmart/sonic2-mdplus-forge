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
| Bugfixed MD+ | Curated policy plus two selected audio-data fixes | Hardware-qualified; targeted post-v3 scope below |

`rom-bugfixed` and its package now integrate curated gameplay fixes with Forge
MD+. Production remains the default hardware-qualified build with its exact
Stage 5 identity. **The released v3 Obj82-corrected hash was hardware-qualified on
MiSTer Mega Drive core `26.06.03` after targeted ARZ testing. The current
selective audio `b04c2fd3...` candidate is also hardware-qualified on that core
for the targeted post-v3 scope below.** The preceding
Obj2B qualification and earlier broad 1P/2P results remain historical evidence;
the exact identities, test scope and evidence chain are recorded below.

## Post-v3 selective audio-data candidate

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

Sky Chase and Death Egg remain excluded. No Z80 fixes, Fixed Files, alternate
2P sprite mechanism, level-data polishing, door-data or launcher-data changes
are introduced. MD+ routes, transactions, WAV conversion and loop points stay
unchanged. Production remains byte-identical to v3.0.0.

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
Historical v3 qualification belongs to `d1668976...`. The new candidate's
qualification comes from its own targeted hardware results below.
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

1. v3.0.0 Bugfixed `d1668976...` remains the released hardware-qualified baseline.
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
- **Upstream Fixed Files:** no replacements are copied, and every other tracked
  input remains byte-identical. Object/ring/data replacements need individual
  selection and review.

The no-MD+ reference runs upstream `build.lua` without Forge includes. Bugfixed
MD+ starts from that exact curated source policy, then applies Forge. Production
continues to prepare pristine `fixBugs = 0` source. Only the two selected
sound/music source files change; `FixDriverBugs` and `FixMusicAndSFXDataBugs` remain zero.
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
and `ARZ_2.bin`, not the excluded Fixed Files replacements. `ChkLoadObj`
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
before changing these five files:

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
All tracked files are hashed before and after preparation; only the five
listed files may change. All five outputs must match explicit post-policy hashes
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
| Stored / calculated Mega Drive checksum | `FD6C` / `FD6C` |
| MD5 | `4cf0dd1f1698c87d2728a071797b1acb` |
| SHA-256 | `869869560951eaad0fc327057e50e8ae3cf4ea04c877ff81e8c22a0b17cc02fa` |

The curated gameplay policy plus selected audio data establish these constants.
Rebuilding from a pristine clone after freezing them, then deleting and recreating the published
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
(4,011). The checksum word changes from `FD6C` to `6AD6`; the header ROM end
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
`d2213ab11b2010e5fdde06fb797fa092e6104bc0ea338700964f57f409d86cec`.
The compiled audit also restores actual stock bytes and reproduces the complete
unmasked curated SHA-256
`869869560951eaad0fc327057e50e8ae3cf4ea04c877ff81e8c22a0b17cc02fa`.
No broad trailing region or gameplay range is ignored. Mutation tests repair
the header checksum and still require rejection outside and inside these spans.

Bugfixed MD+ identity:

- Size: `2,097,152` bytes.
- Stored and calculated checksum: `6AD6`.
- MD5: `ef060d788f896099075e370195120ff2`.
- SHA-256: `b04c2fd39e804719db599cca014966b19f07b16140688ee265c1dc759cb2212b`.

The first controlled build and a rebuild from deleted prepared/ROM output
reproduce this identity. Production remains at checksum `BE41` and SHA-256
`bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44`.
Stock Bugfixed remains at checksum `FD6C` and its frozen identity above.

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
