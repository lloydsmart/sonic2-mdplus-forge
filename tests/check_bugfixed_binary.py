"""Independent curated + Forge audit. Run after both stock and both MD+ builds."""
from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from check_stock_bugfixed_binary import LAYOUT, PAGE_SYMBOLS, snapshot

from tools.mdplus_builder import bugfixed, modern, source
from tools.mdplus_builder.common import BUILD, BuildError
from tools.mdplus_builder.variants import BuildVariant

PRODUCTION, BUGFIXED = BuildVariant
# Observed from the controlled first build; independently reproduced from pristine inputs.
IDENTITY = (2_097_152, '0951', '5d3e5979d3f110d2761da3166b14b7cf',
            'e9f56f0efd72844918918f2efdecf6183f5bdabb47f235b61cc511a16942d3b5')
# Complete 15-byte expansions, in source order; all eight source operands audited.
BANK_SWITCHES = {0x9C: 'SoundIndex', 0xD4: 'SndDAC_Start', 0x62E: 'SoundIndex',
                 0x701: 'Snd_Sega', 0x982: 'SoundIndex', 0xC76: 'MusicPoint1',
                 0xC86: 'MusicPoint2', 0xF48: 'SoundIndex'}
HOOKS = {
    0x382: '61000dd461000f82', 0x45E: '52b8fe0c4cdf7fff4e73',
    0x135E: '4a38ffe0660611c0ffe04e7511c0ffe44e75',
    0x1370: '11c0ffe14e75', 0x1376: '11c0ffe24e75',
    0x13C4: '11fc00feffe0', 0x140A: '11fc00ffffe0',
    0x141E: '11fc00ffffe0', 0x547A: '11fc00ffffe0',
    0xED0DE: '101e53476602584f4e75',
}
# Each region is separately checked by exact instruction bytes / loaded and
# packed driver hashes. In the baseline comparison, restore its actual stock bytes.
FORGE_REGIONS = ((0x1084, 0x10E0), (0xED050, 0xED052), (0xED0DE, 0xF5100),
                 (0x108000, 0x1086C0))


class BugfixedBinaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixed = BUGFIXED.rom_path.read_bytes()
        cls.stock = bugfixed.STOCK_BUGFIXED_ROM_PATH.read_bytes()
        cls.prod = PRODUCTION.rom_path.read_bytes()
        cls.layout = modern.LAYOUT_PROFILES[BUGFIXED]
        cls.symbols = modern.modern_symbols(BUGFIXED.prepared_dir / 's2.lst')
        cls.stock_symbols = modern.modern_symbols(bugfixed.STOCK_BUGFIXED_LISTING_PATH)

    def test_strict_identity_and_divergence(self):
        result = modern.verify_modern(BUGFIXED.rom_path, strict_regression=True, variant=BUGFIXED)
        self.assertEqual(tuple(result[k] for k in ('size', 'header_checksum', 'md5', 'sha256')), IDENTITY)
        self.assertEqual(result['command_transactions'], 21)
        self.assertEqual([result[k] for k in ('overlay_address_signatures', 'command_address_signatures',
                                            'command_write_signatures', 'overlay_open_signatures',
                                            'overlay_close_signatures')], [42, 21, 21, 21, 21])
        for variant in BuildVariant:
            modern.verify_modern(variant.rom_path, strict_regression=True, variant=variant)
            modern.verify_modern_driver(variant.rom_path.read_bytes(), modern.assembled_modern_driver(
                variant.prepared_dir / 'forge-s2.p'), variant=variant)
        self.assertNotEqual(self.prod, self.fixed)
        self.assertFalse(PRODUCTION.rom_path.samefile(BUGFIXED.rom_path))
        self.assertTrue(modern.MODERN_ROM_PATH.samefile(PRODUCTION.rom_path))
        with self.assertRaises(BuildError):
            modern.verify_modern(BUGFIXED.rom_path, variant=PRODUCTION)
        with self.assertRaises(BuildError):
            modern.verify_modern(PRODUCTION.rom_path, variant=BUGFIXED)

    def test_layout_hooks_padding_and_curated_baseline(self):
        bugfixed.verify_stock_bugfixed(bugfixed.STOCK_BUGFIXED_ROM_PATH)
        for name, (_, expected) in LAYOUT.items():
            self.assertEqual(self.stock_symbols[name], expected, name)
            self.assertEqual(self.symbols[name], expected, name)
        self.assertEqual(self.layout.changed_regions, FORGE_REGIONS)
        for name, address in self.layout.handoff.items() | self.layout.router.items():
            self.assertEqual(self.symbols[name], address, name)
        for name, (address, _) in modern.RAM_STATE.items():
            self.assertEqual(self.symbols[name], address, name)
        for name in PAGE_SYMBOLS:
            self.assertNotIn(name, self.symbols)
        self.assertEqual(self.layout.implementation, 0x108000)
        self.assertEqual(self.layout.sound_end, 0x107FEC)
        self.assertFalse(any(self.stock[0x107FEC:]))
        self.assertFalse(any(self.fixed[0x107FEC:0x108000]))
        self.assertFalse(any(self.fixed[0x1086C0:]))
        # Actual last generated object and finishBank location, before only cnop/DC.B padding.
        listing = bugfixed.STOCK_BUGFIXED_LISTING_PATH.read_text()
        self.assertRegex(listing, r'107FEB : F2\s+dc.b\s+\$F2')
        self.assertRegex(listing, r'107FEC : \(MACRO\)\s+finishBank')
        self.assertIn("; end of 'ROM'", listing)
        restored = bytearray(self.fixed)
        restored[0x18E:0x190] = self.stock[0x18E:0x190]
        for address, original in HOOKS.items():
            expected = bytes.fromhex(original)
            self.assertEqual(self.stock[address:address + len(expected)], expected)
            restored[address:address + len(expected)] = expected
        for start, end in FORGE_REGIONS:
            restored[start:end] = self.stock[start:end]
        self.assertEqual(restored, self.stock)
        self.assertEqual(hashlib.sha256(restored).hexdigest(), bugfixed.STOCK_BUGFIXED_SHA256)
        masked = bytearray(self.stock)
        for start, end in FORGE_REGIONS:
            masked[start:end] = bytes(end - start)
        self.assertEqual(hashlib.sha256(masked).hexdigest(), self.layout.stock_masked_sha256)
        # No arbitrary bytes in the curated gameplay or trailing bank space can be ignored.
        offsets = [0x2000, 0x25E5C, 0x2A701, 0x317E6, 0x3F7FA, 0xF5100, 0x107FEB, 0x107FEC, 0x1086C0, 0x1FFFFF]
        offsets += list(HOOKS) + [0x1084, 0xED050, 0xED0E8, 0xEE093, 0xF50FF,
                                  0x108000, 0x1082B6, 0x108300, 0x1083A8]
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            path = Path(directory) / 'mutation.md'
            for offset in offsets:
                damaged = bytearray(self.fixed)
                damaged[offset] ^= 1
                damaged[0x18E:0x190] = source.genesis_checksum(damaged)[1].to_bytes(2, 'big')
                path.write_bytes(damaged)
                with self.subTest(offset=hex(offset)), self.assertRaises(BuildError):
                    # Non-strict verification must also reject every unexplained mutation.
                    modern.verify_modern(path, variant=BUGFIXED)

    def test_profiles_are_independent_and_enforced(self):
        original = modern.VERIFICATION_PROFILES[BUGFIXED]
        for field, value in (('size', 1), ('checksum', '0000'), ('md5', '0' * 32), ('sha256', '0' * 64)):
            with self.subTest(field=field), patch.dict(modern.VERIFICATION_PROFILES, {
                BUGFIXED: replace(original, **{field: value}),
            }):
                with self.assertRaises(BuildError):
                    modern.verify_modern(BUGFIXED.rom_path, strict_regression=True, variant=BUGFIXED)
                modern.verify_modern(PRODUCTION.rom_path, strict_regression=True)
        fields = ('sound_end', 'implementation', 'sax_helper', 'driver_length', 'driver_start', 'driver_limit',
                  'compressed_size', 'loaded_size', 'stock_size', 'loaded_sha256', 'driver_sha256',
                  'handoff_sha256', 'router_sha256', 'stock_checksum', 'stock_masked_sha256')
        for field in fields:
            value = getattr(self.layout, field)
            bad = value + 2 if isinstance(value, int) else '0' * len(value)
            with self.subTest(field=field), patch.dict(modern.LAYOUT_PROFILES, {
                BUGFIXED: replace(self.layout, **{field: bad}),
            }), self.assertRaises(BuildError):
                modern.verify_modern(BUGFIXED.rom_path, variant=BUGFIXED)
        for field, bad in (('curated', False), ('live_hooks', {**self.layout.live_hooks, 0x5478: self.layout.live_hooks[0x547A]}),
                           ('routine_sha256', dict.fromkeys(self.layout.routine_sha256, '0' * 64))):
            with patch.dict(modern.LAYOUT_PROFILES, {BUGFIXED: replace(self.layout, **{field: bad})}), self.assertRaises(BuildError):
                modern.verify_modern(BUGFIXED.rom_path, variant=BUGFIXED)

    def test_exact_policy_then_adapter_and_three_slot_semantics(self):
        with tempfile.TemporaryDirectory(prefix='audit-forge-policy-', dir=BUILD) as directory:
            work = Path(directory) / 'source'
            source._clone_at('', bugfixed.AUDITED_COMMIT, work, modern.SOURCE_MODERN_DIR)
            bugfixed.apply_policy(work)
            for name in self.layout.source_hashes:
                curated = (work / name).read_bytes()
                self.assertEqual(hashlib.sha256(curated).hexdigest(), self.layout.source_hashes[name])
                with patch.dict(modern.LAYOUT_PROFILES, {BUGFIXED: replace(
                    self.layout, source_hashes={**self.layout.source_hashes, name: '0' * 64},
                )}), self.assertRaises(BuildError):
                    modern._prepare_modern_source(curated, name, variant=BUGFIXED)
                self.assertEqual(modern._prepare_modern_source(curated, name, variant=BUGFIXED),
                                 (BUGFIXED.prepared_dir / name).read_bytes())
                pristine = (modern.SOURCE_MODERN_DIR / name).read_bytes()
                self.assertEqual(modern._prepare_modern_source(pristine, name),
                                 (PRODUCTION.prepared_dir / name).read_bytes())
                for data, variant in ((curated, PRODUCTION), (pristine, BUGFIXED), (curated + b'\n', BUGFIXED)):
                    with self.assertRaises(BuildError):
                        modern._prepare_modern_source(data, name, variant=variant)
            for name in bugfixed.AUDIO_PATTERNS:
                self.assertEqual((work / name).read_bytes(), (BUGFIXED.prepared_dir / name).read_bytes())
                self.assertEqual((modern.SOURCE_MODERN_DIR / name).read_bytes(),
                                 (PRODUCTION.prepared_dir / name).read_bytes())
            main = (BUGFIXED.prepared_dir / 's2.asm').read_text()
            self.assertIn(bugfixed.MCZ_RIGHT_DRILL_FIXED, main)
            for name, value in (('fixBugs', 1), ('ForgeFix2PSpritePageFlip', 0),
                                ('FixDriverBugs', 0), ('FixMusicAndSFXDataBugs', 0)):
                self.assertEqual(self.symbols[name], value)
            self.assertIn('moveq\t#3-1,d1', (work / 's2.asm').read_text())
        # MOVEQ #2,D1 through RTS is identical to the complete curated SFX loop.
        stock_start = self.stock_symbols['sndDriverInput.doSFX']
        forge_start = self.symbols['ForgeModernInput.sfx']
        loop = self.stock[stock_start:0x10E0]
        self.assertEqual(loop[:2], bytes.fromhex('7202'))
        self.assertEqual(self.fixed[forge_start:forge_start + len(loop)], loop)
        self.assertEqual(self.fixed[0x1084:0x108A], bytes.fromhex('4ef90010832a'))

    def test_complete_z80_bank_relocations_and_payload_bounds(self):
        prod = modern.assembled_modern_driver(PRODUCTION.prepared_dir / 'forge-s2.p')
        fixed = modern.assembled_modern_driver(BUGFIXED.prepared_dir / 'forge-s2.p')
        ps = modern.modern_symbols(PRODUCTION.prepared_dir / 's2.lst')
        normalized = bytearray(fixed)
        prefix = bytes.fromhex('af1e01210060')
        self.assertEqual([m.start() for m in re.finditer(re.escape(prefix), prod)], list(BANK_SWITCHES))
        self.assertEqual([m.start() for m in re.finditer(re.escape(prefix), fixed)], list(BANK_SWITCHES))
        for start, target in BANK_SWITCHES.items():
            for data, symbols in ((prod, ps), (fixed, self.symbols)):
                expected = prefix + bytes(0x73 if symbols[target] & (1 << bit) else 0x77 for bit in range(15, 24))
                self.assertEqual(data[start:start + 15], expected, (start, target))
            normalized[start:start + 15] = prod[start:start + 15]
        self.assertEqual(normalized, prod)
        self.assertEqual(sum(a != b for a, b in zip(prod, fixed, strict=True)), 34)
        for name in ('zHybridStopMusic', 'zHybridCodeEnd', 'zHybridAck', 'zMusicData', 'zPlaySoundByIndex'):
            self.assertEqual(ps[name], self.symbols[name])
        self.assertEqual((len(fixed), self.layout.compressed_size), (0x137A, 4011))
        self.assertEqual(hashlib.sha256(fixed).hexdigest(), 'f2883990453ba7deedc682b3970be0d2c73fea99a566a30d43362c2769ac7041')
        self.assertEqual(self.layout.driver_start + self.layout.compressed_size, 0xEE093)
        self.assertEqual(self.symbols['Snd_Driver_End'], 0xEE04C)  # nominal reservation, not payload EOF
        self.assertFalse(any(self.fixed[0xEE093:0xF5100]))
        self.assertEqual(self.fixed[0xF5100:0x107FEC], self.stock[0xF5100:0x107FEC])

    def test_clean_rebuild_and_both_order_isolation(self):
        protected = [modern.SOURCE_MODERN_DIR, PRODUCTION.prepared_dir, PRODUCTION.rom_path,
                     modern.MODERN_ROM_PATH, bugfixed.STOCK_BUGFIXED_ROM_PATH,
                     bugfixed.STOCK_BUGFIXED_LISTING_PATH]
        before = snapshot(protected)
        shutil.rmtree(BUGFIXED.prepared_dir)
        BUGFIXED.rom_path.unlink()
        modern.build_modern(variant=BUGFIXED)
        self.assertEqual(BUGFIXED.rom_path.read_bytes(), self.fixed)
        self.assertEqual(snapshot(protected), before)
        before = snapshot([BUGFIXED.prepared_dir, BUGFIXED.rom_path])
        modern.build_modern()
        self.assertEqual(PRODUCTION.rom_path.read_bytes(), self.prod)
        self.assertEqual(snapshot([BUGFIXED.prepared_dir, BUGFIXED.rom_path]), before)
        self.assertTrue(modern.MODERN_ROM_PATH.samefile(PRODUCTION.rom_path))


if __name__ == '__main__':
    unittest.main(verbosity=2)
