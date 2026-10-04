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
  v3 identity is hardware-qualified on MiSTer Mega Drive core `26.06.03` after
  targeted Obj82 testing. The exact post-v3 selective audio `b04c2fd3...` candidate
  is hardware-qualified on the same core for the targeted scope in `docs/BUGFIXED.md`.
  Reuse `apply_policy`;
  do not reconstruct or change the curated policy inside the Forge adapter. Keep Z80
  fixes and global music/SFX fixes off; select only Spin Dash Release and Credits
  data corrections through the authoritative policy. Select only the audited EHZ2,
  selective ARZ2 (retaining its bubble generator) and WFZ1 object corrections
  from pinned Fixed Files references. The post-v3.0.1 door candidate also selects
  all nine CPZ1/CPZ2/DEZ1 `$02` replacements atomically with retirement of both
  Obj2D runtime `$03` stores. Derive records from the pinned references; never
  vendor placement payloads. The exact `e9f56f0e...` candidate is hardware-qualified
  on MiSTer Mega Drive core `26.06.03` for the targeted door-data/runtime-workaround
  scope and regression sanity in `docs/BUGFIXED.md`. Exclude all other Fixed Files and the
  complete alternate 2P sprite mechanism. The exact level-data `f33a1946...`
  candidate is hardware-qualified on the same core for the targeted scope in
  `docs/BUGFIXED.md`. Preserve the `$FFF100-$FFF5FF` RAM
  hole and Forge allocations. Audit layout changes independently for both variants.
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
