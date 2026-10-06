"""Compiled dependency gates for two deferred upstream Z80 fixes.

Run after all four maintained builds, with the emulation venv and PYTHONPATH=.
Research assemblies are disposable, unsupported inputs under ignored build/;
global FixDriverBugs remains zero even in the probes. No policy is changed.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from check_modern_live_binary import LiveMachine
from check_stock_bugfixed_binary import driver
from cpu_machine import Machine

from tools.mdplus_builder import bugfixed, modern
from tools.mdplus_builder.common import BUILD, SOURCE_MODERN_DIR
from tools.mdplus_builder.source import _clone_at, genesis_checksum
from tools.mdplus_builder.variants import BuildVariant

PIN = '380f37a731bfc720bb0371a35a593184a7ec5e43'
PRISTINE = 'ff34692c633f96d50073c24f6ebb72df5c739892c31be6b19b2ae604e76232c7'
CURATED = 'ce96d9dda766fefa33de23ddccea373b58aceb92ec2a91fba30d998105d667a8'
PROBE_SOURCE_HASHES = {
    'a-only': '8efeb55c7d5bfc892f9eadf48313d5f0f973c07b9c1d262afbeecc08bd13befe',
    'a-prerequisite': 'f30a80962f2a2cda5aa1efb944efa4613c52496b48dc75d9b2d4865152cc16eb',
    'a-coupled': 'fb77f446db90b1449dbaa9a2f828599c84f3dfe0b77ac3f1bf88e2702e27c298',
    'b-only': 'f7bdccde1733c6be84ab1890bbdf0b8ef7ed21755448afc358f35803560e6991',
    'b-prerequisite': 'b6a780252e5d6710ba51484cfe2175c5c2f607f5efdfb3b2b7018fcb8e9035c6',
    'b-coupled': '66e512440c4679cb122f79a8c1f3da856ce3429c688cee7fa40c23e5c255f8ec',
}
RELEASED = {
    'stock': ('9BE7', 'bd93d95a110be99e9eb9bafb3d31806f',
              '909e5f229fc4052f3c3c3c9a97c3a6b345117990796b0226dffbc98f88f00bc7', 3942, 4872,
              'bb6d42f875017b434f54ab76d02b476d0efbdc13db23e327d07080cfc84a477f'),
    'mdplus': ('0951', '5d3e5979d3f110d2761da3166b14b7cf',
               'e9f56f0efd72844918918f2efdecf6183f5bdabb47f235b61cc511a16942d3b5', 4011, 4986,
               'f2883990453ba7deedc682b3970be0d2c73fea99a566a30d43362c2769ac7041'),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def probe_source(data, *, a=False, remove_stop=False, b=False, init=False):
    """Select only pinned branch bodies for dependency experiments, never a build flavour."""
    assert digest(data) == CURATED
    text = data.decode()
    for start, end, modifications in (
        ('zPlayMusic:\n', '; zloc_784\n', (
            ('    if ~~FixDriverBugs\n', '    if 0\n', 0, remove_stop),
            ('    if FixDriverBugs\n', '    if 1\n', 0, a),
            ('    if ~~FixDriverBugs\n', '    if 0\n', -1, a))),
        ('zPSGNoteOff:\n', '; End of function zPSGNoteOff', (
            ('    if FixDriverBugs\n', '    if 1\n', 0, b),)),
        ('zInitMusicPlayback:\n', '; End of function zInitMusicPlayback', (
            ('    if FixDriverBugs\n', '    if 1\n', -1, init),)),
    ):
        left, right = text.index(start), text.index(end)
        region = text[left:right]
        for old, new, index, enabled in modifications:
            if enabled:
                positions = [i for i in range(len(region)) if region.startswith(old, i)]
                position = positions[index]
                region = region[:position] + new + region[position + len(old):]
        text = text[:left] + region + text[right:]
    assert text.count('\nFixDriverBugs = 0\n') == 1
    return text.encode()


class DriverMachine(LiveMachine):
    """Existing actual-loader / dual-CPU harness, with explicit research inputs."""

    def __init__(self, source, symbols):
        Machine.__init__(self, source, symbols)

    def begin(self, label, a=0):
        self.z80.pc, self.z80.sp = self.symbols[label], 0x1B60
        self.z80.ix, self.z80.a = self.symbols['zAbsVar'], a
        self.z80.memory[0x1B60:0x1B62] = bytes.fromhex('0070')

    def until(self, address):
        self.z80.set_breakpoint(address)
        try:
            for _ in range(30):
                self.z80.ticks_to_stop = 100_000
                self.z80.run()
                if self.z80.pc == address:
                    return
            raise AssertionError(f'Did not reach ${address:04X}; PC=${self.z80.pc:04X}')
        finally:
            if address != 0x7000:
                self.z80.clear_breakpoint(address)

    def effect(self, name):
        self.setz('zAbsVar.Queue0', self.symbols[name])
        self.callz('zCycleQueue')
        selected = self.getz('zAbsVar.QueueToPlay')
        self.callz('zPlaySoundByIndex', selected)
        return selected

    def complete_jingle(self):
        for frame in range(600):
            self.vint_frame()
            if not self.getz('zAbsVar.1upPlaying'):
                return frame + 1
        raise AssertionError('1-up did not restore')

    def complete_fade(self):
        # SFX are intentionally suppressed during the native restore fade;
        # testing before this gate opens would misidentify normal suppression.
        for frame in range(600):
            self.vint_frame()
            if not self.getz('zAbsVar.FadeInFlag'):
                return frame + 1
        raise AssertionError('Restore fade did not finish')

    def noise_active(self):
        self.callz('zPlaySoundByIndex', self.symbols['MusID_CNZ'])
        self.events.clear()
        for frame in range(600):
            self.vint_frame()
            if any(a == 0x7F11 and v & 0xF0 == 0xF0 and v != 0xFF for a, v in self.events):
                assert self.getz('zSongPSG3.VoiceControl') == 0xE0
                self.events.clear()
                return frame + 1
        raise AssertionError('CNZ noise never became active')


class SelectiveDriverBinaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='driver-gates-', dir=BUILD)
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.inputs, cls.images, cls.report = {}, {}, {}
        for kind, path, listing in (
            ('stock', bugfixed.STOCK_BUGFIXED_ROM_PATH, bugfixed.STOCK_BUGFIXED_LISTING_PATH),
            ('mdplus', BuildVariant.BUGFIXED.rom_path, BuildVariant.BUGFIXED.prepared_dir / 's2.lst'),
        ):
            source = cls.root / kind
            source.mkdir()
            rom = path.read_bytes()
            (source / 's2built.bin').write_bytes(rom)
            symbols = modern.modern_symbols(listing)
            cls.inputs[kind] = source, symbols
            cls.images[kind] = rom, symbols
        # Compile entire drivers with the real upstream build, compression and
        # 68000 loader, rather than injecting hand-encoded instructions into RAM.
        for name, options in (
            ('a-only', {'a': True}),
            ('a-prerequisite', {'remove_stop': True}),
            ('a-coupled', {'remove_stop': True, 'a': True}),
            ('b-only', {'b': True}),
            ('b-prerequisite', {'init': True}),
            ('b-coupled', {'init': True, 'b': True}),
        ):
            work = cls.root / name
            _clone_at('', PIN, work, SOURCE_MODERN_DIR)
            bugfixed.apply_policy(work)
            original = (work / 's2.sounddriver.asm').read_bytes()
            assert digest(original) == CURATED
            prepared = probe_source(original, **options)
            assert digest(prepared) == PROBE_SOURCE_HASHES[name]
            (work / 's2.sounddriver.asm').write_bytes(prepared)
            # Preserve assembler object evidence without changing tracked build.lua.
            (work / 'modern_build.lua').write_bytes(Path(modern.__file__).with_name('modern_build.lua').read_bytes())
            result = subprocess.run(['lua', 'modern_build.lua'], cwd=work, check=False)
            if result.returncode:
                # B-only crosses the upstream one-byte table boundary. Upstream
                # emits a valid ROM then returns 1 for this precise warning. This
                # is research evidence, not acceptance by a maintained verifier.
                assert name == 'b-only' and result.returncode == 1
                warning = (work / 's2.log').read_text()
                assert warning.count(': warning:') == 1 and ': error:' not in warning
                assert 'had to insert 7h   bytes of padding before improperly located data at 0DF9h' in warning
                cls.report['b-only-warning'] = warning
            rom = (work / 's2built.bin').read_bytes()
            symbols = modern.modern_symbols(work / 's2.lst')
            assert symbols['FixDriverBugs'] == 0
            cls.inputs[name] = work, symbols
            cls.images[name] = rom, symbols
            packed, loaded = driver(rom, symbols)
            assembled = modern.assembled_modern_driver(work / 'forge-s2.p')
            assert loaded == assembled
            actual = DriverMachine(work, symbols)
            assert actual.loaded == len(assembled)
            assert bytes(actual.z80.memory[:actual.loaded]) == assembled
            cls.report[name] = {'global_FixDriverBugs': 0, 'packed_bytes': len(packed),
                                'loaded_bytes': len(loaded), 'loaded_sha256': digest(loaded),
                                'source_sha256': digest((work / 's2.sounddriver.asm').read_bytes())}

    @classmethod
    def tearDownClass(cls):
        (BUILD / 'driver-investigation' / 'evidence.json').parent.mkdir(parents=True, exist_ok=True)
        (BUILD / 'driver-investigation' / 'evidence.json').write_text(json.dumps(cls.report, indent=2) + '\n')

    def machine(self, name):
        return DriverMachine(*self.inputs[name])

    def test_pinned_complete_source_and_no_selected_executable_change(self):
        pristine = (SOURCE_MODERN_DIR / 's2.sounddriver.asm').read_bytes()
        self.assertEqual(digest(pristine), PRISTINE)
        curated = bugfixed.transform_source(pristine, 's2.sounddriver.asm')
        self.assertEqual(curated, pristine.replace(b'FixDriverBugs = fixBugs', b'FixDriverBugs = 0'))
        self.assertEqual(digest(curated), CURATED)
        for variant, source in ((BuildVariant.PRODUCTION, pristine), (BuildVariant.BUGFIXED, curated)):
            # Complete prepared driver, including all Forge transforms, matches
            # the unchanged production adapter's output from its pinned input.
            self.assertEqual((variant.prepared_dir / 's2.sounddriver.asm').read_bytes(),
                             modern._prepare_modern_source(source, 's2.sounddriver.asm', variant=variant))
        for name in self.images:
            symbols = self.images[name][1]
            self.assertEqual(symbols['FixDriverBugs'], 0)
            self.assertEqual(symbols['FixMusicAndSFXDataBugs'], 0)
            self.assertEqual(symbols['ForgeFix2PSpritePageFlip'], 0)

    def test_complete_rom_and_driver_identities_unchanged(self):
        for kind in ('stock', 'mdplus'):
            rom, symbols = self.images[kind]
            checksum, md5, sha, packed_size, loaded_size, loaded_sha = RELEASED[kind]
            packed, loaded = driver(rom, symbols)
            self.assertEqual(len(rom), 2_097_152)
            self.assertEqual(genesis_checksum(rom), (int(checksum, 16),) * 2)
            self.assertEqual(hashlib.md5(rom, usedforsecurity=False).hexdigest(), md5)
            self.assertEqual(digest(rom), sha)
            self.assertEqual((len(packed), len(loaded), digest(loaded)), (packed_size, loaded_size, loaded_sha))
            self.assertEqual(bytes(self.machine(kind).z80.memory[:len(loaded)]), loaded)
            self.report[kind] = {'sha256': sha, 'packed_bytes': packed_size, 'loaded_bytes': loaded_size,
                                 'loaded_sha256': loaded_sha, 'changed_ROM_bytes': 0,
                                 'inverse': 'identity: no newly selected transformation'}
        modern.verify_modern(BuildVariant.PRODUCTION.rom_path, strict_regression=True)
        modern.verify_stock_modern(modern.STOCK_MODERN_ROM_PATH)

    def test_a_compiled_instruction_order_and_size_neutral_move(self):
        for kind in ('stock', 'mdplus', 'a-only', 'a-prerequisite', 'a-coupled'):
            rom, s = self.images[kind]
            _, code = driver(rom, s)
            p = s['zPlayMusic']
            stop = b'\xf5\xcd' + s['zStopSoundEffects'].to_bytes(2, 'little') + b'\xf1'
            if kind not in ('a-prerequisite', 'a-coupled'):
                self.assertEqual(code[p:p + 5], stop)
                self.assertEqual(code[s['zStopSoundEffects']:s['zStopSoundEffects'] + 4], bytes.fromhex('af32801b'))
            clear = bytes.fromhex('af32801b')
            backup = bytes.fromhex('11381e21801b01bc01edb03e8032911b')
            expected = clear + backup if kind in ('a-only', 'a-coupled') else backup + clear
            self.assertEqual(code.count(expected), 1, kind)
            restore = bytes.fromhex('21381e11801b01bc01edb0')
            self.assertEqual(code[s['cfFadeInToPrevious']:s['cfFadeInToPrevious'] + 11], restore)
        baseline = driver(*self.images['stock'])[1]
        selected = driver(*self.images['a-only'])[1]
        self.assertEqual(len(selected), len(baseline))
        p = baseline.index(bytes.fromhex('11381e21801b01bc01edb03e8032911baf32801b'))
        restored = bytearray(selected)
        restored[p:p + 20] = selected[p + 4:p + 20] + selected[p:p + 4]
        self.assertEqual(restored, baseline)  # Every changed loaded byte accounted for.
        self.report['a-only']['loaded_changed_offsets'] = [
            i for i, (a, b) in enumerate(zip(baseline, selected, strict=True)) if a != b]
        self.report['a-only']['backup_start'] = p

    def test_a_complete_backup_contains_already_cleared_priority(self):
        for kind in ('stock', 'mdplus', 'a-only'):
            m = self.machine(kind)
            m.callz('zPlaySoundByIndex', m.symbols['MusID_EHZ'])
            self.assertEqual(m.effect('SndID_Ring'), 0xB5)
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0x70)
            packed, loaded = driver(*self.images[kind])
            self.assertTrue(packed)
            copy = loaded.index(bytes.fromhex('11381e21801b01bc01edb0'))
            m.begin('zPlaySoundByIndex', 0x98)
            m.until(copy)
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0)
            expected = bytes(m.z80.memory[0x1B80:0x1D3C])
            self.assertEqual(len(expected), 0x1BC)  # 24 variables + ten 42-byte song tracks, no SFX.
            m.until(copy + 11)
            self.assertEqual(bytes(m.z80.memory[0x1E38:0x1FF4]), expected)
            m.until(0x7000)

    def test_a_released_and_selected_round_trip_accept_lower_priority_sfx(self):
        for kind in ('stock', 'mdplus', 'a-only'):
            m = self.machine(kind)
            m.callz('zPlaySoundByIndex', m.symbols['MusID_EHZ'])
            m.effect('SndID_Ring')
            m.callz('zPlaySoundByIndex', 0x98)
            self.assertEqual(m.getz('zSaveVar.SFXPriorityVal'), 0)
            frames = m.complete_jingle()
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0)
            fade = m.complete_fade()
            self.assertEqual(m.effect('SndID_Splash'), 0xAA)
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0x68)
            self.assertTrue(m.getz('zSFX_PSG3.PlaybackControl') & 0x80)
            self.report.setdefault('a-round-trip', {})[kind] = {'jingle_VInts': frames, 'fade_VInts': fade,
                                                               'saved_priority': 0, 'splash_accepted': True}

    def test_a_stale_failure_requires_removing_retained_stop_sfx(self):
        for kind, expected, accepted in (('a-prerequisite', 0x70, False), ('a-coupled', 0, True)):
            m = self.machine(kind)
            m.callz('zPlaySoundByIndex', m.symbols['MusID_EHZ'])
            self.assertEqual(m.effect('SndID_Ring'), 0xB5)
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0x70)
            m.callz('zPlaySoundByIndex', 0x98)
            self.assertEqual(m.getz('zSaveVar.SFXPriorityVal'), expected)
            frames = m.complete_jingle()
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), expected)
            m.complete_fade()
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), expected)
            m.setz('zAbsVar.Queue0', 0xAA)
            m.callz('zCycleQueue')
            self.assertEqual(m.getz('zAbsVar.Queue0'), 0)
            self.assertEqual(m.getz('zAbsVar.QueueToPlay'), 0xAA if accepted else 0x80)
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0x68 if accepted else 0x70)
            self.report[kind].update(saved_priority=expected, restored_priority=expected,
                                     splash_accepted=accepted, jingle_VInts=frames)

    def test_a_priority_oracle_and_real_game_queue_sites(self):
        for kind in ('stock', 'mdplus'):
            m = self.machine(kind)
            for sound, value in (('SndID_Ring', 0x70), ('SndID_Splash', 0x68),
                                 ('SndID_CasinoBonus', 0x6F), ('SndID_HTZLiftClick', 0x60),
                                 ('SndID_Jump', 0x80), ('SndID_Roll', 0x70),
                                 ('SndID_Spring', 0x70), ('SndID_Flipper', 0x70)):
                index = m.symbols[sound] - m.symbols['SndID__First']
                self.assertEqual(m.z80.memory[m.symbols['zSFXPriority'] + index], value, sound)
        source = (SOURCE_MODERN_DIR / 's2.asm').read_text()
        self.assertIn('move.w\t#SndID_Splash,d0', source)
        self.assertIn('move.w\t#SndID_Ring,d0', source)
        self.assertIn('move.w\t#MusID_ExtraLife,d0', source)

    def test_a_actual_99th_and_100th_ring_calls_do_not_save_stale_priority(self):
        m = self.machine('mdplus')
        m.start('MusID_ARZ')
        m.put('Ring_count', 98, 2)
        m.call68('CollectRing_1P')
        self.assertEqual(m.get68('Sound_Queue.SFX1'), 0xB5)
        m.input()
        m.vint_frame()
        self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0x70)
        m.call68('CollectRing_1P')
        # The threshold replaces the ring request with the 1-up ID; it does
        # not play both. The preceding (99th) ring establishes the priority.
        self.assertEqual(m.get68('Sound_Queue.SFX1'), 0x98)
        m.input()
        m.vint_frame()
        self.assertTrue(m.getz('zAbsVar.1upPlaying'))
        self.assertEqual(m.getz('zSaveVar.SFXPriorityVal'), 0)
        m.complete_jingle()
        m.complete_fade()
        self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0)
        self.assertEqual(m.effect('SndID_Splash'), 0xAA)
        self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0x68)

    def test_b_compiled_note_off_writes_and_override_guard(self):
        for kind in ('stock', 'mdplus', 'b-only', 'b-prerequisite', 'b-coupled'):
            m = self.machine(kind)
            _, loaded = driver(*self.images[kind])
            p = m.symbols['zPSGNoteOff']
            prefix = bytes.fromhex('ddcb0056c0dd7e01f61f32117f')
            self.assertEqual(loaded[p:p + len(prefix)], prefix)
            tail = bytes.fromhex('fedfc03eff32117fc9') if kind in ('b-only', 'b-coupled') else b'\xc9'
            self.assertEqual(loaded[p + len(prefix):p + len(prefix) + len(tail)], tail)
            for voice, writes in ((0x80, [0x9F]), (0xA0, [0xBF]),
                                   (0xC0, [0xDF, 0xFF] if kind in ('b-only', 'b-coupled') else [0xDF]),
                                   (0xE0, [0xFF])):
                for override in (0, 4):
                    m.events.clear()
                    m.z80.ix = m.symbols['zSongPSG3']
                    m.setz('zSongPSG3.VoiceControl', voice)
                    m.setz('zSongPSG3.PlaybackControl', override)
                    m.begin('zPSGNoteOff')
                    m.z80.ix = m.symbols['zSongPSG3']
                    m.until(0x7000)
                    self.assertEqual([v for a, v in m.events if a == 0x7F11], [] if override else writes)

    def test_b_retail_init_mutes_noise_upstream_init_does_not(self):
        for kind in ('stock', 'mdplus', 'b-only', 'b-prerequisite', 'b-coupled'):
            m = self.machine(kind)
            m.callz('zInitMusicPlayback')
            writes = [v for a, v in m.events if a == 0x7F11]
            self.assertEqual(writes, [] if kind in ('b-prerequisite', 'b-coupled') else [0x9F, 0xBF, 0xDF, 0xFF])
            _, loaded = driver(*self.images[kind])
            s = m.symbols
            code = loaded[s['zInitMusicPlayback']:s['zSpeedUpMusic']]
            if kind in ('b-prerequisite', 'b-coupled'):
                self.assertEqual(m.getz('zSongPSG3.VoiceControl'), 0xC0)
                expected = (bytes.fromhex('dd21981b060a112a0021') +
                            s['zFMDACInitBytes'].to_bytes(2, 'little') +
                            bytes.fromhex('7e23dd7701dd1910f7c9'))
                self.assertEqual(code[-22:], expected)
            else:
                expected = (b'\xcd' + s['zFMSilenceAll'].to_bytes(2, 'little') +
                            b'\xc3' + s['zPSGSilenceAll'].to_bytes(2, 'little'))
                self.assertEqual(code[-6:], expected)

    def test_b_actual_cnz_to_end_level_dependency_gate(self):
        for kind in ('stock', 'mdplus', 'b-only', 'b-prerequisite', 'b-coupled'):
            m = self.machine(kind)
            frames = m.noise_active()
            m.callz('zPlaySoundByIndex', m.symbols['MusID_EndLevel'])
            writes = [v for a, v in m.events if a == 0x7F11]
            self.assertEqual(0xFF in writes, kind != 'b-prerequisite')
            self.assertEqual(m.getz('zSongPSG3.VoiceControl'), 0xC0)
            if kind in ('stock', 'mdplus'):
                self.assertEqual(writes, [0x9F, 0xBF, 0xDF, 0xFF, 0x9F, 0xBF, 0xDF])
            self.report.setdefault('b-CNZ-EndLevel', {})[kind] = {'noise_active_VInt': frames, 'PSG_writes': writes,
                                                                 'noise_muted': 0xFF in writes}

    def test_b_psg3_sfx_setup_already_mutes_both_tone_and_noise(self):
        for kind in ('stock', 'mdplus'):
            m = self.machine(kind)
            m.noise_active()
            m.effect('SndID_SpindashRelease')
            writes = [v for a, v in m.events if a == 0x7F11]
            self.assertEqual(writes[:2], [0xDF, 0xFF])

    def test_b_native_noise_handoff_stops_noise_with_retail_note_off(self):
        m = self.machine('mdplus')
        m.noise_active()
        m.request('MusID_EHZ')
        m.finish()
        self.assertIn((0x7F11, 0xFF), m.events)
        self.assertEqual(m.state_bytes(), (1, 0, 0, 0, 1))
        self.assertEqual(m.commands, [0x15FF, 0x1203])

    def test_a_mdplus_repeated_native_jingle_priority_and_restoration(self):
        m = self.machine('mdplus')
        m.start()
        for repetition in range(3):
            m.events.clear()
            m.request('SndID_Ring', 'PlaySound2')
            m.input()
            m.vint_frame()
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0x70)
            m.request('MusID_ExtraLife')
            m.input()
            m.callz('zPlaySoundByIndex', 0x98)
            self.assertTrue(m.getz('zSongFM1.PlaybackControl') & 0x80)
            self.assertEqual(m.getz('zSaveVar.SFXPriorityVal'), 0)
            for _ in range(255):
                m.duck_vint()
                m.vint_frame()
            self.assertFalse(m.getz('zAbsVar.1upPlaying'))
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0)
            self.assertEqual(m.commands, [0x1519] * 255 + [0x15FF])
            self.assertEqual(m.state_bytes(), (1, 0, 0, 0, 1))
            self.assertFalse(m.getz('zSongFM1.PlaybackControl') & 0x80)
            m.complete_fade()
            m.events.clear()
            m.request('SndID_Splash', 'PlaySound2')
            m.input()
            m.vint_frame()
            self.assertEqual(m.getz('zAbsVar.SFXPriorityVal'), 0x68)
            self.assertTrue(m.getz('zSFX_PSG3.PlaybackControl') & 0x80)
            self.assertEqual(m.commands, [])
            # Finish the accepted SFX before establishing the next high priority.
            for _ in range(120):
                m.vint_frame()
            self.report['MD+-repetitions'] = repetition + 1


if __name__ == '__main__':
    unittest.main()
