"""Variant selection and output isolation using synthetic inputs only."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import wave
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from tools.mdplus_builder import cli, modern, package, variants
from tools.mdplus_builder.common import DEFAULT_MANIFEST, BuildError
from tools.mdplus_builder.variants import BuildVariant


class VariantSelectionTests(unittest.TestCase):
    def test_defaults_and_bugfixed_selection(self):
        commands = [
            ['prepare-source'], ['build-rom'], ['verify-rom', 'build/test.md'],
            ['package'], ['all', '--input-dir', 'inputs/audio'],
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIs(cli.parser().parse_args(command).variant, BuildVariant.PRODUCTION)
                self.assertIs(cli.parser().parse_args(command + ['--bugfixed']).variant, BuildVariant.BUGFIXED)

    def test_compatibility_commands_do_not_accept_variant_selection(self):
        for command in ('bootstrap', 'bootstrap-modern', 'prepare-modern', 'build-modern', 'build-stock-modern'):
            with self.subTest(command=command), patch('sys.stderr'), self.assertRaises(SystemExit) as exc:
                cli.parser().parse_args([command, '--bugfixed'])
            self.assertEqual(exc.exception.code, 2)

    def test_bugfixed_dispatch(self):
        cases = [
            (['prepare-source'], 'prepare_modern', (), {}),
            (['build-rom'], 'build_modern', (None,), {}),
            (['build-rom', '--output', 'build/custom.md'], 'build_modern',
             (Path('build/custom.md').resolve(),), {}),
            (['verify-rom', '--strict-regression', 'build/test.md'], 'verify_modern',
             (Path('build/test.md').resolve(),), {'strict_regression': True}),
            (['package'], 'assemble', (DEFAULT_MANIFEST,),
             {'rom_path': None, 'audio_dir': variants.BUILD / 'audio'}),
        ]
        for command, function, args, kwargs in cases:
            with self.subTest(command=command), patch.object(cli, function) as call, patch.object(cli, '_print_json'), patch('builtins.print'):
                self.assertEqual(cli.main(command + ['--bugfixed']), 0)
                call.assert_called_once_with(*args, **kwargs, variant=BuildVariant.BUGFIXED)

    def test_all_bugfixed_shares_bootstrap_and_audio(self):
        with ExitStack() as stack:
            calls = {name: stack.enter_context(patch.object(cli, name)) for name in (
                'bootstrap_modern', 'build_modern', 'prepare_audio', 'assemble',
            )}
            stack.enter_context(patch('builtins.print'))
            self.assertEqual(cli.main(['all', '--bugfixed', '--input-dir', 'inputs/audio']), 0)
            calls['bootstrap_modern'].assert_called_once_with(local_source=None)
            calls['build_modern'].assert_called_once_with(variant=BuildVariant.BUGFIXED)
            calls['prepare_audio'].assert_called_once_with(DEFAULT_MANIFEST, Path('inputs/audio').resolve())
            calls['assemble'].assert_called_once_with(DEFAULT_MANIFEST, variant=BuildVariant.BUGFIXED)

    def test_verification_failure_names_selected_variant_path_and_cause(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.md'
            path.write_bytes(b'x')
            for variant in BuildVariant:
                with self.subTest(variant=variant), self.assertRaises(BuildError) as failure:
                    modern.verify_modern(path, variant=variant)
                self.assertIn(f'{variant.value.capitalize()} verification failed for {path}:',
                              str(failure.exception))
                self.assertIn('Modern MD+ ROM size is 1, expected 2097152', str(failure.exception))
            with patch.dict(modern.VERIFICATION_PROFILES, {
                BuildVariant.BUGFIXED: replace(modern.VERIFICATION_PROFILES[BuildVariant.BUGFIXED], size=1),
            }):
                with self.assertRaisesRegex(BuildError, 'Production verification failed.*ROM size'):
                    modern.verify_modern(path, variant=BuildVariant.PRODUCTION)
                with self.assertRaisesRegex(BuildError, 'Bugfixed verification failed.*File is too small'):
                    modern.verify_modern(path, variant=BuildVariant.BUGFIXED)

    def test_paths_and_independent_strict_profiles(self):
        production, bugfixed = BuildVariant
        self.assertEqual(production.prepared_dir, variants.BUILD / 'prepared-modern')
        self.assertEqual(bugfixed.prepared_dir, variants.BUILD / 'prepared-bugfixed')
        self.assertEqual(production.rom_path, variants.BUILD / 'sonic2-mdplus.md')
        self.assertEqual(bugfixed.rom_path, variants.BUILD / 'sonic2-mdplus-bugfixed.md')
        expected = modern.VerificationProfile(
            2_097_152, 'BE41', '9eb40c0601a7c424a0d1ce168b5f40f2',
            'bd12138cd478596e4d294a06f573a98a6d37747dfe58d726ca62cf50dc3a8c44',
        )
        self.assertEqual(modern.VERIFICATION_PROFILES[production], expected)
        self.assertNotEqual(modern.VERIFICATION_PROFILES[bugfixed], expected)
        self.assertIsNot(modern.VERIFICATION_PROFILES[production], modern.VERIFICATION_PROFILES[bugfixed])


class VariantIsolationTests(unittest.TestCase):
    def test_custom_output_cannot_overwrite_the_other_flavour(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            stack.enter_context(patch.object(variants, 'BUILD', root))
            stack.enter_context(patch.object(variants, 'ROM_PATH', root / 'sonic2-mdplus.md'))
            alias = root / 'sonic2-modern-mdplus.md'
            stack.enter_context(patch.object(modern, 'MODERN_ROM_PATH', alias))
            prepare = stack.enter_context(patch.object(modern, 'prepare_modern'))
            for variant in BuildVariant:
                other = next(v for v in BuildVariant if v is not variant)
                other.rom_path.write_bytes(b'previous ROM')
                link = root / (variant.value + '-custom.md')
                link.symlink_to(other.rom_path)
                outputs = [other.rom_path, link, other.prepared_dir / 'custom.md']
                if other is BuildVariant.PRODUCTION:
                    outputs.append(alias)
                for output in outputs:
                    with self.subTest(variant=variant, output=output), self.assertRaisesRegex(BuildError, 'belongs to'):
                        modern.build_modern(output, variant=variant)
                self.assertEqual(other.rom_path.read_bytes(), b'previous ROM')
            prepare.assert_not_called()

    def test_prepare_and_build_in_both_orders_preserve_other_outputs(self):
        # Exercise real preparation/publishing; replace only external inputs and
        # assembler/verifier operations. The compiled check covers real ROMs.
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            checkout = root / 'source-modern'
            checkout.mkdir()
            (checkout / 'input-marker').write_text('immutable input')
            stack.enter_context(patch.object(variants, 'BUILD', root))
            stack.enter_context(patch.object(variants, 'ROM_PATH', root / 'sonic2-mdplus.md'))
            stack.enter_context(patch.object(modern, 'BUILD', root))
            stack.enter_context(patch.object(modern, 'ROM_PATH', root / 'sonic2-mdplus.md'))
            alias = root / 'sonic2-modern-mdplus.md'
            stack.enter_context(patch.object(modern, 'MODERN_ROM_PATH', alias))
            stack.enter_context(patch.object(modern, 'SOURCE_MODERN_DIR', checkout))
            stack.enter_context(patch.object(modern, '_git_output', return_value=modern.AUDITED_MODERN_COMMIT))

            def clone(url, commit, destination, local_source):
                self.assertEqual(local_source, checkout)
                self.assertEqual(commit, modern.AUDITED_MODERN_COMMIT)
                destination.mkdir()
                for name in ('s2.asm', 's2.sounddriver.asm', 's2.constants.asm'):
                    (destination / name).write_bytes(b'synthetic source')

            stack.enter_context(patch.object(modern, '_clone_at', side_effect=clone))
            stack.enter_context(patch.object(modern, '_prepare_modern_source', side_effect=lambda data, name, **kwargs: data))
            stack.enter_context(patch.object(modern.bugfixed, 'apply_policy'))
            stack.enter_context(patch.object(modern, 'require_program', return_value='lua'))

            def run(args, *, cwd=None):
                if cwd is not None:
                    (cwd / 's2built.bin').write_bytes(b'synthetic compiled bytes')

            stack.enter_context(patch.object(modern, 'run', side_effect=run))
            verify = stack.enter_context(patch.object(modern, 'verify_modern', return_value={}))
            stack.enter_context(patch.object(modern, 'verify_modern_driver'))
            stack.enter_context(patch.object(modern, 'assembled_modern_driver', return_value=b''))
            def symbols(path):
                variant = next(v for v in BuildVariant if path.parent == v.prepared_dir)
                layout = modern.LAYOUT_PROFILES[variant]
                return layout.handoff | layout.router | {n: a for n, (a, _) in modern.RAM_STATE.items()}

            stack.enter_context(patch.object(modern, 'modern_symbols', side_effect=symbols))

            def snapshot(path):
                return {p.relative_to(path): (p.read_bytes(), p.stat().st_mtime_ns)
                        for p in path.rglob('*') if p.is_file()}

            for variant in BuildVariant:
                modern.build_modern(variant=variant)
            self.assertTrue(alias.samefile(BuildVariant.PRODUCTION.rom_path))
            for variant in (BuildVariant.BUGFIXED, BuildVariant.PRODUCTION):
                other = next(v for v in BuildVariant if v is not variant)
                before = snapshot(other.prepared_dir)
                rom_before = (other.rom_path.read_bytes(), other.rom_path.stat().st_mtime_ns)
                alias_before = alias.lstat().st_mtime_ns
                modern.prepare_modern(variant=variant)
                modern.build_modern(variant=variant)
                verify.assert_called_with(variant.prepared_dir / 's2built.bin', strict_regression=True, variant=variant)
                self.assertEqual(snapshot(other.prepared_dir), before)
                self.assertEqual((other.rom_path.read_bytes(), other.rom_path.stat().st_mtime_ns), rom_before)
                if variant is BuildVariant.BUGFIXED:
                    self.assertEqual(alias.lstat().st_mtime_ns, alias_before)
                self.assertTrue(alias.samefile(BuildVariant.PRODUCTION.rom_path))
            self.assertEqual((checkout / 'input-marker').read_text(), 'immutable input')
            self.assertEqual(len(list(checkout.iterdir())), 1)
            contents = [{p: data for p, (data, _) in snapshot(v.prepared_dir).items()} for v in BuildVariant]
            self.assertNotEqual(*contents)

    def test_packages_coexist_with_unchanged_audio_and_selected_verifier(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            stack.enter_context(patch.object(package, 'DIST', root / 'dist'))
            stack.enter_context(patch.object(variants, 'BUILD', root))
            stack.enter_context(patch.object(variants, 'ROM_PATH', root / 'sonic2-mdplus.md'))
            verify = stack.enter_context(patch.object(package, 'verify_modern'))
            audio = root / 'track03.wav'
            with wave.open(str(audio), 'wb') as wav:
                wav.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
                wav.writeframes(bytes(588 * 4 * 2))
            manifest = root / 'tracks.json'
            basename = json.loads(DEFAULT_MANIFEST.read_text())['rom_basename']
            self.assertEqual(basename, 'Sonic 2 - Addryu Mega-CD Remix MD+')
            manifest.write_text(json.dumps({'schema': 1, 'rom_basename': basename, 'tracks': [{
                'track': 3, 'enabled': True, 'source': 'input.wav', 'mode': 'loop',
                'loop_start_sector': 0, 'loop_end_sector': 2,
            }]}))
            outputs = {}
            for variant in BuildVariant:
                variant.rom_path.write_bytes(b'synthetic ROM')
            for variant in (*BuildVariant, *reversed(list(BuildVariant))):
                output = package.assemble(manifest, audio_dir=root, variant=variant)
                verify.assert_called_with(variant.rom_path, strict_regression=True, variant=variant)
                name = basename + (' (Bugfixed)' if variant is BuildVariant.BUGFIXED else '')
                self.assertEqual(output, root / 'dist' / name)
                self.assertEqual({p.name for p in output.iterdir()},
                                 {f'{name}.md', f'{name}.cue', 'track03.wav', 'SHA256SUMS.json'})
                self.assertEqual((output / f'{name}.md').read_bytes(), variant.rom_path.read_bytes())
                self.assertEqual((output / 'track03.wav').read_bytes(), audio.read_bytes())
                self.assertEqual((output / f'{name}.cue').read_text(), package.cue_text(json.loads(manifest.read_text())))
                hashes = json.loads((output / 'SHA256SUMS.json').read_text())
                self.assertEqual(hashes, {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in output.iterdir() if p.name != 'SHA256SUMS.json'})
                outputs[output] = {p.name: p.read_bytes() for p in output.iterdir()}
                for previous, content in outputs.items():
                    self.assertEqual({p.name: p.read_bytes() for p in previous.iterdir()}, content)
            self.assertEqual(len(outputs), 2)
            verify.side_effect = BuildError('wrong Bugfixed ROM')
            with patch.object(package.shutil, 'copy2') as copy, self.assertRaisesRegex(BuildError, 'wrong Bugfixed'):
                package.assemble(manifest, audio_dir=root, variant=BuildVariant.BUGFIXED)
            copy.assert_not_called()
