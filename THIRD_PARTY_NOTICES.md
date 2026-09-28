# Third-party notices

This repository contains original build tooling and does not vendor the
source dependency below. The bootstrap commands fetch its exact
pinned commit into the ignored `build/` directory.

## sonicretro/s2disasm (production source)

- Repository: <https://github.com/sonicretro/s2disasm>
- Pinned commit: `380f37a731bfc720bb0371a35a593184a7ec5e43`
- Normal `bootstrap` fetches it into ignored `build/source-modern/`.
- `bootstrap-modern` is retained only as a compatibility alias.

This is the production Sonic 2 source dependency. Production preparation and
building operate on disposable clones, using upstream's `lua build.lua` and
its bundled native build tools, including upstream's AS assembler. The separate
Macroassembler-AS checkout and Forge bootstrap support used by earlier releases
have been removed; the production toolchain remains unchanged.
`build-stock-modern` remains a separate untouched-upstream audit build, also
using a disposable clone. No source, tools,
Sega assets, or generated ROMs are vendored or redistributed by Forge.
The pinned upstream `readme.md`
states that the material is for informational and educational purposes,
prohibits commercial usage, and disclaims ownership and warranty. Forge's
license does not grant rights to this dependency or the game assets.

## FFmpeg

FFmpeg is a user-installed command-line dependency. Its exact licensing depends
on how the user's binary was configured. No FFmpeg binary or library is
distributed by this repository.

Sonic the Hedgehog, Sonic the Hedgehog 2, Sega, Addryu, MiSTer, and other names
belong to their respective owners. No endorsement is implied.
