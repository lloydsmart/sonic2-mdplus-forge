"""Public production commands and strict packaging guards; no game fixtures."""
from __future__ import annotations

import json
import tempfile
import unittest
import wave
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from tools.mdplus_builder import cli, package
from tools.mdplus_builder.common import DEFAULT_MANIFEST, ROM_PATH, BuildError


class PublicSelectionTests(unittest.TestCase):
    def test_all_uses_production_build_and_package(self):
        with ExitStack() as stack:
            calls = {name: stack.enter_context(patch.object(cli, name)) for name in (
                'bootstrap_modern', 'build_modern', 'build_stock_modern', 'prepare_audio', 'assemble',
            )}
            stack.enter_context(patch('builtins.print'))
            self.assertEqual(cli.main(['all', '--input-dir', 'inputs/audio']), 0)
            calls['bootstrap_modern'].assert_called_once_with(local_source=None)
            calls['build_modern'].assert_called_once_with()
            calls['build_stock_modern'].assert_not_called()
            calls['prepare_audio'].assert_called_once_with(DEFAULT_MANIFEST, Path('inputs/audio').resolve())
            calls['assemble'].assert_called_once_with(DEFAULT_MANIFEST)

    def test_rom_commands_and_custom_output_select_current_source(self):
        for command in ('build-rom', 'build-modern'):
            with (
                self.subTest(command=command), patch.object(cli, 'build_modern') as modern,
                patch.object(cli, '_print_json'),
            ):
                self.assertEqual(cli.main([command]), 0)
                self.assertEqual(modern.call_count, 1)
                self.assertEqual(modern.call_args.args or (ROM_PATH,), (ROM_PATH,))
        with patch.object(cli, 'build_modern') as build, patch.object(cli, '_print_json'):
            self.assertEqual(cli.main(['build-rom', '--output', 'build/custom.md']), 0)
            build.assert_called_once_with(Path('build/custom.md').resolve())

    def test_bootstrap_and_prepare_aliases_select_current_source(self):
        for command, function in (
            ('bootstrap', 'bootstrap_modern'), ('bootstrap-modern', 'bootstrap_modern'),
            ('prepare-source', 'prepare_modern'), ('prepare-modern', 'prepare_modern'),
        ):
            with self.subTest(command=command), patch.object(cli, function) as call, patch.object(cli, '_print_json'):
                self.assertEqual(cli.main([command]), 0)
                if command.startswith('bootstrap'):
                    call.assert_called_once_with(local_source=None)
                else:
                    call.assert_called_once_with()

    def test_removed_legacy_options_are_rejected(self):
        commands = [
            ['bootstrap'], ['prepare-source'], ['build-rom'], ['verify-rom', 'build/test.md'],
            ['package'], ['all', '--input-dir', 'inputs/audio'],
        ]
        retired_args = [args + ['--legacy'] for args in commands] + [
            ['bootstrap', '--skip-assembler-build'],
            ['prepare-source', '--source-dir', 'build/source'],
            ['build-rom', '--source-dir', 'build/source'],
        ]
        for args in retired_args:
            with self.subTest(args=args), patch('sys.stderr'), self.assertRaises(SystemExit) as exc:
                cli.main(args)
            self.assertEqual(exc.exception.code, 2)

    def test_verification_uses_production_identity(self):
        with patch.object(cli, 'verify_modern') as verify, patch.object(cli, '_print_json'):
            self.assertEqual(cli.main(['verify-rom', '--strict-regression', 'build/test.md']), 0)
            verify.assert_called_once_with(Path('build/test.md').resolve(), strict_regression=True)


class PackageSelectionTests(unittest.TestCase):
    def test_package_validates_production_rom_before_writing(self):
        for rom in (None, Path('build/custom.md')):
            with (
                self.subTest(rom=rom),
                patch.object(package, 'verify_modern', side_effect=BuildError('wrong ROM')) as verify,
                patch.object(package.shutil, 'copy2') as copy,
            ):
                with self.assertRaisesRegex(BuildError, 'wrong ROM'):
                    package.assemble(DEFAULT_MANIFEST, rom_path=rom)
                verify.assert_called_once_with(rom or ROM_PATH, strict_regression=True)
                copy.assert_not_called()

    def test_packaged_names_cue_audio_and_checksums_are_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / 'source.md'
            rom.write_bytes(b'synthetic ROM')
            audio = root / 'track03.wav'
            with wave.open(str(audio), 'wb') as wav:
                wav.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
                wav.writeframes(bytes(588 * 4 * 2))
            manifest = root / 'tracks.json'
            manifest.write_text(json.dumps({'schema': 1, 'rom_basename': 'Test MD+', 'tracks': [{
                'track': 3, 'enabled': True, 'source': 'input.wav', 'mode': 'loop',
                'loop_start_sector': 0, 'loop_end_sector': 2,
            }]}))
            with patch.object(package, 'DIST', root / 'dist'), patch.object(package, 'verify_modern') as verify:
                output = package.assemble(manifest, rom_path=rom, audio_dir=root)
            verify.assert_called_once_with(rom, strict_regression=True)
            self.assertEqual({p.name for p in output.iterdir()},
                             {'Test MD+.md', 'Test MD+.cue', 'track03.wav', 'SHA256SUMS.json'})
            self.assertEqual((output / 'Test MD+.md').read_bytes(), rom.read_bytes())
            self.assertEqual((output / 'track03.wav').read_bytes(), audio.read_bytes())
            self.assertEqual((output / 'Test MD+.cue').read_text(),
                             'FILE "track03.wav" WAVE\n  TRACK 03 AUDIO\n    INDEX 01 00:00:00\n    REM LOOP 0\n')
            hashes = json.loads((output / 'SHA256SUMS.json').read_text())
            self.assertEqual(hashes, {p.name: package.sha256(p) for p in output.iterdir()
                                      if p.name != 'SHA256SUMS.json'})
