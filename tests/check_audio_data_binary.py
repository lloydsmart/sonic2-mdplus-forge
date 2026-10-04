"""Selective audio audit after both stock and MD+ builds; no reference variant.

Reconstruct both released v3 images exactly and assemble pristine upstream's
fixed selected data in disposable wrappers. All generated material stays in build/.
"""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import z80
from door_data_evidence import restore_v301
from level_data_evidence import pre_level_symbols, restore_pre_level

from tools.mdplus_builder import bugfixed, modern
from tools.mdplus_builder.common import BUILD, BuildError, run
from tools.mdplus_builder.driver import saxman_decode
from tools.mdplus_builder.source import _clone_at, genesis_checksum
from tools.mdplus_builder.variants import BuildVariant

V3 = {
    'stock': ('FDEC', '7e8fe718aea8344dfe32931097977c0661bc0dbc9c41cba60e7b7a5e12be933f',
              'fa3e71943d4f3e2ed5ba99c31fa021f83e6f9356be100fa188a1b2135fcf9625'),
    'mdplus': ('6B56', 'd16689760d3c913ff795c7f3b1c3c98b8ad789fb95efdbd50efaa4cd7f95f621',
               '8ec6707534a3f112a41e9df92d224f7f58b4eda01eb072616bc297549db6bf3b'),
}
# Only three source-data operands; opcode, header, pointers and all other data stay put.
OPERANDS = {0x106712: (0xF4, 0x0C), 0x10674E: (0x18, 0x00), 0x107449: (0x90, 0x10)}
EXCLUDED = {
    'Sky Chase': ('Mus_SCZ', 'Mus_OOZ', 797,
                  'a34c80a453485677040838040f8835cf19b085e7cfbb7aa695018a51bc2e1aa0'),
    'Death Egg': ('Mus_DEZ', 'Mus_SpecStage', 898,
                  'd997397b4a712631bf47cef97466d282072ecbd69d658dc90328ffcc0be97427'),
}


class SelectiveAudioBinaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.images = {
            'stock': (bugfixed.STOCK_BUGFIXED_ROM_PATH.read_bytes(),
                      modern.modern_symbols(bugfixed.STOCK_BUGFIXED_LISTING_PATH)),
            'mdplus': (BuildVariant.BUGFIXED.rom_path.read_bytes(),
                       modern.modern_symbols(BuildVariant.BUGFIXED.prepared_dir / 's2.lst')),
        }

    def test_complete_v3_binary_diff_and_all_symbol_addresses(self):
        report = {}
        for name, (rom, symbols) in self.images.items():
            listing = (bugfixed.STOCK_BUGFIXED_LISTING_PATH if name == 'stock' else
                       BuildVariant.BUGFIXED.prepared_dir / 's2.lst')
            rom, symbols = restore_v301(rom, symbols, listing, name)
            rom = restore_pre_level(rom, symbols, name)
            symbols = pre_level_symbols(symbols)
            old_checksum, old_sha256, symbol_sha256 = V3[name]
            self.assertEqual(len(rom), 2_097_152)
            # Freeze the entire parsed v3 symbol map, including sound, Z80 and RAM.
            self.assertEqual(hashlib.sha256(json.dumps(symbols, sort_keys=True).encode()).hexdigest(),
                             symbol_sha256, name)
            baseline = bytearray(rom)
            for offset, (old, new) in OPERANDS.items():
                self.assertEqual(rom[offset], new)
                baseline[offset] = old
            baseline[0x18E:0x190] = bytes.fromhex(old_checksum)
            self.assertEqual(genesis_checksum(baseline), (int(old_checksum, 16),) * 2)
            self.assertEqual(hashlib.sha256(baseline).hexdigest(), old_sha256)
            differences = [{'offset': f'{i:06X}', 'v3': f'{a:02X}', 'candidate': f'{b:02X}'}
                           for i, (a, b) in enumerate(zip(baseline, rom, strict=True)) if a != b]
            self.assertEqual({int(d['offset'], 16) for d in differences},
                             set(OPERANDS) | ({0x18F} if name == 'stock' else {0x18E, 0x18F}))
            report[name] = {'differences': differences, 'v3_sha256': old_sha256,
                            'candidate_sha256': hashlib.sha256(rom).hexdigest(),
                            'symbol_sha256': symbol_sha256}
        (BUILD / 'selective-audio-diff.json').write_text(json.dumps(report, indent=2) + '\n')

    def test_excluded_data_and_global_flags(self):
        for rom, symbols in self.images.values():
            for label, (start, end, size, digest) in EXCLUDED.items():
                data = rom[symbols[start]:symbols[end]]
                self.assertEqual(len(data), size, label)
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest, label)
            self.assertEqual(symbols['FixMusicAndSFXDataBugs'], 0)
            self.assertEqual(symbols['FixDriverBugs'], 0)
            self.assertEqual(symbols['Mus_Credits.is_compressed'], 0)
        for variant in BuildVariant:
            symbols = modern.modern_symbols(variant.prepared_dir / 's2.lst')
            self.assertEqual(symbols['FixMusicAndSFXDataBugs'], 0)
            self.assertEqual((variant.prepared_dir / 'build.lua').read_text().count(
                '\nFixMusicAndSFXDataBugs = 0\n'), 1)
            self.assertIn('dofile("build.lua")',
                          (variant.prepared_dir / 'modern_build.lua').read_text())

    def test_pristine_and_post_policy_hashes_are_independent_and_enforced(self):
        with tempfile.TemporaryDirectory(prefix='audio-policy-', dir=BUILD) as directory:
            work = Path(directory) / 'source'
            _clone_at('', bugfixed.AUDITED_COMMIT, work, modern.SOURCE_MODERN_DIR)
            originals = {name: (work / name).read_bytes() for name in bugfixed.SOURCE_HASHES}
            for name, data in originals.items():
                self.assertEqual(hashlib.sha256(data).hexdigest(), bugfixed.SOURCE_HASHES[name])
                with patch.dict(bugfixed.POST_POLICY_HASHES, {name: '0' * 64}), self.assertRaisesRegex(
                        BuildError, 'post-policy hash changed'):
                    bugfixed.apply_policy(work)
                self.assertEqual({n: (work / n).read_bytes() for n in originals}, originals)
            result = bugfixed.apply_policy(work)
            self.assertEqual(result, bugfixed.POLICY_HASHES)
            for name in bugfixed.AUDIO_PATTERNS:
                self.assertEqual((work / name).read_bytes(), (BuildVariant.BUGFIXED.prepared_dir / name).read_bytes())
                self.assertEqual(originals[name], (BuildVariant.PRODUCTION.prepared_dir / name).read_bytes())

    def test_complete_selected_data_matches_upstream_fixed_semantics(self):
        rom, symbols = self.images['stock']
        with tempfile.TemporaryDirectory(prefix='upstream-audio-reference-', dir=BUILD) as directory:
            work = Path(directory) / 'source'
            _clone_at('', bugfixed.AUDITED_COMMIT, work, modern.SOURCE_MODERN_DIR)
            for stem, file, start, end in (
                ('spin', bugfixed.SPIN_DASH_FILE, 'Sound3C', 'Sound3D'),
                ('credits', bugfixed.CREDITS_FILE, 'Mus_Credits', 'SoundIndex'),
            ):
                base = symbols[start]
                # Pristine selected source only, upstream fixed conditional branches.
                # No s2.asm/build.lua mutation, ROM build or supported extra variant.
                (work / f'{stem}.asm').write_text(
                    ' CPU 68000\n padding off\n'
                    'z80_ptr function x,(x)<<8&$FF00|(x)>>8&$7F|$80\n'
                    'FixMusicAndSFXDataBugs = 1\nSonicDriverVer = 2\n'
                    ' include "sound/_smps2asm_inc.asm"\n'
                    f' phase ${base:X}\n include "{file}"\n dephase\n')
                lua = ('local c=require("build_tools.lua.common"); '
                       f'c.handle_failure(c.assemble_file("{stem}.asm", "{stem}.bin", '
                       '"", "", false, "https://github.com/sonicretro/s2disasm"))')
                run(['lua', '-e', lua], cwd=work)
                reference = bytearray((work / f'{stem}.bin').read_bytes())
                expected = rom[base:symbols[end]]
                if stem == 'spin':
                    self.assertEqual(len(reference), 65)
                    self.assertEqual(reference[8], 0x10)
                else:
                    # Upstream removes E9 18. Forge retains E9 00 to avoid moving
                    # any later song, SFX or pointer. Normalize ONLY that no-op
                    # and the reference's consequent two-byte pointer relocation.
                    neutral = 0x10674D
                    self.assertEqual(expected[0x106711 - base:0x106713 - base], bytes.fromhex('e90c'))
                    self.assertEqual(expected[neutral - base:neutral - base + 4], bytes.fromhex('e900f505'))
                    self.assertEqual(reference[neutral - base:neutral - base + 2], bytes.fromhex('f505'))
                    self.assertEqual(len(reference) + 2, len(expected))
                    rs = modern.modern_symbols(work / 'credits.lst')
                    for label, address in symbols.items():
                        if label.startswith('Credits_') and base <= address < symbols[end]:
                            self.assertEqual(rs[label], address - (2 if address >= neutral + 2 else 0), label)
                    pointers = re.findall(
                        r'([0-9A-F]+) : ([0-9A-F]{4})\s+dc.w\s+z80_ptr\((Credits_\w+)\)',
                        (work / 'credits.lst').read_text())
                    self.assertEqual(len(pointers), 173)
                    for address, emitted, target in pointers:
                        offset = int(address, 16) - base
                        original = ((rs[target] & 0x7FFF) | 0x8000).to_bytes(2, 'little')
                        self.assertEqual(bytes.fromhex(emitted), original)
                        self.assertEqual(reference[offset:offset + 2], original)
                        reference[offset:offset + 2] = ((symbols[target] & 0x7FFF) | 0x8000).to_bytes(2, 'little')
                    reference[neutral - base:neutral - base] = bytes.fromhex('e900')
                self.assertEqual(reference, expected)
                # Both integration paths emit the complete identical selected data.
                md_rom, md_symbols = self.images['mdplus']
                self.assertEqual(md_rom[md_symbols[start]:md_symbols[end]], expected)

    def test_neutral_pitch_executes_current_unchanged_z80_handler(self):
        for rom, symbols in self.images.values():
            start = symbols['Snd_Driver']
            size = int.from_bytes(rom[symbols['movewZ80CompSize'] + 2:symbols['movewZ80CompSize'] + 4], 'big')
            loaded = saxman_decode(rom[start:start + size])
            handler = symbols['cfChangeTransposition']
            self.assertEqual(loaded[handler:handler + 7], bytes.fromhex('dd8605dd7705c9'))
            cpu = z80.Z80Machine()
            cpu.memory[:len(loaded)] = loaded
            cpu.set_breakpoint(0x7000)
            for initial, adjustment in [(i, 0) for i in range(256)] + [(0xD0, 0x0C), (0xDC, 0xE8), (0xC4, 0x18)]:
                cpu.pc, cpu.ix, cpu.a, cpu.sp = handler, 0x1800, adjustment, 0x1B60
                cpu.memory[0x1805] = initial
                cpu.memory[0x1B60:0x1B62] = bytes.fromhex('0070')
                cpu.ticks_to_stop = 1000
                cpu.run()
                self.assertEqual(cpu.pc, 0x7000)
                self.assertEqual(cpu.memory[0x1805], (initial + adjustment) & 0xFF)


if __name__ == '__main__':
    unittest.main()
