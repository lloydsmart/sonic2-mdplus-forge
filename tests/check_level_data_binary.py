"""Pinned semantic policy, full ROM diff accounting and complete symbol audit."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from door_data_evidence import DOORS, restore_v301
from level_data_evidence import (
    OBJECT_ORDER,
    PRE_LEVEL,
    TABLE_ORDER,
    audited_layouts,
    pre_level_symbols,
    restore_pre_level,
)
from unicorn import UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, Uc
from unicorn.m68k_const import UC_CPU_M68K_M68000, UC_M68K_REG_A0, UC_M68K_REG_A1, UC_M68K_REG_A7, UC_M68K_REG_SR

from tools.mdplus_builder import bugfixed, modern
from tools.mdplus_builder.common import BUILD, BuildError
from tools.mdplus_builder.level_data import LEVEL_POLICIES, parse_objects
from tools.mdplus_builder.source import _clone_at
from tools.mdplus_builder.variants import BuildVariant

SYMBOL_HASHES = {
    'stock': 'fa3e71943d4f3e2ed5ba99c31fa021f83e6f9356be100fa188a1b2135fcf9625',
    'mdplus': '8ec6707534a3f112a41e9df92d224f7f58b4eda01eb072616bc297549db6bf3b',
}


class LevelDataBinaryTests(unittest.TestCase):
    def test_compiled_conveyor_width_and_grounded_transport(self):
        rom = bugfixed.STOCK_BUGFIXED_ROM_PATH.read_bytes()
        symbols = modern.modern_symbols(bugfixed.STOCK_BUGFIXED_LISTING_PATH)
        for subtype, radius, height in ((0x90, 0, 0x70), (0x09, 0x90, 0x30)):
            cpu = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
            cpu.ctl_set_cpu_model(UC_CPU_M68K_M68000)
            cpu.mem_map(0, 0x200000)
            cpu.mem_write(0, rom)
            cpu.mem_map(0xFFFF0000, 0x10000)
            cpu.mem_map(0x300000, 0x1000)
            obj, player, stack = 0xFFFFD000, 0xFFFFD040, 0xFFFFEF00
            cpu.reg_write(UC_M68K_REG_SR, 0x2700)
            cpu.reg_write(UC_M68K_REG_A0, obj)
            cpu.reg_write(UC_M68K_REG_A7, stack)
            cpu.mem_write(obj + symbols['subtype'], bytes((subtype,)))
            cpu.emu_start(symbols['Obj72_Init'], symbols['Obj72_Main'], count=100)
            self.assertEqual(cpu.mem_read(obj + symbols['objoff_38'], 1)[0], radius)
            self.assertEqual(int.from_bytes(cpu.mem_read(obj + symbols['objoff_3C'], 2), 'big'), height)
            cpu.mem_write(obj + symbols['x_pos'], (0x800).to_bytes(2, 'big'))
            cpu.mem_write(obj + symbols['y_pos'], (0x400).to_bytes(2, 'big'))
            for airborne in (False, True):
                cpu.reg_write(UC_M68K_REG_A1, player)
                cpu.reg_write(UC_M68K_REG_A7, stack)
                cpu.mem_write(stack, (0x300000).to_bytes(4, 'big'))
                cpu.mem_write(player + symbols['x_pos'], (0x800).to_bytes(2, 'big'))
                cpu.mem_write(player + symbols['y_pos'], (0x3F0).to_bytes(2, 'big'))
                cpu.mem_write(player + symbols['status'], bytes((2 if airborne else 0,)))
                cpu.emu_start(symbols['Obj72_Action'], 0x300000, count=100)
                x = int.from_bytes(cpu.mem_read(player + symbols['x_pos'], 2), 'big')
                self.assertEqual(x, 0x800 + (2 if subtype == 9 and not airborne else 0))

    def test_pinned_policy_semantics_exclusions_and_atomic_failures(self):
        with tempfile.TemporaryDirectory(prefix='level-policy-', dir=BUILD) as directory:
            work = Path(directory) / 'source'
            _clone_at('', bugfixed.AUDITED_COMMIT, work, modern.SOURCE_MODERN_DIR)
            before = bugfixed.tracked_hashes(work)
            evidence = audited_layouts()
            originals = {f'level/objects/{name}.bin': b''.join(values[0])
                         for name, values in evidence.items()}
            # Wrong pristine, reference, expected semantic diff and target all reject
            # before any tracked write, including the earlier audio/game transforms.
            for name, policy in LEVEL_POLICIES.items():
                for field, value in (
                    ('pristine_sha256', '0' * 64), ('reference_sha256', '0' * 64),
                    ('reference_shapes', ()), ('selected_shapes', (('insert', 0, 0, 1),)),
                    ('target_sha256', '0' * 64),
                ):
                    with (patch.dict(LEVEL_POLICIES, {name: replace(policy, **{field: value})}),
                          self.subTest(name=name, field=field), self.assertRaises(BuildError)):
                        bugfixed.apply_policy(work)
                    self.assertEqual(bugfixed.tracked_hashes(work), before)
            bugfixed.apply_policy(work)
            after = bugfixed.tracked_hashes(work)
            self.assertEqual({n for n in before if before[n] != after[n]}, set(bugfixed.POLICY_HASHES))
            for name in before.keys() - bugfixed.POLICY_HASHES.keys():
                self.assertEqual(before[name], after[name], name)
            for layout, (retail, _, expected) in evidence.items():
                name = f'level/objects/{layout}.bin'
                target = b''.join(expected)
                self.assertEqual((work / name).read_bytes(), target)
                self.assertEqual(target, (BuildVariant.BUGFIXED.prepared_dir / name).read_bytes())
                self.assertEqual(b''.join(retail), (BuildVariant.PRODUCTION.prepared_dir / name).read_bytes())
            ehz = parse_objects((work / 'level/objects/EHZ_2.bin').read_bytes())
            for index in (29, 65, 144):
                self.assertEqual(ehz[index].raw, evidence['EHZ_2'][1][index])
            # Issue #111: every retail signpost/capsule remains, with no additions;
            # no internal $FFFF terminator, sorted X, no trailing out-of-order wall.
            retail = parse_objects(originals['level/objects/EHZ_2.bin'])
            self.assertEqual([e.raw for e in ehz if e.object_id in (0x0D, 0x3E)],
                             [e.raw for e in retail if e.object_id in (0x0D, 0x3E)])
            self.assertEqual([e.raw.hex() for e in ehz if e.x >= 0xFFFF], [])
            self.assertEqual(ehz[-1].raw, retail[-1].raw)
            self.assertEqual(ehz[-1].object_id, 0x3E)
            arz = parse_objects((work / 'level/objects/ARZ_2.bin').read_bytes())
            self.assertEqual(arz[119].raw, evidence['ARZ_2'][1][118])
            self.assertEqual(arz[119].object_id, 0x03)
            self.assertEqual(arz[33].raw, evidence['ARZ_2'][0][33])
            self.assertEqual(arz[33].object_id, 0x24)
            wfz = parse_objects((work / 'level/objects/WFZ_1.bin').read_bytes())
            self.assertEqual(wfz[127].raw, evidence['WFZ_1'][1][127])
            self.assertEqual(wfz[127].object_id, 0x72)

    def test_complete_binary_reconstruction_symbol_movements_and_accounting(self):
        report = {}
        for kind, path, listing in (
            ('stock', bugfixed.STOCK_BUGFIXED_ROM_PATH, bugfixed.STOCK_BUGFIXED_LISTING_PATH),
            ('mdplus', BuildVariant.BUGFIXED.rom_path, BuildVariant.BUGFIXED.prepared_dir / 's2.lst'),
        ):
            rom, symbols = restore_v301(path.read_bytes(), modern.modern_symbols(listing), listing, kind)
            baseline = restore_pre_level(rom, symbols, kind)
            old_symbols = pre_level_symbols(symbols)
            # Freeze ALL symbols, including sound/Z80/Forge/RAM and assembly values.
            self.assertEqual(hashlib.sha256(json.dumps(old_symbols, sort_keys=True).encode()).hexdigest(),
                             SYMBOL_HASHES[kind])
            movements = {n: {'before': old_symbols[n], 'after': v, 'delta': v - old_symbols[n]}
                         for n, v in symbols.items() if v != old_symbols[n]}
            self.assertEqual(len(movements), 25)  # 24 labels and paddingSoFar.
            # Validate all compiled files and all intervening boundary bytes.
            files = {}
            for index, (name, old_address) in enumerate(OBJECT_ORDER[:-1]):
                source_name = f'level/objects/{name}.bin'
                retail = (modern.SOURCE_MODERN_DIR / source_name).read_bytes()
                prepared = (BuildVariant.BUGFIXED.prepared_dir / source_name).read_bytes()
                if name in DOORS:
                    # This historical audit operates after reversing the door phase.
                    prepared = retail
                new_address = symbols['Objects_' + name]
                self.assertEqual(baseline[old_address:old_address + len(retail)], retail)
                self.assertEqual(rom[new_address:new_address + len(prepared)], prepared)
                next_name, next_old = OBJECT_ORDER[index + 1]
                self.assertEqual(baseline[old_address + len(retail):next_old],
                                 rom[new_address + len(prepared):symbols['Objects_' + next_name]])
                files[name] = {'before': old_address, 'after': new_address,
                               'before_bytes': len(retail), 'after_bytes': len(prepared)}
            self.assertEqual(rom[0xEC36A:0xEC382], baseline[0xEC352:0xEC36A])
            self.assertFalse(any(rom[0xEC382:0xED000]))
            self.assertFalse(any(baseline[0xEC36A:0xED000]))
            # Disjoint categories exhaust every difference, checked against full hashes.
            categories = {'checksum': (0x18E, 0x190), 'object_pointers': (0xE6E00, 0xE6E44),
                          'object_entries_boundaries_alignment': (0xE717A, 0xED000)}
            indexes = [i for i, (a, b) in enumerate(zip(baseline, rom, strict=True)) if a != b]
            counts = {n: sum(a <= i < b for i in indexes) for n, (a, b) in categories.items()}
            self.assertEqual(sum(counts.values()), len(indexes))
            self.assertEqual(len(indexes), 17041)
            self.assertEqual(len(TABLE_ORDER), 34)
            report[kind] = {'baseline_sha256': PRE_LEVEL[kind][1],
                            'candidate_sha256': hashlib.sha256(rom).hexdigest(),
                            'changed_bytes': len(indexes), 'categories': counts,
                            'symbol_movements': movements, 'files': files,
                            'alignment_before': 0xED000 - 0xEC36A,
                            'alignment_after': 0xED000 - 0xEC382,
                            'compression': 'Object entries are uncompressed BINCLUDE data'}
        (BUILD / 'level-data-diff.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
