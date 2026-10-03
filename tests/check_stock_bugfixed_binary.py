"""Audit both stock references after both MD+ builds; recreate the curated output.

Run with PYTHONPATH=. python tests/check_stock_bugfixed_binary.py.
Detailed layout/pattern evidence is generated only under ignored build/.
"""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from unicorn import UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, Uc
from unicorn.m68k_const import (
    UC_CPU_M68K_M68000,
    UC_M68K_REG_A0,
    UC_M68K_REG_A7,
    UC_M68K_REG_D1,
    UC_M68K_REG_D2,
    UC_M68K_REG_D3,
    UC_M68K_REG_PC,
    UC_M68K_REG_SR,
)

from tools.mdplus_builder import bugfixed, modern
from tools.mdplus_builder.common import BUILD, BuildError
from tools.mdplus_builder.driver import saxman_decode
from tools.mdplus_builder.source import _clone_at, _git_output, genesis_checksum
from tools.mdplus_builder.variants import BuildVariant

# Independent observations from the first controlled build, not verifier constants.
EXPECTED_IDENTITY = (2_097_152, 'FD6C', '4cf0dd1f1698c87d2728a071797b1acb',
                     '869869560951eaad0fc327057e50e8ae3cf4ea04c877ff81e8c22a0b17cc02fa')
LAYOUT = {
    'PlayMusic': (0x135E, 0x135E), 'PlaySound': (0x1370, 0x1370),
    'PlaySound2': (0x1376, 0x1376), 'sndDriverInput': (0x1084, 0x1084),
    'SaxDec_GetByte': (0xEC0DE, 0xED0DE), 'VintRet': (0x45E, 0x45E),
    'GameInit': (0x370, 0x370), 'VDPSetupGame': (0x1158, 0x1158),
    'JmpTo_SoundDriverLoad': (0x130A, 0x130A), 'SoundDriverLoad': (0xEC000, 0xED000),
    'DecompressSoundDriver': (0xEC04A, 0xED04A), 'movewZ80CompSize': (0xEC04E, 0xED04E),
    'Snd_Driver': (0xEC0E8, 0xED0E8), 'Snd_Driver_End': (0xED04C, 0xEE04C),
    'Size_of_Snd_driver_guess': (0xF64, 0xF64),
    'Obj57_FallApart': (0x31358, 0x317F2), 'return_313C4': (0x313C4, 0x3187C),
    'SoundIndex': (0xFEE91, 0x106E91), 'Snd_Sega': (0xF1E8C, 0xF9E8C),
    'MusicPoint1': (0xF0000, 0xF8000), 'MusicPoint2': (0xF8000, 0x100000),
    'SndDAC_Start': (0xED100, 0xF5100), 'SndDAC_End': (0xF0000, 0xF8000),
    'RAM_Start': (0xFF0000, 0xFF0000), 'Underwater_palette': (0xFFF080, 0xFFF080),
    'Game_Mode': (0xFFF600, 0xFFF600), 'CrossResetRAM': (0xFFFE00, 0xFFFE00),
    'Sprite_Table': (0xFFF800, 0xFFF800), 'Sprite_Table_P2': (0xFFDD00, 0xFFDD00),
    'Sprite_Table_End': (0xFFFA80, 0xFFFA80),
    'Vint0_noWater': (0x566, 0x566), 'H_Int': (0xF54, 0xF54),
    'BuildSprites_2P': (0x1694E, 0x16BA2), 'BuildSprites_P2': (0x16A7A, 0x16CCE),
    'BuildSprites_P2_NextLevel': (0x16B78, 0x16DCC),
    'Obj2B_Init': (0x25A6E, 0x25E2A), 'Obj2B_Main': (0x25A9C, 0x25E58),
    'loc_25ACE': (0x25ACE, 0x25E84),
    'loc_25B8E': (0x25B8E, 0x25F44), 'Obj2B_MapUnc_25C6E': (0x25C6E, 0x26024),
    'Map_obj2B_03F6_End': (0x260D6, 0x2648C), 'Obj2C': (0x26104, 0x264B8),
    'Obj82': (0x2A290, 0x2A658), 'Obj82_Init': (0x2A2AA, 0x2A672),
    'Obj82_Main': (0x2A312, 0x2A6DA), 'Obj82_Properties': (0x2A2A2, 0x2A66A),
    'Obj82_Types': (0x2A358, 0x2A728), 'Obj82_MapUnc_2A476': (0x2A476, 0x2A846),
    'Obj83': (0x2A4FC, 0x2A8CC),
}
PAGE_SYMBOLS = ('Sprite_Table_Alternate', 'Sprite_Table_P2_Alternate',
                'Current_sprite_table_page', 'Sprite_table_page_flip_pending')
# All eight bankswitch macro expansions in the retail Z80 driver, with source operand.
BANK_SWITCHES = {0x94: 'SoundIndex', 0xCC: 'SndDAC_Start', 0x626: 'SoundIndex',
                 0x6F4: 'Snd_Sega', 0x975: 'SoundIndex', 0xC69: 'MusicPoint1',
                 0xC79: 'MusicPoint2', 0xF39: 'SoundIndex'}


def snapshot(paths):
    result = {}
    for path in paths:
        files = sorted(path.rglob('*')) if path.is_dir() else [path]
        for file in files:
            if file.is_file():
                result[str(file)] = hashlib.sha256(file.read_bytes()).hexdigest()
            if file.is_symlink():
                result[str(file) + ':link'] = str(file.readlink())
    return result


def driver(rom, symbols):
    metadata = symbols['movewZ80CompSize']
    if rom[metadata:metadata + 2] != bytes.fromhex('3e3c'):
        raise AssertionError('Expected MOVE.W immediate,D7 loader metadata')
    size = int.from_bytes(rom[metadata + 2:metadata + 4], 'big')
    start = symbols['Snd_Driver']
    compressed = rom[start:start + size]
    loaded = saxman_decode(compressed, stock_loader=True)
    if loaded != saxman_decode(compressed):
        raise AssertionError('Retail EOF behaviour changed loaded bytes')
    return compressed, loaded


class StockBugfixedBinaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = modern.STOCK_MODERN_ROM_PATH.read_bytes()
        cls.fixed = bugfixed.STOCK_BUGFIXED_ROM_PATH.read_bytes()
        cls.stock_symbols = modern.modern_symbols(modern.STOCK_MODERN_LISTING_PATH)
        cls.fixed_symbols = modern.modern_symbols(bugfixed.STOCK_BUGFIXED_LISTING_PATH)

    def test_strict_identities_mutations_and_deterministic_rebuild_isolation(self):
        modern.verify_stock_modern(modern.STOCK_MODERN_ROM_PATH)
        result = bugfixed.verify_stock_bugfixed(bugfixed.STOCK_BUGFIXED_ROM_PATH)
        self.assertEqual(tuple(result[k] for k in ('size', 'header_checksum', 'md5', 'sha256')),
                         EXPECTED_IDENTITY)
        # Mutate body AND repair checksum: a checksum-only verifier is insufficient.
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            path = Path(directory) / 'mutation.md'
            for offset in (0x18E, 0x200, 0xED0E8, len(self.fixed) - 1):
                damaged = bytearray(self.fixed)
                damaged[offset] ^= 1
                if offset != 0x18E:
                    damaged[0x18E:0x190] = genesis_checksum(damaged)[1].to_bytes(2, 'big')
                path.write_bytes(damaged)
                with self.subTest(offset=offset), self.assertRaises(BuildError):
                    bugfixed.verify_stock_bugfixed(path)
        protected = [modern.SOURCE_MODERN_DIR, modern.STOCK_MODERN_ROM_PATH,
                     modern.STOCK_MODERN_LISTING_PATH, modern.MODERN_ROM_PATH]
        for variant in BuildVariant:
            protected.extend((variant.prepared_dir, variant.rom_path))
            modern.verify_modern(variant.rom_path, strict_regression=True, variant=variant)
        before = snapshot(protected)
        bugfixed.STOCK_BUGFIXED_ROM_PATH.unlink()
        bugfixed.STOCK_BUGFIXED_LISTING_PATH.unlink()
        bugfixed.build_stock_bugfixed()
        self.assertEqual(bugfixed.STOCK_BUGFIXED_ROM_PATH.read_bytes(), self.fixed)
        self.assertEqual(snapshot(protected), before)
        self.assertNotEqual(BuildVariant.PRODUCTION.rom_path.read_bytes(), BuildVariant.BUGFIXED.rom_path.read_bytes())

    def test_pinned_source_policy_changes_only_five_files(self):
        with tempfile.TemporaryDirectory(prefix='audit-curated-', dir=BUILD) as directory:
            work = Path(directory) / 'source'
            _clone_at('', bugfixed.AUDITED_COMMIT, work, modern.SOURCE_MODERN_DIR)
            before = bugfixed.tracked_hashes(work)
            originals = {name: (work / name).read_bytes() for name in bugfixed.SOURCE_HASHES}
            bugfixed.apply_policy(work)
            after = bugfixed.tracked_hashes(work)
            self.assertEqual({name for name in before if before[name] != after[name]},
                             {'s2.asm', 's2.constants.asm', 's2.sounddriver.asm',
                              'sound/sfx/BC - Spin Dash Release.asm', 'sound/music/9E - Credits.asm'})
            self.assertEqual(set(before), set(after))
            self.assertEqual(set(_git_output(work, 'diff', '--name-only').splitlines()),
                             {'s2.asm', 's2.constants.asm', 's2.sounddriver.asm',
                              'sound/sfx/BC - Spin Dash Release.asm', 'sound/music/9E - Credits.asm'})
            # Every normal object/ring file, Fixed Files replacement, unselected sound source,
            # and the separate compressed-music builder is still pristine.
            self.assertTrue(any(name.startswith('Utility Project Files/Fixed Files/') for name in before))
            for name in before.keys() - bugfixed.SOURCE_HASHES.keys():
                self.assertEqual(before[name], after[name], name)
            main = (work / 's2.asm').read_text()
            self.assertIn('\nfixBugs = 1\n', main)
            self.assertIn('\nForgeFix2PSpritePageFlip = 0 ', main)
            self.assertIn('\nFixMusicAndSFXDataBugs = 0\n', main)
            self.assertIn('\nFixMusicAndSFXDataBugs = 0\n', (work / 'build.lua').read_text())
            self.assertEqual((work / 's2.sounddriver.asm').read_bytes(),
                             originals['s2.sounddriver.asm'].replace(b'FixDriverBugs = fixBugs', b'FixDriverBugs = 0'))
            for name, expected in (('s2.asm', (7, 2)), ('s2.constants.asm', (2, 0))):
                text = (work / name).read_text()
                self.assertEqual((text.count('if ForgeFix2PSpritePageFlip'),
                                  text.count('if ~~ForgeFix2PSpritePageFlip')), expected)
                # Audit all references independently of the replacement anchors.
                stack, references = [], 0
                for line in text.splitlines():
                    stripped = line.strip()
                    if stripped.startswith('if '):
                        stack.append(stripped[3:])
                    elif stripped == 'endif':
                        stack.pop()
                    if any(re.search(r'\b' + symbol + r'\b', line) for symbol in PAGE_SYMBOLS):
                        self.assertIn('ForgeFix2PSpritePageFlip', stack, line)
                        references += 1
                self.assertEqual(references, 19 if name == 's2.asm' else 4)
            self.write_pattern_report(work, originals)

    def write_pattern_report(self, work, originals):
        patterns = {
            's2.asm': {name: getattr(modern, name) for name in (
                'NATIVE_SOURCE', 'TAIL_SOURCE', 'INPUT_START', 'INPUT_END', 'LOADER_SOURCE',
                'SOUND_SOURCE', 'SOUND2_SOURCE', 'VINT_SOURCE', 'RESET_SOURCE')},
            's2.constants.asm': {'RAM_HOLE': modern.RAM_HOLE},
            's2.sounddriver.asm': {
                'Z80_READY': modern.Z80_READY, 'Z80_PAUSE': modern.Z80_PAUSE,
                'Z80_SAVE_END': 'zTracksSaveEnd:\n',
                'Z80_ALIGNMENT': '\tensure1byteoffset 8\nzVolTLMaskTbl:',
                'Z80_TAIL': "; end of Z80 'ROM'"},
        }
        for i, (old, _, _) in enumerate(modern.PAUSE_SOURCES):
            patterns['s2.asm'][f'PAUSE_SOURCE_{i}'] = old
        report = {}
        for name, markers in patterns.items():
            original, curated = originals[name].decode(), (work / name).read_text()
            report[name] = {key: [original.count(value), curated.count(value)] for key, value in markers.items()}
            self.assertEqual({k: a for k, (a, _) in report[name].items()},
                             {k: b for k, (_, b) in report[name].items()})
        # sndDriverInput is transformed as a whole region, not just its markers.
        for text in (originals['s2.asm'].decode(), (work / 's2.asm').read_text()):
            region = text[text.index(modern.INPUT_START):text.index(modern.INPUT_END)]
            report.setdefault('sndDriverInput_region_sha256', []).append(hashlib.sha256(region.encode()).hexdigest())
        self.assertEqual(*report['sndDriverInput_region_sha256'])
        (BUILD / 'stock-bugfixed-pattern-audit.json').write_text(json.dumps(report, indent=2) + '\n')

    def test_page_flip_is_not_assembled_and_ram_hole_remains(self):
        symbols = self.fixed_symbols
        for name in PAGE_SYMBOLS:
            self.assertNotIn(name, symbols)
            self.assertNotIn(name, bugfixed.STOCK_BUGFIXED_LISTING_PATH.read_text())
        for name, value in (('fixBugs', 1), ('ForgeFix2PSpritePageFlip', 0),
                            ('FixDriverBugs', 0), ('FixMusicAndSFXDataBugs', 0)):
            self.assertEqual(symbols[name], value)
        self.assertEqual(symbols['Underwater_palette'] + 0x80, 0xFFF100)
        self.assertEqual(symbols['Game_Mode'], 0xFFF600)
        listing = bugfixed.STOCK_BUGFIXED_LISTING_PATH.read_text()
        self.assertRegex(listing, r'FFF100 : .*ds\.b\s+\$500\s+; \$FFFFF100-\$FFFFF5FF')
        # Both negative companion paths and the retail upload are actually emitted.
        start, end = self.stock_symbols['Vint0_noWater'], self.stock_symbols['Vint_SEGA']
        self.assertEqual(self.fixed[start:end], self.stock[start:end])
        for name, op in (('BuildSprites_2P', '45f8f800'), ('BuildSprites_P2', '4a78f64466fa45f8dd00')):
            address = symbols[name]
            self.assertEqual(self.fixed[address:address + len(bytes.fromhex(op))], bytes.fromhex(op))
        self.assertNotIn(b'\x00\x03\xf7\xfa', self.fixed)
        self.assertNotIn(b'\x00\x03\xf7\xfe', self.fixed)

    def test_retail_z80_bytes_except_exact_bank_relocations(self):
        stock_compressed, stock = driver(self.stock, self.stock_symbols)
        fixed_compressed, fixed = driver(self.fixed, self.fixed_symbols)
        self.assertEqual((len(stock_compressed), len(fixed_compressed), len(stock), len(fixed)),
                         (3940, 3942, 4872, 4872))
        self.assertEqual(hashlib.sha256(stock).hexdigest(),
                         '5fd429a9e64fe5b2975dae05bb44ced601f1662df1006dd5a8d1c8e505d79e75')
        self.assertEqual(hashlib.sha256(fixed).hexdigest(),
                         'bb6d42f875017b434f54ab76d02b476d0efbdc13db23e327d07080cfc84a477f')
        normalized = bytearray(fixed)
        for start, symbol in BANK_SWITCHES.items():
            for data, symbols in ((stock, self.stock_symbols), (fixed, self.fixed_symbols)):
                # XOR A; LD E,1; LD HL,$6000; nine serial bank bits.
                expected = bytes.fromhex('af1e01210060') + bytes(
                    0x73 if symbols[symbol] & (1 << bit) else 0x77 for bit in range(15, 24))
                self.assertEqual(data[start:start + 15], expected)
            normalized[start:start + 15] = stock[start:start + 15]
        self.assertEqual(normalized, stock)
        self.assertEqual(sum(a != b for a, b in zip(stock, fixed, strict=True)), 34)
        self.assertEqual(len(fixed_compressed), 0xF66)
        self.assertEqual(self.fixed_symbols['Snd_Driver'] + len(fixed_compressed), 0xEE04E)
        self.assertEqual(self.fixed_symbols['Snd_Driver_End'], 0xEE04C)  # nominal upstream boundary

    def test_layout_and_emit_report(self):
        rows = []
        for name, expected in LAYOUT.items():
            actual = (self.stock_symbols[name], self.fixed_symbols[name])
            self.assertEqual(actual, expected, name)
            rows.append({'symbol': name, 'stock': f'{actual[0]:06X}', 'bugfixed': f'{actual[1]:06X}',
                         'delta': actual[1] - actual[0]})
        # The reset patch remains AFTER the checksum and covers the same two BSRs.
        self.assertEqual(self.stock[0x382:0x38A], bytes.fromhex('61000dd461000f82'))
        self.assertEqual(self.fixed[0x382:0x38A], self.stock[0x382:0x38A])
        word = (self.stock_symbols['movewZ80CompSize'] + 2,
                self.fixed_symbols['movewZ80CompSize'] + 2)
        self.assertEqual(word, (0xEC050, 0xED050))
        rows.append({'symbol': 'compressed_driver_length_word', 'stock': f'{word[0]:06X}',
                     'bugfixed': f'{word[1]:06X}', 'delta': word[1] - word[0]})
        (BUILD / 'stock-bugfixed-layout.json').write_text(json.dumps(rows, indent=2) + '\n')
        print(json.dumps(rows, indent=2))

    def test_pillar_insertion_and_alignment_are_local(self):
        listing = bugfixed.STOCK_BUGFIXED_LISTING_PATH.read_text()
        self.assertRegex(listing, r'25E68 : 5142\s+subq\.w\s+#8,d2')
        self.assertRegex(listing, r'264B6 : .*align 4')
        self.assertRegex(listing, r'264B8 : .*!org')
        self.assertRegex(listing, r'EC36A : .*align \$1000')
        # All seven Obj2B jump stubs moved by two; the following Obj2C did not.
        for index, target in enumerate(('DisplaySprite', 'DeleteObject', 'MarkObjGone',
                                        'AllocateObjectAfterCurrent', 'Adjust2PArtPointer',
                                        'SolidObject', 'ObjectMove')):
            address = 0x2648C + index * 6
            expected = bytes.fromhex('4ef9') + self.fixed_symbols[target].to_bytes(4, 'big')
            self.assertEqual(self.fixed[address:address + 6], expected)
        self.assertEqual(self.fixed[0x264B6:0x264B8], bytes(2))
        # Unmoved tables must still point to the two moved pillar targets.
        self.assertEqual(int.from_bytes(self.fixed[0x25E28:0x25E2A], 'big'),
                         self.fixed_symbols['loc_25B8E'] - self.fixed_symbols['Obj2B_Index'])
        self.assertEqual(int.from_bytes(self.fixed[0x429E0:0x429E4], 'big'),
                         0x2B000000 | self.fixed_symbols['Obj2B_MapUnc_25C6E'])


class ARZPillarCompiledTests(unittest.TestCase):
    """Execute Obj2B init and movement through the actual SolidObject entry."""

    @classmethod
    def setUpClass(cls):
        cls.images = {
            'retail': (modern.STOCK_MODERN_ROM_PATH, modern.STOCK_MODERN_LISTING_PATH),
            'curated': (bugfixed.STOCK_BUGFIXED_ROM_PATH, bugfixed.STOCK_BUGFIXED_LISTING_PATH),
            'mdplus': (BuildVariant.BUGFIXED.rom_path, BuildVariant.BUGFIXED.prepared_dir / 's2.lst'),
        }
        cls.images = {name: (rom.read_bytes(), modern.modern_symbols(listing))
                      for name, (rom, listing) in cls.images.items()}

    def machine(self, name):
        rom, symbols = self.images[name]
        cpu = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        cpu.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        cpu.mem_map(0, 0x200000)
        cpu.mem_write(0, rom)
        cpu.mem_map(0xFFFF0000, 0x10000)
        obj, stack = 0xFFFFB000, 0xFFFFEF00
        cpu.reg_write(UC_M68K_REG_SR, 0x2700)
        cpu.reg_write(UC_M68K_REG_A0, obj)
        cpu.reg_write(UC_M68K_REG_A7, stack)
        cpu.mem_write(obj + symbols['x_pos'], (0x100).to_bytes(2, 'big'))
        cpu.emu_start(symbols['Obj2B_Init'], symbols['Obj2B_Main'], count=128)
        self.assertEqual(cpu.reg_read(UC_M68K_REG_PC), symbols['Obj2B_Main'])
        self.assertEqual(cpu.reg_read(UC_M68K_REG_A7), stack)
        return cpu, symbols, obj, stack

    def test_culling_initialization_remains_fixed_in_stock_and_mdplus(self):
        for name in self.images:
            with self.subTest(image=name):
                cpu, symbols, obj, _ = self.machine(name)
                flags = cpu.mem_read(obj + symbols['render_flags'], 1)[0]
                explicit = 1 << symbols['render_flags.explicit_height']
                self.assertEqual(bool(flags & explicit), name != 'retail')
                self.assertEqual(cpu.mem_read(obj + symbols['width_pixels'], 1)[0],
                                 0x10 if name == 'retail' else 0x1C)
                self.assertEqual(cpu.mem_read(obj + symbols['y_radius'], 1)[0],
                                 0x18 if name == 'retail' else 0x20)

    def collision(self, name, radius, rising=False):
        cpu, symbols, obj, stack = self.machine(name)
        cpu.mem_write(obj + symbols['y_radius'], bytes((radius,)))
        # Secondary state 4 has finished rising; 2 with timer zero advances a stage.
        cpu.mem_write(obj + symbols['routine_secondary'], bytes((2 if rising else 4,)))
        cpu.mem_write(obj + symbols['objoff_34'], bytes(2))
        for register in (UC_M68K_REG_D1, UC_M68K_REG_D2, UC_M68K_REG_D3):
            cpu.reg_write(register, 0xA5A5FFFF)
        cpu.emu_start(symbols['Obj2B_Main'], symbols['SolidObject'], count=128)
        self.assertEqual(cpu.reg_read(UC_M68K_REG_PC), symbols['SolidObject'])
        self.assertEqual(cpu.reg_read(UC_M68K_REG_A7), stack - 4)  # JSR return only.
        self.assertEqual(cpu.mem_read(obj + symbols['y_radius'], 1)[0],
                         radius + (4 if rising else 0))
        return (cpu.reg_read(UC_M68K_REG_D1), cpu.reg_read(UC_M68K_REG_D2),
                cpu.reg_read(UC_M68K_REG_D3) & 0xFFFF)

    def test_initial_and_all_raised_collision_inputs_match_retail(self):
        for radius in range(0x20, 0x39, 4):
            expected = (0x1B, radius - 8, radius - 7)
            for name in self.images:
                with self.subTest(image=name, display_radius=hex(radius)):
                    actual = self.collision(name, radius - 8 if name == 'retail' else radius)
                    self.assertEqual(actual, expected)

    def test_actual_rising_stage_keeps_display_radius_and_retail_collision(self):
        for name in self.images:
            with self.subTest(image=name):
                actual = self.collision(name, 0x2C if name == 'retail' else 0x34, rising=True)
                self.assertEqual(actual, (0x1B, 0x30, 0x31))


class ARZObj82CompiledTests(unittest.TestCase):
    """Execute valid Obj82 initialization and movement to actual SolidObject."""

    @classmethod
    def setUpClass(cls):
        images = {
            'retail': (modern.STOCK_MODERN_ROM_PATH, modern.STOCK_MODERN_LISTING_PATH),
            'curated': (bugfixed.STOCK_BUGFIXED_ROM_PATH, bugfixed.STOCK_BUGFIXED_LISTING_PATH),
            'mdplus': (BuildVariant.BUGFIXED.rom_path, BuildVariant.BUGFIXED.prepared_dir / 's2.lst'),
        }
        cls.images = {name: (rom.read_bytes(), modern.modern_symbols(listing))
                      for name, (rom, listing) in images.items()}

    def machine(self, name, subtype):
        rom, symbols = self.images[name]
        cpu = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        cpu.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        cpu.mem_map(0, 0x200000)
        cpu.mem_write(0, rom)
        cpu.mem_map(0xFFFF0000, 0x10000)
        obj, stack = 0xFFFFB000, 0xFFFFEF00
        cpu.reg_write(UC_M68K_REG_SR, 0x2700)
        cpu.reg_write(UC_M68K_REG_A0, obj)
        cpu.reg_write(UC_M68K_REG_A7, stack)
        cpu.mem_write(obj + symbols['subtype'], bytes((subtype,)))
        cpu.mem_write(obj + symbols['x_pos'], (0x340).to_bytes(2, 'big'))
        cpu.mem_write(obj + symbols['y_pos'], (0x520).to_bytes(2, 'big'))
        cpu.emu_start(symbols['Obj82_Init'], symbols['Obj82_Main'], count=128)
        self.assertEqual(cpu.reg_read(UC_M68K_REG_PC), symbols['Obj82_Main'])
        self.assertEqual(cpu.reg_read(UC_M68K_REG_A7), stack)
        self.assertEqual(cpu.mem_read(obj + symbols['mapping_frame'], 1)[0], subtype >> 4)
        self.assertEqual(cpu.mem_read(obj + symbols['subtype'], 1)[0], subtype & 0xF)
        flags = cpu.mem_read(obj + symbols['render_flags'], 1)[0]
        self.assertEqual(bool(flags & (1 << symbols['render_flags.explicit_height'])), name != 'retail')
        return cpu, symbols, obj, stack

    def collision(self, name, subtype, width, radius):
        cpu, symbols, obj, stack = self.machine(name, subtype)
        self.assertEqual(cpu.mem_read(obj + symbols['width_pixels'], 1)[0], width)
        self.assertEqual(cpu.mem_read(obj + symbols['y_radius'], 1)[0], radius)
        # The real routine calls SolidObject only for an on-screen object.
        flags = cpu.mem_read(obj + symbols['render_flags'], 1)[0]
        cpu.mem_write(obj + symbols['render_flags'], bytes((flags | (1 << symbols['render_flags.on_screen']),)))
        for register in (UC_M68K_REG_D1, UC_M68K_REG_D2, UC_M68K_REG_D3):
            cpu.reg_write(register, 0xA5A5FFFF)
        cpu.emu_start(symbols['Obj82_Main'], symbols['SolidObject'], count=128)
        self.assertEqual(cpu.reg_read(UC_M68K_REG_PC), symbols['SolidObject'])
        self.assertEqual(cpu.reg_read(UC_M68K_REG_A7), stack - 4)
        self.assertEqual(cpu.mem_read(obj + symbols['y_radius'], 1)[0], radius)
        self.assertEqual(cpu.mem_read(obj + symbols['width_pixels'], 1)[0], width)
        self.assertEqual(cpu.mem_read(obj + symbols['render_flags'], 1)[0], flags | 0x80)
        return (cpu.reg_read(UC_M68K_REG_D1), cpu.reg_read(UC_M68K_REG_D2),
                cpu.reg_read(UC_M68K_REG_D3) & 0xFFFF)

    def test_pillar_visual_state_and_both_collision_heights_match_retail(self):
        # Both subtypes actually occur in ARZ: stationary and waiting to fall.
        for name in self.images:
            for subtype in (0x10, 0x11):
                with self.subTest(image=name, subtype=hex(subtype)):
                    radius = 0x30 if name == 'retail' else 0x32
                    self.assertEqual(self.collision(name, subtype, 0x1C, radius), (0x27, 0x30, 0x31))

    def test_valid_non_pillar_frame_zero_does_not_subtract(self):
        for name in self.images:
            for subtype in (0x00, 0x01):
                with self.subTest(image=name, subtype=hex(subtype)):
                    self.assertEqual(self.collision(name, subtype, 0x20, 8), (0x2B, 8, 9))

    def test_compiled_reordering_is_exact_and_size_neutral(self):
        old = bytes.fromhex('740014280016360252434a28001a67025543')
        fixed = bytes.fromhex('7400142800164a28001a6702554236025243')
        self.assertEqual(len(old), len(fixed))
        for name in ('curated', 'mdplus'):
            with self.subTest(image=name):
                rom, symbols = self.images[name]
                self.assertEqual(rom[0x2A700:0x2A712], fixed)
                self.assertEqual(symbols['last_btst_converted.notPillar'], 0x2A70E)
                self.assertEqual(symbols['Obj82_Types'], 0x2A728)
                self.assertEqual(rom[0x2A712:0x2A716], bytes.fromhex('610001a6'))


class MCZDrillCompiledTests(unittest.TestCase):
    """Execute the actual assembled boss routine through RTS in both orientations."""

    @classmethod
    def setUpClass(cls):
        cls.rom = bugfixed.STOCK_BUGFIXED_ROM_PATH.read_bytes()
        cls.symbols = modern.modern_symbols(bugfixed.STOCK_BUGFIXED_LISTING_PATH)

    def run_drills(self, flipped):
        symbols = self.symbols
        cpu = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        cpu.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        cpu.mem_map(0, 0x200000)
        cpu.mem_write(0, self.rom)
        cpu.mem_map(0xFFFF0000, 0x10000)
        cpu.mem_map(0x400000, 0x1000)
        obj, stack, return_address = 0xFFFFB000, 0xFFFFEF00, 0x400000
        self.assertEqual((symbols['sub5_x_pos'], symbols['sub2_x_pos'],
                          symbols['render_flags.x_flip'], symbols['Boss_Countdown']),
                         (0x22, 0x10, 0, 0xFFF75C))
        for name, value in (('sub5_x_pos', 100), ('sub2_x_pos', 200)):
            cpu.mem_write(obj + symbols[name], value.to_bytes(2, 'big'))
        cpu.mem_write(obj + symbols['render_flags'], bytes((int(flipped),)))
        cpu.mem_write(0xFFFFF75C, bytes(2))
        cpu.reg_write(UC_M68K_REG_SR, 0x2700)
        cpu.reg_write(UC_M68K_REG_A0, obj)
        cpu.reg_write(UC_M68K_REG_A7, stack)
        cpu.mem_write(stack, return_address.to_bytes(4, 'big'))
        cpu.emu_start(symbols['Obj57_FallApart'], return_address, count=256)
        self.assertEqual(cpu.reg_read(UC_M68K_REG_PC), return_address)
        self.assertEqual(cpu.reg_read(UC_M68K_REG_A7), stack + 4)
        return tuple(int.from_bytes(cpu.mem_read(obj + symbols[name], 2), 'big')
                     for name in ('sub5_x_pos', 'sub2_x_pos'))

    def test_unflipped_drills_move_outward(self):
        self.assertEqual(self.run_drills(False), (99, 201))

    def test_flipped_drills_move_outward(self):
        self.assertEqual(self.run_drills(True), (101, 199))


if __name__ == '__main__':
    unittest.main(verbosity=2)
