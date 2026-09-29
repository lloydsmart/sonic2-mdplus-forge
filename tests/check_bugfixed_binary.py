"""Check both built flavours after make rom and make rom-bugfixed."""
from __future__ import annotations

import unittest
from dataclasses import replace
from unittest.mock import patch

from tools.mdplus_builder import modern, source
from tools.mdplus_builder.common import BuildError
from tools.mdplus_builder.variants import BuildVariant


class BugfixedBinaryTests(unittest.TestCase):
    def test_strict_identity_and_exact_byte_equality(self):
        production, bugfixed = BuildVariant
        expected = (2_097_152, 'BE41', '9eb40c0601a7c424a0d1ce168b5f40f2',
                    'bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44')
        for variant in BuildVariant:
            result = modern.verify_modern(variant.rom_path, strict_regression=True, variant=variant)
            self.assertEqual(tuple(result[k] for k in ('size', 'header_checksum', 'md5', 'sha256')), expected)
            modern.verify_modern_driver(variant.rom_path.read_bytes(), modern.assembled_modern_driver(
                variant.prepared_dir / 'forge-s2.p'))
        self.assertEqual(production.rom_path.read_bytes(), bugfixed.rom_path.read_bytes())
        self.assertFalse(production.rom_path.samefile(bugfixed.rom_path))
        self.assertTrue(modern.MODERN_ROM_PATH.samefile(production.rom_path))

    def test_bugfixed_profile_is_independent_and_enforced(self):
        production, bugfixed = BuildVariant
        original = modern.VERIFICATION_PROFILES[bugfixed]
        for field, value in (('size', 1), ('checksum', '0000'), ('md5', '0' * 32), ('sha256', '0' * 64)):
            with self.subTest(field=field), patch.dict(modern.VERIFICATION_PROFILES, {
                bugfixed: replace(original, **{field: value}),
            }):
                with self.assertRaises(BuildError):
                    modern.verify_modern(bugfixed.rom_path, strict_regression=True, variant=bugfixed)
                modern.verify_modern(production.rom_path, strict_regression=True, variant=production)

    def test_prepared_source_content_and_pin_are_equal(self):
        production, bugfixed = BuildVariant
        tracked = source._git_output(production.prepared_dir, 'ls-files', '-z').split('\0')
        names = {name for name in tracked if name} | {
            'hybrid_modern.asm', 'hybrid_modern_handoff.asm', 'hybrid_modern_z80.asm',
            'hybrid_modern_router.asm', 'modern_build.lua',
        }
        for variant in BuildVariant:
            self.assertEqual(source._git_output(variant.prepared_dir, 'rev-parse', 'HEAD'),
                             modern.AUDITED_MODERN_COMMIT)
            self.assertIn('fixBugs = 0', (variant.prepared_dir / 's2.asm').read_text())
        for name in sorted(names):
            with self.subTest(source=name):
                self.assertEqual((production.prepared_dir / name).read_bytes(),
                                 (bugfixed.prepared_dir / name).read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
