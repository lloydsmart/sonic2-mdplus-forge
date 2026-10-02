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
  identity, layout and isolated prepared, ROM and package outputs. It is
  hardware-qualified on MiSTer Mega Drive core `26.06.03`. Reuse `apply_policy`;
  do not reconstruct or change the curated policy inside the Forge adapter. Keep Z80
  and music/SFX data fixes off, exclude Fixed Files and the complete alternate
  2P sprite mechanism, and preserve the `$FFF100-$FFF5FF` RAM hole and Forge
  allocations. Audit layout changes independently for both variants.
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
Audio changes require an FFmpeg conversion test using non-copyrighted
synthetic input.

## Commits and releases

- Use focused commits with a clear imperative subject.
- Sign commits and tags when the maintainer's signing setup is available.
- Do not publish generated game or soundtrack content as GitHub release assets.
- Update `CHANGELOG.md` for user-visible changes.
