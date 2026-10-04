"""Fast fail-closed policy tests; actual pinned inputs are checked by the binary suite."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.mdplus_builder import bugfixed, cli
from tools.mdplus_builder.common import BuildError


class CuratedPolicyTests(unittest.TestCase):
    def transform_fixture(self, filename, text):
        data = text.encode()
        with patch.dict(bugfixed.SOURCE_HASHES, {filename: hashlib.sha256(data).hexdigest()}):
            return bugfixed.transform_source(data, filename).decode()

    def main_fixture(self):
        return ('\nfixBugs = 0\n\nFixMusicAndSFXDataBugs = fixBugs\n' +
                '\n'.join(pattern * count for pattern, count in bugfixed.PAGE_FLIP_PATTERNS['s2.asm']) +
                bugfixed.MCZ_RIGHT_DRILL_OLD + bugfixed.ARZ_PILLAR_OLD + bugfixed.ARZ_OBJ82_OLD +
                "".join(old for old, _ in bugfixed.DOOR_PATTERNS))

    def test_rejects_wrong_source_hash_and_unknown_file(self):
        for name in (*bugfixed.SOURCE_HASHES, 'build.lua'):
            with self.subTest(name=name), self.assertRaisesRegex(BuildError, 'source hash changed'):
                bugfixed.transform_source(b'changed source', name)

    def test_exact_patterns_and_counts_are_enforced_even_after_hash_check(self):
        for pattern, _ in bugfixed.PAGE_FLIP_PATTERNS['s2.asm']:
            for text in (self.main_fixture().replace(pattern, '', 1), self.main_fixture() + pattern):
                with self.subTest(pattern=pattern), self.assertRaisesRegex(BuildError, 'source pattern'):
                    self.transform_fixture('s2.asm', text)
        for old in ('fixBugs = 0', 'FixMusicAndSFXDataBugs = fixBugs'):
            with self.assertRaisesRegex(BuildError, 'source pattern'):
                self.transform_fixture('s2.asm', self.main_fixture().replace(old, 'unexpected'))

    def test_flags_and_companion_negative_branches(self):
        result = self.transform_fixture('s2.asm', self.main_fixture())
        self.assertIn('\nfixBugs = 1\n', result)
        self.assertIn('\nForgeFix2PSpritePageFlip = 0 ', result)
        self.assertIn('\nFixMusicAndSFXDataBugs = 0\n', result)
        self.assertEqual(result.count('if ForgeFix2PSpritePageFlip'), 7)
        self.assertEqual(result.count('if ~~ForgeFix2PSpritePageFlip'), 2)
        self.assertEqual(result.count('if fixBugs'), 3)  # Three downstream corrections.
        self.assertNotIn('if ~~fixBugs', result)

    def test_ordinary_game_fixes_are_not_rewritten(self):
        ordinary = '\n    if fixBugs\nordinary correction\n    endif\n'
        result = self.transform_fixture('s2.asm', self.main_fixture() + ordinary)
        self.assertIn(ordinary, result)

    def test_mcz_right_drill_operand_is_corrected_exactly_once(self):
        source = self.main_fixture()
        result = self.transform_fixture('s2.asm', source)
        self.assertIn(bugfixed.MCZ_RIGHT_DRILL_FIXED, result)
        self.assertNotIn(bugfixed.MCZ_RIGHT_DRILL_OLD, result)
        self.assertEqual(len(bugfixed.MCZ_RIGHT_DRILL_OLD), len(bugfixed.MCZ_RIGHT_DRILL_FIXED))
        self.assertIn('addi_.w\t#1,sub2_x_pos(a0)', result)
        self.assertIn('subi_.w\t#2,sub2_x_pos(a0)', result)
        for wrong in (source.replace(bugfixed.MCZ_RIGHT_DRILL_OLD,
                                     bugfixed.MCZ_RIGHT_DRILL_FIXED),
                      source + bugfixed.MCZ_RIGHT_DRILL_OLD):
            with self.assertRaisesRegex(BuildError, 'source pattern'):
                self.transform_fixture('s2.asm', wrong)

    def test_arz_pillar_correction_requires_one_pristine_anchor(self):
        source = self.main_fixture()
        result = self.transform_fixture('s2.asm', source)
        self.assertIn(bugfixed.ARZ_PILLAR_FIXED, result)
        self.assertNotIn(bugfixed.ARZ_PILLAR_OLD, result)
        self.assertEqual(result.count('subq.w\t#8,d2'), 1)
        for wrong in (source.replace(bugfixed.ARZ_PILLAR_OLD, ''),
                      source + bugfixed.ARZ_PILLAR_OLD,
                      source.replace(bugfixed.ARZ_PILLAR_OLD, bugfixed.ARZ_PILLAR_FIXED)):
            with self.assertRaisesRegex(BuildError, 'source pattern'):
                self.transform_fixture('s2.asm', wrong)

    def test_door_overrides_require_each_exact_pristine_context(self):
        source = self.main_fixture()
        result = self.transform_fixture('s2.asm', source)
        for old, new in bugfixed.DOOR_PATTERNS:
            self.assertIn(new, result)
            self.assertNotIn(old, result)
            for wrong in (source.replace(old, ''), source + old,
                          source.replace(old, new), source.replace(old, old.replace('#3,', '#2,'))):
                with self.assertRaisesRegex(BuildError, 'source pattern'):
                    self.transform_fixture('s2.asm', wrong)
        self.assertNotIn('move.b\t#3,subtype(a0)', result)

    def test_driver_and_ram_exclusions(self):
        self.assertEqual(self.transform_fixture('s2.sounddriver.asm', '\nFixDriverBugs = fixBugs\n'),
                         '\nFixDriverBugs = 0\n')
        text = '\n'.join(p for p, _ in bugfixed.PAGE_FLIP_PATTERNS['s2.constants.asm'])
        result = self.transform_fixture('s2.constants.asm', text)
        self.assertEqual(result.count('if ForgeFix2PSpritePageFlip'), 2)
        self.assertNotIn('if fixBugs', result)
        for pattern, _ in bugfixed.PAGE_FLIP_PATTERNS['s2.constants.asm']:
            with self.assertRaisesRegex(BuildError, 'source pattern'):
                self.transform_fixture('s2.constants.asm', text.replace(pattern, '', 1))

    def test_selected_audio_contexts_fail_closed(self):
        for name, patterns in bugfixed.AUDIO_PATTERNS.items():
            source = ''.join(old for old, _ in patterns)
            self.assertEqual(self.transform_fixture(name, source), ''.join(new for _, new in patterns))
            for old, new in patterns:
                for wrong in (source.replace(old, '', 1), source + old,
                              source.replace(old, new, 1), source.replace(old, old + '; unexpected\n', 1)):
                    with self.subTest(name=name), self.assertRaisesRegex(BuildError, 'source hash changed'):
                        bugfixed.transform_source(wrong.encode(), name)
                for wrong in (source.replace(old, '', 1), source + old, source.replace(old, new, 1)):
                    with self.subTest(name=name), self.assertRaisesRegex(BuildError, 'source pattern'):
                        self.transform_fixture(name, wrong)

    def test_post_policy_hash_failure_precedes_all_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for name in bugfixed.SOURCE_HASHES:
                path = work / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'pristine')
            (work / 'build.lua').write_text('\nFixMusicAndSFXDataBugs = 0\n')
            hashes = {'build.lua': bugfixed.BUILD_LUA_SHA256}
            with (patch.object(bugfixed, '_git_output', side_effect=[bugfixed.AUDITED_COMMIT, '']),
                  patch.object(bugfixed, 'tracked_hashes', return_value=hashes),
                  patch.object(bugfixed, 'transform_source', return_value=b'wrong output'),
                  self.assertRaisesRegex(BuildError, 'post-policy hash changed')):
                bugfixed.apply_policy(work)
            for name in bugfixed.SOURCE_HASHES:
                self.assertEqual((work / name).read_bytes(), b'pristine')

    def test_obj82_requires_one_pristine_anchor_and_preserves_obj2b(self):
        source = self.main_fixture()
        result = self.transform_fixture('s2.asm', source)
        self.assertIn(bugfixed.ARZ_OBJ82_FIXED, result)
        self.assertNotIn(bugfixed.ARZ_OBJ82_OLD, result)
        self.assertEqual(result.count(bugfixed.ARZ_PILLAR_FIXED), 1)
        for wrong in (source.replace(bugfixed.ARZ_OBJ82_OLD, ''),
                      source + bugfixed.ARZ_OBJ82_OLD,
                      source.replace(bugfixed.ARZ_OBJ82_OLD, bugfixed.ARZ_OBJ82_FIXED),
                      source.replace('subq.w\t#2,d3', 'subq.w\t#3,d3')):
            with self.assertRaisesRegex(BuildError, 'source pattern'):
                self.transform_fixture('s2.asm', wrong)
            with self.assertRaisesRegex(BuildError, 'source hash changed'):
                bugfixed.transform_source(wrong.encode(), 's2.asm')

    def test_wrong_revision_and_dirty_clone_rejected_before_mutation(self):
        with patch.object(bugfixed, '_git_output', return_value='wrong'), self.assertRaisesRegex(
                BuildError, 'audited pinned commit'):
            bugfixed.apply_policy(Path('not-used'))
        with (patch.object(bugfixed, '_git_output', side_effect=[bugfixed.AUDITED_COMMIT, ' M s2.asm']),
              self.assertRaisesRegex(BuildError, 'pristine disposable')):
            bugfixed.apply_policy(Path('not-used'))

    def test_build_pin_is_independent_of_config(self):
        with (patch.object(bugfixed, 'require_program', return_value='lua'),
              patch.object(bugfixed, 'run'),
              patch.object(bugfixed, 'load_json', return_value={'source_modern': {'commit': 'wrong'}}),
              self.assertRaisesRegex(BuildError, 'audited pinned commit')):
            bugfixed.build_stock_bugfixed()

    def test_cli_is_separate_from_mdplus_variants(self):
        parsed = cli.parser().parse_args(['build-stock-bugfixed'])
        self.assertFalse(hasattr(parsed, 'variant'))
        with patch.object(cli, 'build_stock_bugfixed', return_value={}) as build:
            self.assertEqual(cli.main(['build-stock-bugfixed']), 0)
            build.assert_called_once_with()

    def test_verifier_rejects_missing_small_and_incorrect_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.md'
            with self.assertRaisesRegex(BuildError, 'Cannot read'):
                bugfixed.verify_stock_bugfixed(path)
            path.write_bytes(b'bad')
            with self.assertRaisesRegex(BuildError, 'too small'):
                bugfixed.verify_stock_bugfixed(path)
            path.write_bytes(bytes(0x200))
            with self.assertRaisesRegex(BuildError, 'audited curated target'):
                bugfixed.verify_stock_bugfixed(path)


if __name__ == '__main__':
    unittest.main()
