"""Post-v3.0.1 door source/data, complete relocation and compiled CPU evidence."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unittest
from collections import Counter
from pathlib import Path

from door_data_evidence import DOORS, RELEASED, SPANS, door_inputs, restore_v301
from unicorn import UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, Uc
from unicorn.m68k_const import (
    UC_CPU_M68K_M68000,
    UC_M68K_REG_A0,
    UC_M68K_REG_A7,
    UC_M68K_REG_D1,
    UC_M68K_REG_D2,
    UC_M68K_REG_D3,
    UC_M68K_REG_D4,
    UC_M68K_REG_PC,
    UC_M68K_REG_SR,
)

from tools.mdplus_builder import bugfixed, modern
from tools.mdplus_builder.common import BUILD, ROOT, SOURCE_MODERN_DIR
from tools.mdplus_builder.source import genesis_checksum
from tools.mdplus_builder.variants import BuildVariant

SYMBOL_HASHES = {
    'stock': '925f1fb62a92a0aa5c094059759e4c47dbee6bb028f7d8a078280d86867e7dd9',
    'mdplus': '3766c109f823d7ef30fa6a3eced197f7fab9e3fd5a2d0563f54bc376997541b3',
}


class DoorMachine:
    object_address = 0xFFFFD800
    stack = 0xFFFFEF00

    def __init__(self, rom, symbols, zone, record=None, subtype=0, flipped=0):
        self.s = symbols
        self.c = c = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        c.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        c.mem_map(0, 0x200000)
        c.mem_write(0, rom)
        c.mem_map(0xFFFF0000, 0x10000)
        c.reg_write(UC_M68K_REG_SR, 0x2700)
        c.reg_write(UC_M68K_REG_A0, self.object_address)
        c.reg_write(UC_M68K_REG_A7, self.stack)
        c.mem_write(symbols['Current_Zone'] | 0xFF000000, bytes((symbols[zone],)))
        # Match ChkLoadObj's Y mask / ROL.W #3 orientation extraction.
        x, y = (0x800, 0x400) if record is None else (
            int.from_bytes(record[:2], 'big'), int.from_bytes(record[2:4], 'big') & 0xFFF)
        if record is not None:
            flipped = (int.from_bytes(record[2:4], 'big') >> 13) & 3
            subtype = record[5]
        self.put('x_pos', x, 2)
        self.put('y_pos', y, 2)
        self.put('status', flipped)
        self.put('render_flags', flipped)
        self.put('subtype', subtype)
        self.run('Obj2D_Init', 'Obj2D_Main')

    def put(self, name, value, size=1):
        self.c.mem_write(self.object_address + self.s[name], value.to_bytes(size, 'big'))

    def get(self, name, size=1):
        return int.from_bytes(self.c.mem_read(self.object_address + self.s[name], size), 'big')

    def run(self, start, end):
        self.c.reg_write(UC_M68K_REG_A7, self.stack)
        self.c.emu_start(self.s[start], self.s[end], count=2000)
        assert self.c.reg_read(UC_M68K_REG_PC) == self.s[end], (start, end)

    def state(self):
        data = bytearray(self.c.mem_read(self.object_address, 0x40))
        # These are the deliberate semantic/relocation changes, checked separately.
        for name, count in (('subtype', 1), ('mapping_frame', 1), ('mappings', 4)):
            data[self.s[name]:self.s[name] + count] = bytes(count)
        return data

    def step(self, x, y, control=0, sidekick=False):
        for name, active in (('MainCharacter', not sidekick), ('Sidekick', sidekick)):
            player = self.s[name] | 0xFF000000
            for field, value in (('x_pos', x if active else 0), ('y_pos', y if active else 0)):
                self.c.mem_write(player + self.s[field], value.to_bytes(2, 'big'))
            self.c.mem_write(player + self.s['obj_control'], bytes((control,)))
        self.run('Obj2D_Main', 'SolidObject')
        return tuple(self.c.reg_read(reg) & 0xFFFF for reg in (
            UC_M68K_REG_D1, UC_M68K_REG_D2, UC_M68K_REG_D3, UC_M68K_REG_D4))


class DoorDataBinaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.images = {}
        cls.reports = {}
        for kind, path, listing in (
            ('stock', bugfixed.STOCK_BUGFIXED_ROM_PATH, bugfixed.STOCK_BUGFIXED_LISTING_PATH),
            ('mdplus', BuildVariant.BUGFIXED.rom_path, BuildVariant.BUGFIXED.prepared_dir / 's2.lst'),
        ):
            rom, symbols = path.read_bytes(), modern.modern_symbols(listing)
            report = {}
            baseline, old_symbols = restore_v301(rom, symbols, listing, kind, report)
            cls.images[kind] = rom, symbols, baseline, old_symbols, listing
            cls.reports[kind] = report

    def test_complete_rom_reconstruction_and_every_symbol(self):
        for kind, (rom, symbols, baseline, old, _) in self.images.items():
            report = self.reports[kind]
            self.assertEqual(report['symbol_sha256'], SYMBOL_HASHES[kind])
            self.assertEqual(hashlib.sha256(baseline).hexdigest(), RELEASED[kind][2])
            self.assertEqual(report['changed_bytes'], 808214)
            self.assertEqual(Counter(f[0] for f in report['fixups']),
                             {'absolute': 2362, 'relative': 60, 'short_branch': 2, 'index_word': 1})
            # Literal whole-tail equality includes loader, banks, Z80, Forge and padding.
            self.assertEqual(rom[0xED000:], baseline[0xED000:])
            for name in ('PlayMusic', 'PlaySound', 'PlaySound2', 'VintRet', 'GameInit',
                         'SoundDriverLoad', 'SaxDec_GetByte', 'Snd_Driver', 'Snd_Driver_End',
                         'MusicPoint1', 'MusicPoint2', 'SoundIndex', 'SndDAC_Start',
                         'RAM_Start', 'Underwater_palette', 'Game_Mode', 'CrossResetRAM'):
                self.assertEqual(symbols[name], old[name], name)
            self.assertEqual(symbols['Obj2D_Init'], old['Obj2D_Init'])
            for name, delta in (('Obj2D_Main', -12), ('Obj2D_MapUnc_11822', -12),
                                ('ArtUnc_Sonic', -32), ('Off_Rings', -256), ('Off_Objects', -512)):
                self.assertEqual(symbols[name] - old[name], delta, name)
        modern.verify_modern(BuildVariant.PRODUCTION.rom_path, strict_regression=True)
        (BUILD / 'door-data-diff.json').write_text(json.dumps(self.reports, indent=2) + '\n')

    def test_reconstruction_rejects_mutations_and_wrong_listing(self):
        rom, symbols, _, _, listing = self.images['mdplus']
        # Check code, assets, padding, selected data, audio, Z80 and Forge. Repair
        # checksum to ensure body coverage does not rely on checksum rejection.
        for offset in (0x2000, 0x11902, 0x11952, 0x50560, 0xE47E2, 0xE6BD8,
                       symbols['Objects_CPZ_1'] + 60 * 6 + 5, 0xEC182,
                       0xED0E8, 0x106E91, 0x108300, 0x1FFFFF):
            damaged = bytearray(rom)
            damaged[offset] ^= 1
            damaged[0x18E:0x190] = genesis_checksum(damaged)[1].to_bytes(2, 'big')
            with self.subTest(offset=hex(offset)), self.assertRaises(AssertionError):
                restore_v301(damaged, symbols, listing, 'mdplus')
        with self.assertRaises(AssertionError):
            restore_v301(rom, symbols, BuildVariant.PRODUCTION.prepared_dir / 's2.lst', 'mdplus')

    def test_pinned_source_and_whole_fixed_files(self):
        inputs = door_inputs()
        pristine = (SOURCE_MODERN_DIR / 's2.asm').read_bytes()
        self.assertEqual(hashlib.sha256(pristine).hexdigest(),
                         '448630bb22c08b5281d143438296e5b9045f6539699ec3724147a7f945c938b9')
        def obj2d(text):
            return text[text.index('Obj2D_Init:'):text.index('Obj2D_Main:')]
        original = obj2d(pristine.decode())
        # Independent context discovery within the pinned Obj2D init only.
        blocks = re.findall(r'    if fixBugs\n.*?    endif\n', original, re.DOTALL)
        self.assertEqual(len(blocks), 2)
        for block in blocks:
            instructions = [line.strip() for line in block.splitlines()[1:-1]
                            if line.strip() and not line.lstrip().startswith(';')]
            self.assertEqual(instructions, ['move.b\t#3,subtype(a0)'])
        current = obj2d((BuildVariant.BUGFIXED.prepared_dir / 's2.asm').read_text())
        expected = original
        for block in blocks:
            expected = expected.replace(block, '')
        # Comments have no executable semantics; verify the complete remaining code.
        def code(text):
            return [line.split(';')[0].rstrip() for line in text.splitlines()
                    if line.split(';')[0].strip()]
        self.assertEqual(code(current), code(expected))
        self.assertNotIn('subtype 3', current)
        self.assertEqual(obj2d((BuildVariant.PRODUCTION.prepared_dir / 's2.asm').read_text()), original)
        for name, (retail, fixed) in inputs.items():
            for variant, expected_data in ((BuildVariant.PRODUCTION, retail), (BuildVariant.BUGFIXED, fixed)):
                self.assertEqual((variant.prepared_dir / f'level/objects/{name}.bin').read_bytes(), expected_data)
        for name in ('EHZ_2', 'ARZ_2', 'WFZ_1'):
            prepared = (BuildVariant.BUGFIXED.prepared_dir / f'level/objects/{name}.bin').read_bytes()
            for rom, symbols, baseline, old, _ in self.images.values():
                a, b = symbols['Objects_' + name], old['Objects_' + name]
                self.assertEqual(rom[a:a + len(prepared)], baseline[b:b + len(prepared)])

    def test_all_nine_initializations_and_mapping_equivalence(self):
        prod = BuildVariant.PRODUCTION.rom_path.read_bytes()
        ps = modern.modern_symbols(BuildVariant.PRODUCTION.prepared_dir / 's2.lst')
        for rom, symbols, baseline, old, _ in self.images.values():
            for image, syms in ((rom, symbols), (baseline, old), (prod, ps)):
                a, b = syms['Map_obj2D_003C'], syms['Map_obj2D_004E']
                self.assertEqual(syms['Map_obj2D_003C_End'] - a, 18)
                self.assertEqual(image[a:a + 18], image[b:b + 18])
                c = syms['Map_obj2D_0008']
                self.assertNotEqual(image[c:c + 18], image[a:a + 18])
            for name, (retail, fixed) in door_inputs().items():
                zone = 'death_egg_zone' if name == 'DEZ_1' else 'chemical_plant_zone'
                for index in DOORS[name][0]:
                    a, b = retail[index * 6:index * 6 + 6], fixed[index * 6:index * 6 + 6]
                    machines = [DoorMachine(image, syms, zone, entry) for image, syms, entry in (
                        (rom, symbols, b), (baseline, old, a), (baseline, old, b),
                        (rom, symbols, a), (prod, ps, a))]
                    self.assertEqual([(m.get('subtype'), m.get('mapping_frame')) for m in machines],
                                     [(2, 2), (3, 3), (3, 3), (0, 0), (0, 0)])
                    for m in machines[1:]:
                        self.assertEqual(m.state(), machines[0].state())
                    for m, syms in zip(machines, (symbols, old, old, symbols, ps), strict=True):
                        self.assertEqual(m.get('mappings', 4), syms['Obj2D_MapUnc_11822'])

    def test_compiled_trigger_boundaries_collision_and_open_close(self):
        # Actual Obj2D_Main and CheckCharacter execute through the SolidObject
        # call boundary. Compare its complete object state and collision arguments.
        for rom, symbols, baseline, old, _ in self.images.values():
            for name, (retail, fixed) in door_inputs().items():
                zone = 'death_egg_zone' if name == 'DEZ_1' else 'chemical_plant_zone'
                for index in DOORS[name][0]:
                    pair = [DoorMachine(image, syms, zone, data[index * 6:index * 6 + 6])
                            for image, syms, data in ((rom, symbols, fixed), (baseline, old, retail))]
                    m = pair[0]
                    x, y = m.get('x_pos', 2), m.get('objoff_32', 2)
                    left, right = m.get('objoff_38', 2), m.get('objoff_3A', 2)
                    trigger_x = x + 1 if m.get('status') & 1 else x - 1
                    scenarios = ([(trigger_x, y, 0, False)] * 10 +
                                 [(left - 1, y, 0, False)] * 10 +
                                 [(trigger_x, y, 0, True)] * 10 +
                                 [(trigger_x, y, 0x80, False)] * 10 +
                                 [(px, py, 0, False) for px in (left - 1, left, x - 1, x, right - 1, right)
                                  for py in (y - 33, y - 32, y + 31, y + 32)])
                    for step, (px, py, control, sidekick) in enumerate(scenarios):
                        outputs = [machine.step(px, py, control, sidekick) for machine in pair]
                        self.assertEqual(outputs[0], outputs[1])
                        self.assertEqual(outputs[0], (19, 32, 33, x))
                        self.assertEqual(pair[0].state(), pair[1].state())
                        if step in (9, 19, 29, 39):
                            self.assertEqual(m.get('objoff_30', 2), 64 if step in (9, 29) else 0)

    def test_other_zone_users_keep_generic_subtypes(self):
        for rom, symbols, baseline, old, _ in self.images.values():
            for zone in ('hill_top_zone', 'metropolis_zone', 'metropolis_zone_2', 'aquatic_ruin_zone'):
                for subtype in range(4):
                    for flip in (0, 1):
                        a = DoorMachine(rom, symbols, zone, subtype=subtype, flipped=flip)
                        b = DoorMachine(baseline, old, zone, subtype=subtype, flipped=flip)
                        self.assertEqual((a.get('subtype'), a.get('mapping_frame')), (subtype, subtype))
                        self.assertEqual(a.state(), b.state())
                        self.assertEqual(a.step(0x800, 0x400), b.step(0x800, 0x400))
                        self.assertEqual(a.state(), b.state())

    def test_tracked_and_proposed_files_have_no_door_payloads(self):
        # Include untracked proposed source files; generated/ignored files stay out.
        names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                                        cwd=ROOT).decode().split('\0')
        records = {data[i * 6:i * 6 + 6] for name, values in door_inputs().items()
                   for data in values for i in DOORS[name][0]}
        for name in filter(None, names):
            data = (ROOT / name).read_bytes()
            self.assertNotIn(Path(name).suffix.lower(), ('.bin', '.rom', '.wav', '.cue', '.iso', '.chd'))
            # .md is Markdown in maintained files; detect binary payload directly.
            compact = re.sub(rb'[^0-9a-f]', b'', data.lower())
            for record in records:
                self.assertNotIn(record, data, name)
                self.assertNotIn(record.hex().encode(), compact, name)
        self.assertEqual(len(records), 18)
        self.assertEqual(len(SPANS), 7)


if __name__ == '__main__':
    unittest.main(verbosity=2)
