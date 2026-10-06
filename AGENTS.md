# AGENTS.md

## Project scope

This repository contains reproducible tooling and metadata for building a
user-owned Sonic 2 MD+ package. It must never contain or distribute a Sonic 2
ROM, Sega game assets, Addryu audio, converted soundtrack files, disc images,
or generated MiSTer packages.

## Working rules

- Keep `config/dependencies.json` pinned to immutable commit hashes.
- Treat dependency checkouts under `build/` as generated, read-only inputs.
- Keep all generated material under ignored `build/`, `dist/`, or `inputs/`.
- Production is the default, hardware-qualified flavour. Keep its exact Stage 5
  identity and compatibility symlink unchanged. Bugfixed integrates the frozen
  curated policy in `docs/BUGFIXED.md` with Forge MD+ and has its own strict
  identity, layout and isolated prepared, ROM and package outputs. The released
  v3.0.2 baseline is frozen: stock Bugfixed checksum `9BE7`, SHA-256
  `909e5f229fc4052f3c3c3c9a97c3a6b345117990796b0226dffbc98f88f00bc7`;
  Bugfixed MD+ checksum `0951`, SHA-256
  `e9f56f0efd72844918918f2efdecf6183f5bdabb47f235b61cc511a16942d3b5`.
  The exact MD+ identity is hardware-qualified on MiSTer Mega Drive core
  `26.06.03` for the targeted door-data/runtime-workaround scope and regression
  sanity in `docs/BUGFIXED.md`. Historical v3.0.0, selective-audio `b04c2fd3...`
  and v3.0.1 level-data `f33a1946...` qualifications remain tied to their exact
  identities. Reuse `apply_policy`; do not reconstruct or change the curated
  policy inside the Forge adapter. Keep Z80 fixes and global music/SFX fixes off;
  select only Spin Dash Release and Credits data corrections through the
  authoritative policy. Select only the audited EHZ2, selective ARZ2 (retaining
  its bubble generator) and WFZ1 object corrections from pinned Fixed Files
  references, plus all nine CPZ1/CPZ2/DEZ1 `$02` replacements atomically with
  retirement of both Obj2D runtime `$03` stores. Derive records from the pinned
  references; never vendor placement payloads. OOZ2 Obj45 retail indices
  139/140 must retain subtype `$30`; do not adopt the Fixed Files `$02`
  replacements. MiSTer core `26.06.03` testing at both actual placements
  found the replacement upward vertical behaviour incorrect and the released
  horizontal behaviour correct. Retain the existing Obj45 initialization
  guard unchanged. Revisit these substitutions only with genuinely new
  evidence; the earlier wrong-spring hardware test was discarded. Released
  v3.0.2 identities and version remain unchanged. Issue #26 remains
  unrelated/open. Exclude all other Fixed Files
  and the complete alternate 2P sprite mechanism. Preserve the
  `$FFF100-$FFF5FF` RAM hole and Forge allocations. Audit layout changes
  independently for both variants. Keep historical release documents immutable.
- Do not guess loop points. New default-manifest loops require listening tests
  and MiSTer verification across multiple repetitions.
- Preserve the delayed MD+ overlay activation; opening it before Sonic's
  startup checksum causes the red-screen failure.
- Do not weaken ROM checksum, MD+ signature, PCM format, or sector-alignment
  checks to make a failing build pass.
- Never commit or attach generated `.md`, `.bin`, `.rom`, `.wav`, `.cue`,
  `.iso`, or `.chd` files.

## Validation

Before proposing a change, run:

```sh
ruff check .
npm run lint:markdown
python3 -m compileall -q tools tests
python3 -m unittest discover -s tests -v
python3 -m tools.mdplus_builder validate-manifest --manifest config/tracks.json
```

For source-conversion changes, also run the clean Linux regression described in
the README and confirm that the generated ROM still matches the documented
size, header checksum, MD+ signatures, and SHA-256 value. Run both ROM builds
and `tests/check_bugfixed_binary.py` to check independent identities, curated
baseline preservation and isolation. Run all three compiled CPU suites for both
variants, retaining the Production `fixBugs=1` negative control.
Build both stock references and run `tests/check_stock_bugfixed_binary.py` after
both MD+ builds. Keep the stock Bugfixed strict identity and exclusion audits
independent of the MD+ Bugfixed verification profile.
Run `tests/check_level_data_binary.py` after all four builds for selected-entry
semantics, exclusions, complete pre-level ROM reconstruction and symbol movement.
Run `tests/check_door_data_binary.py` for compiled Obj2D behavior, payload-boundary
audit and complete reversal to the frozen released v3.0.1 stock/MD+ identities.
The previous level/audio audits must reverse the door phase before checking their
unchanged historical baselines. Keep `docs/releases/v3.0.1.md` frozen.
Audio changes require an FFmpeg conversion test using non-copyrighted
synthetic input.

## Commits and releases

- Use focused commits with a clear imperative subject.
- Sign commits and tags when the maintainer's signing setup is available.
- Do not publish generated game or soundtrack content as GitHub release assets.
- Update `CHANGELOG.md` for user-visible changes.
