"""Independent post-v3.0.2 MTZ3 source, compiled semantics and inverse audit."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from check_door_data_binary import DoorMachine
from mtz3_data_evidence import COUNTS, INDICES, MOVED, RELEASED, mtz3_inputs, restore_v302
from unicorn import UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, Uc
from unicorn.m68k_const import (
    UC_CPU_M68K_M68000,
    UC_M68K_REG_A0,
    UC_M68K_REG_A1,
    UC_M68K_REG_A2,
    UC_M68K_REG_A7,
    UC_M68K_REG_PC,
    UC_M68K_REG_SR,
)

from tools.mdplus_builder import bugfixed, modern
from tools.mdplus_builder.common import BUILD, DEPENDENCIES, ROOT, SOURCE_MODERN_DIR, load_json
from tools.mdplus_builder.source import _clone_at, genesis_checksum
from tools.mdplus_builder.variants import BuildVariant


class MTZ3DataBinaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.images, cls.reports = {}, {}
        for kind, path, listing in (
            ('stock', bugfixed.STOCK_BUGFIXED_ROM_PATH, bugfixed.STOCK_BUGFIXED_LISTING_PATH),
            ('mdplus', BuildVariant.BUGFIXED.rom_path, BuildVariant.BUGFIXED.prepared_dir / 's2.lst'),
        ):
            rom, symbols = path.read_bytes(), modern.modern_symbols(listing)
            report = {}
            baseline, old = restore_v302(rom, symbols, kind, report)
            cls.images[kind] = rom, symbols, baseline, old
            cls.reports[kind] = report

    def test_pinned_reference_exact_deletions_and_all_survivors(self):
        self.assertEqual(load_json(DEPENDENCIES)['source_modern'], {
            'url': 'https://github.com/sonicretro/s2disasm.git',
            'commit': '380f37a731bfc720bb0371a35a593184a7ec5e43'})
        retail, fixed = mtz3_inputs()
        self.assertEqual(len(retail) // 6, 270)
        self.assertEqual(len(fixed) // 6, 265)
        for data, variant in ((retail, BuildVariant.PRODUCTION), (fixed, BuildVariant.BUGFIXED)):
            self.assertEqual((variant.prepared_dir / 'level/objects/MTZ_3.bin').read_bytes(), data)
        for rom, symbols, baseline, old in self.images.values():
            start = symbols['Objects_MTZ_3']
            self.assertEqual(rom[start:start + len(fixed)], fixed)
            self.assertEqual(baseline[old['Objects_MTZ_3']:old['Objects_MTZ_3'] + len(retail)], retail)
            for i in INDICES:
                self.assertNotIn(retail[i * 6:i * 6 + 6],
                                 tuple(rom[j:j + 6] for j in range(start, start + len(fixed), 6)))
            # Exact whole-file equality includes every nearby and surviving entry.
            self.assertEqual(rom[start + len(fixed):symbols['Objects_WFZ_1']],
                             baseline[start + len(retail):old['Objects_WFZ_1']])

    def test_no_unrelated_source_or_reference_file_changes(self):
        with tempfile.TemporaryDirectory(prefix='mtz3-policy-', dir=BUILD) as directory:
            work = Path(directory) / 'source'
            _clone_at('', bugfixed.AUDITED_COMMIT, work, SOURCE_MODERN_DIR)
            before = bugfixed.tracked_hashes(work)
            bugfixed.apply_policy(work)
            after = bugfixed.tracked_hashes(work)
            changed = {name for name in before if before[name] != after[name]}
            existing = {'EHZ_2', 'ARZ_2', 'WFZ_1', 'CPZ_1', 'CPZ_2', 'DEZ_1'}
            self.assertEqual({n for n in changed if n.startswith('level/')},
                             {f'level/objects/{n}.bin' for n in existing | {'MTZ_3'}})
            self.assertEqual(changed, set(bugfixed.POLICY_HASHES))
            for name in before:
                if name.startswith('Utility Project Files/Fixed Files/') or name not in changed:
                    self.assertEqual(before[name], after[name], name)
            for name in before:
                if name.startswith(('level/objects/', 'level/rings/')):
                    self.assertEqual((BuildVariant.PRODUCTION.prepared_dir / name).read_bytes(),
                                     (SOURCE_MODERN_DIR / name).read_bytes(), name)

    def test_complete_accounting_all_symbols_and_inverse(self):
        for kind, (rom, symbols, baseline, old) in self.images.items():
            self.assertEqual(self.reports[kind]['counts'], COUNTS)
            self.assertEqual(self.reports[kind]['changed_bytes'], 14889)
            self.assertEqual(len(self.reports[kind]['fixups']), 28)
            self.assertEqual(hashlib.sha256(baseline).hexdigest(), RELEASED[kind][2])
            movements = {n: v - old[n] for n, v in symbols.items() if v != old[n]}
            self.assertEqual(movements, {'Objects_' + n: -30 for n in MOVED} | {'paddingSoFar': 30})
            self.assertEqual(len(movements), 22)
            # Exact equal slices freeze every code/asset byte outside the deletion
            # and table/checksum sites, including ring data and the entire tail.
            for start, end in ((0, 0x18E), (0x190, 0xE6C00), (0xE6C44, 0xE7D00),
                               (0xEC182, 0x200000)):
                self.assertEqual(rom[start:end], baseline[start:end])
            self.assertEqual(rom[0xE8336:0xEC164], baseline[0xE8354:0xEC182])
            self.assertFalse(any(rom[0xEC164:0xED000]))
            for name in ('Off_Rings', 'Off_Objects', 'Objects_MTZ_3', 'SoundDriverLoad',
                         'Snd_Driver', 'Snd_Driver_End', 'MusicPoint1', 'MusicPoint2',
                         'SoundIndex', 'SndDAC_Start', 'RAM_Start', 'Game_Mode', 'CrossResetRAM'):
                self.assertEqual(symbols[name], old[name], name)
            if kind == 'mdplus':
                for name in symbols:
                    if name.startswith('Forge'):
                        self.assertEqual(symbols[name], old[name], name)
        (BUILD / 'mtz3-data-diff.json').write_text(json.dumps(self.reports, indent=2) + '\n')

    def test_mutations_deleted_regions_movement_alignment_checksum_and_symbols(self):
        for kind, (rom, symbols, _, _) in self.images.items():
            offsets = [0x18E, 0xE6C00, 0xE6C18, 0xE8336, 0xE9000, 0xEC163,
                       0xEC164, 0xEC181, 0xED000, 0xED0E8, 0x108300, 0x1FFFFF]
            for removed, index in enumerate(INDICES):
                site = symbols['Objects_MTZ_3'] + (index - removed) * 6
                offsets.extend((site - 1, site, site + 5))
            for offset in offsets:
                damaged = bytearray(rom)
                damaged[offset] ^= 1
                if offset != 0x18E:
                    damaged[0x18E:0x190] = genesis_checksum(damaged)[1].to_bytes(2, 'big')
                with self.subTest(kind=kind, offset=hex(offset)), self.assertRaises(AssertionError):
                    restore_v302(damaged, symbols, kind)
            for name in ('Objects_MTZ_3', 'Objects_WFZ_1', 'Objects_ARZ_2', 'Off_Objects',
                         'SoundDriverLoad', 'RAM_Start', 'paddingSoFar'):
                with self.subTest(symbol=name), self.assertRaises(AssertionError):
                    restore_v302(rom, symbols | {name: symbols[name] + 2}, kind)
            with self.assertRaises(AssertionError):
                restore_v302(rom, modern.modern_symbols(BuildVariant.PRODUCTION.prepared_dir / 's2.lst'), kind)

    def cpu(self, rom, symbols, index=None):
        c = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        c.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        c.mem_map(0, 0x200000)
        c.mem_write(0, rom)
        c.mem_map(0xFFFF0000, 0x10000)
        c.mem_map(0x300000, 0x300000)
        c.reg_write(UC_M68K_REG_SR, 0x2700)
        c.reg_write(UC_M68K_REG_A7, 0xFFFFEF00)
        c.mem_write(0xFFFFEF00, (0x500000).to_bytes(4, 'big'))
        if index is not None:
            data = mtz3_inputs()[0][index * 6:index * 6 + 6]
            obj = 0xFFFFD800
            c.reg_write(UC_M68K_REG_A0, obj)
            for name, value in (('x_pos', data[:2]), ('y_pos', data[2:4]), ('subtype', data[5:6])):
                c.mem_write(obj + symbols[name], value)
            c.mem_write(symbols['Current_Zone'] | 0xFF000000, bytes((symbols['metropolis_zone_2'],)))
        return c

    @staticmethod
    def field(cpu, symbols, name, size=1):
        return int.from_bytes(cpu.mem_read(0xFFFFD800 + symbols[name], size), 'big')

    def test_compiled_object_types_art_and_collision(self):
        source = (SOURCE_MODERN_DIR / 's2.asm').read_text()
        plcs = source[source.index('PlrList_Mtz1:'):source.index('PlrList_Mtz2_End')]
        self.assertIn('ArtNem_Spikes', plcs)  # Upright art IS loaded; qualify upstream's note.
        self.assertNotIn('ArtNem_HorizSpike', plcs)
        retail = mtz3_inputs()[0]
        for rom, s, baseline, old in self.images.values():
            for index in INDICES:
                c = self.cpu(baseline, old)
                c.reg_write(UC_M68K_REG_A0, old['Objects_MTZ_3'] + index * 6)
                c.reg_write(UC_M68K_REG_A2, 0xFFFFFC00)
                # Camera/player Y remains zero, far from these placements;
                # the real normal loader nevertheless allocates each record.
                c.emu_start(old['ChkLoadObj'], 0x500000, count=500)
                self.assertEqual(c.reg_read(UC_M68K_REG_PC), 0x500000)
                obj = c.reg_read(UC_M68K_REG_A1)
                record = retail[index * 6:index * 6 + 6]
                self.assertEqual(bytes(c.mem_read(obj + old['x_pos'], 2)), record[:2])
                self.assertEqual(bytes(c.mem_read(obj + old['y_pos'], 2)), record[2:4])
                self.assertEqual(c.mem_read(obj + old['id'], 1)[0], record[4])
                self.assertEqual(c.mem_read(obj + old['subtype'], 1)[0], record[5])
                self.assertEqual(c.mem_read(obj + old['respawn_index'], 1)[0], 0)
            for image, syms in ((rom, s), (baseline, old)):
                c = self.cpu(image, syms, 53)
                c.emu_start(syms['Obj36_Init'], 0x500000, count=500)
                self.assertEqual(c.reg_read(UC_M68K_REG_PC), 0x500000)
                self.assertEqual((self.field(c, syms, 'routine'), self.field(c, syms, 'mapping_frame'), self.field(c, syms, 'subtype')), (4, 4, 0))
                self.assertEqual(self.field(c, syms, 'art_tile', 2), 0x242C)
                self.assertEqual((self.field(c, syms, 'width_pixels'), self.field(c, syms, 'y_radius')), (16, 16))
                c.emu_start(syms['Obj36_Sideways'], syms['SolidObject'], count=500)
                self.assertEqual(c.reg_read(UC_M68K_REG_PC), syms['SolidObject'])
                door = DoorMachine(image, syms, 'metropolis_zone_2', retail[100 * 6:101 * 6])
                self.assertEqual(door.get('mapping_frame'), 1)
                self.assertEqual(door.get('art_tile', 2), 0x6000)
                self.assertEqual(door.get('width_pixels'), 12)
                self.assertEqual(door.step(0x1170, 0x5E0), (23, 32, 33, 0x1174))
                c = self.cpu(image, syms, 217)
                c.emu_start(syms['Obj65_Init'], syms['SolidObject'], count=1000)
                self.assertEqual(c.reg_read(UC_M68K_REG_PC), syms['SolidObject'])
                self.assertEqual((self.field(c, syms, 'mapping_frame'), self.field(c, syms, 'subtype'), self.field(c, syms, 'width_pixels'),
                                  self.field(c, syms, 'y_radius'), self.field(c, syms, 'objoff_3C', 2)), (1, 3, 32, 12, 64))
                for index in (230, 233):
                    c = self.cpu(image, syms, index)
                    # Keep Obj31 in its horizontal lifetime window.
                    x = int.from_bytes(retail[index * 6:index * 6 + 2], 'big') & 0xFF80
                    c.mem_write(syms['Camera_X_pos_coarse'] | 0xFF000000, x.to_bytes(2, 'big'))
                    c.emu_start(syms['Obj31_Init'], 0x500000, count=500)
                    self.assertEqual(c.reg_read(UC_M68K_REG_PC), 0x500000)
                    self.assertEqual((self.field(c, syms, 'collision_flags'), self.field(c, syms, 'render_flags')), (0x95, 4))
                    self.assertEqual(image[syms['Touch_Sizes'] + 0x15 * 2:syms['Touch_Sizes'] + 0x15 * 2 + 2],
                                     bytes((128, 32)))
                    c.mem_write(syms['Debug_placement_mode'] | 0xFF000000, b'\x00\x01')
                    c.emu_start(syms['Obj31_Main'], syms['DisplaySprite'], count=500)
                    self.assertEqual(c.reg_read(UC_M68K_REG_PC), syms['DisplaySprite'])

    def test_compiled_kosinski_terrain_context(self):
        rom, symbols, _, _ = self.images['stock']
        def decode(name):
            c = self.cpu(rom, symbols)
            c.mem_write(0x300000, (SOURCE_MODERN_DIR / name).read_bytes())
            c.reg_write(UC_M68K_REG_A0, 0x300000)
            c.reg_write(UC_M68K_REG_A1, 0x400000)
            c.emu_start(symbols['KosDec'], 0x500000, count=2_000_000)
            self.assertEqual(c.reg_read(UC_M68K_REG_PC), 0x500000)
            return bytes(c.mem_read(0x400000, c.reg_read(UC_M68K_REG_A1) - 0x400000))
        layout = decode('level/layout/MTZ_3.kos')
        chunks = decode('mappings/128x128/MTZ.kos')
        collision = decode('collision/MTZ primary 16x16 collision index.kos')
        heights = (SOURCE_MODERN_DIR / 'collision/Collision array - Vertical.bin').read_bytes()
        self.assertEqual((len(layout), len(chunks), len(collision)), (4096, 32768, 768))
        def solid(x, y):
            chunk = layout[y // 128 * 256 + x // 128]
            offset = chunk * 128 + ((y % 128) // 16 * 8 + (x % 128) // 16) * 2
            word = int.from_bytes(chunks[offset:offset + 2], 'big')
            shape = collision[word & 1023]
            return bool(word >> 12 & 2) and heights[shape * 16:shape * 16 + 16] == bytes((16,)) * 16
        # Centers are embedded; do not infer that their collision overhang is
        # unreachable merely from this. Door/spike collision can protrude.
        for x, y in ((0xA98, 0x258), (0x1174, 0x5E0), (0x1D20, 0x56D),
                     (0x1F80, 0x5FC), (0x2080, 0x5FC)):
            self.assertTrue(solid(x, y))
        # The retracting platform's complete 64-pixel travel stays embedded.
        self.assertTrue(all(solid(x, y) for x in range(0x1CC0, 0x1D40, 16)
                            for y in (0x561, 0x56D, 0x578)))
        # Marker 230 overlaps a cavity enclosed by full solid bands/walls.
        self.assertTrue(all(solid(x, y) for x in range(0x1F00, 0x1F80, 16)
                            for y in (0x580, 0x590, 0x600, 0x610)))
        self.assertTrue(all(solid(x, y) for x in (0x1EF0, 0x1F80)
                            for y in range(0x5A0, 0x600, 16)))

    def test_asset_boundary_all_mtz3_input_records(self):
        names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                                        cwd=ROOT).decode().split('\0')
        records = {data[i:i + 6] for data in mtz3_inputs() for i in range(0, len(data), 6)}
        for name in filter(None, names):
            data = (ROOT / name).read_bytes()
            self.assertNotIn(Path(name).suffix.lower(), ('.bin', '.rom', '.wav', '.cue', '.iso', '.chd'))
            compact = re.sub(rb'[^0-9a-f]', b'', data.lower())
            for record in records:
                self.assertNotIn(record, data, name)
                self.assertNotIn(record.hex().encode(), compact, name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
