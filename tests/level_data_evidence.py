"""Independent ROM reconstruction for level and selective-audio binary audits."""
from __future__ import annotations

import hashlib

from tools.mdplus_builder.common import SOURCE_MODERN_DIR
from tools.mdplus_builder.source import _git_output, genesis_checksum

# Independently observed pre-level-data locations, shared by stock and MD+.
OBJECT_ORDER = (
    ('EHZ_1', 0xE6E4A), ('EHZ_2', 0xE717A), ('MTZ_1', 0xE7534),
    ('MTZ_2', 0xE79C0), ('MTZ_3', 0xE7EEE), ('WFZ_1', 0xE8548),
    ('WFZ_2', 0xE88FC), ('HTZ_1', 0xE8902), ('HTZ_2', 0xE8C68),
    ('HPZ_1', 0xE9280), ('HPZ_2', 0xE9394), ('OOZ_1', 0xE93A0),
    ('OOZ_2', 0xE9814), ('MCZ_1', 0xE9C8E), ('MCZ_2', 0xE9FA0),
    ('CNZ_1', 0xEA31E), ('CNZ_2', 0xEA9D8), ('CPZ_1', 0xEAFD2),
    ('CPZ_2', 0xEB36E), ('DEZ_1', 0xEB830), ('DEZ_2', 0xEB854),
    ('ARZ_1', 0xEB85A), ('ARZ_2', 0xEBCA4), ('SCZ_1', 0xEC1DE),
    ('SCZ_2', 0xEC34C), ('Null', 0xEC352),
)
TABLE_ORDER = (
    'EHZ_1', 'EHZ_2', *(['Null'] * 6), 'MTZ_1', 'MTZ_2', 'MTZ_3', 'MTZ_3',
    'WFZ_1', 'WFZ_2', 'HTZ_1', 'HTZ_2', 'HPZ_1', 'HPZ_2', 'Null', 'Null',
    'OOZ_1', 'OOZ_2', 'MCZ_1', 'MCZ_2', 'CNZ_1', 'CNZ_2', 'CPZ_1', 'CPZ_2',
    'DEZ_1', 'DEZ_2', 'ARZ_1', 'ARZ_2', 'SCZ_1', 'SCZ_2',
)
PRE_LEVEL = {
    'stock': ('FD6C', '869869560951eaad0fc327057e50e8ae3cf4ea04c877ff81e8c22a0b17cc02fa'),
    'mdplus': ('6AD6', 'b04c2fd39e804719db599cca014966b19f07b16140688ee265c1dc759cb2212b'),
}


# Independent input/target locks and slice-based derivation. Do not import the
# production policy, parser, semantic diff or transformation into this evidence.
INPUT_HASHES = {
    'EHZ_2': (
        '7b3384fe361309fd2a36961116bf8d89c22399acb88fa7d632a467cc062c1560',
        'ba2b2db75688f309847a90172991f151e233d41c272fbd5eb3462f3650c00e5d',
        'ba2b2db75688f309847a90172991f151e233d41c272fbd5eb3462f3650c00e5d'),
    'ARZ_2': (
        '08f21b09e76d4920e5861d9cdc25329ee304ea69e3171d8551b5c5c729d82297',
        '2b52c83cdc3a87bf594292c9a2769c7d99595a04159231ed9879588d6d59f39e',
        '30fea857b2209a2b33f1befec90c446081356a8203f9e665874746bda0720ad2'),
    'WFZ_1': (
        'b5afcb63c936ae62d860292a3ec4a7c4e7ff5cb24cf88130e4a6ae231bb737c4',
        '570e79e93a71296f69f91413b6f615de83c662ab3d6f9e31ff864cc001b9cbab',
        '570e79e93a71296f69f91413b6f615de83c662ab3d6f9e31ff864cc001b9cbab'),
}


def audited_layouts():
    """Derive independent expected entries from immutable generated inputs only."""
    assert _git_output(SOURCE_MODERN_DIR, 'rev-parse', 'HEAD') == (
        '380f37a731bfc720bb0371a35a593184a7ec5e43')
    result = {}
    for name, hashes in INPUT_HASHES.items():
        relative = f'level/objects/{name}.bin'
        inputs = [(SOURCE_MODERN_DIR / prefix / relative).read_bytes()
                  for prefix in ('', 'Utility Project Files/Fixed Files')]
        for data, digest in zip(inputs, hashes[:2], strict=True):
            assert hashlib.sha256(data).hexdigest() == digest, name
            assert len(data) % 6 == 0, name
        retail, reference = [tuple(data[i:i + 6] for i in range(0, len(data), 6))
                             for data in inputs]
        if name == 'EHZ_2':
            # Whole-reference equality accounts for every unchanged retail entry.
            target = (retail[:29] + reference[29:30] + retail[29:64]
                      + reference[65:66] + retail[64:142]
                      + reference[144:145] + retail[142:])
            assert reference == target
        elif name == 'ARZ_2':
            # Reference index 118 corresponds to retail 119 after deletion 33.
            insertion = reference[118:119]
            assert reference == retail[:33] + retail[34:119] + insertion + retail[119:]
            target = retail[:119] + insertion + retail[119:]
            assert target[33] == retail[33]  # Retain the bubble generator verbatim.
        else:
            target = retail[:127] + reference[127:128] + retail[128:]
            assert reference == target
            assert reference[127][:5] == retail[127][:5]
            assert reference[127][5] != retail[127][5]
        assert hashlib.sha256(b''.join(target)).hexdigest() == hashes[2], name
        for entries in (retail, reference, target):
            xs = [int.from_bytes(entry[:2], 'big') for entry in entries]
            assert xs == sorted(xs) and all(x < 0xFFFF for x in xs), name
        result[name] = retail, reference, target
    return result


def pre_level_symbols(symbols):
    result = dict(symbols)
    for name, address in OBJECT_ORDER:
        shift = 0 if address <= 0xE717A else 18 if address <= 0xEBCA4 else 24
        assert symbols['Objects_' + name] == address + shift, name
        result['Objects_' + name] = address
    result['paddingSoFar'] += 24
    return result


def restore_pre_level(rom, symbols, kind):
    """Reverse ONLY independently enumerated edits; frozen full hash guards the rest."""
    layouts = audited_layouts()
    pre_level_symbols(symbols)
    assert len(rom) == 0x200000
    assert symbols['Off_Objects'] == 0xE6E00
    assert symbols['SoundDriverLoad'] == 0xED000
    restored = bytearray(rom)
    # Reverse in descending address order; preserve all intervening shifted bytes.
    blob = bytearray(rom[0xE717A:0xED000])
    arz = 0xEBCB6 + 119 * 6 - 0xE717A
    assert blob[arz:arz + 6] == layouts['ARZ_2'][2][119]
    del blob[arz:arz + 6]
    wfz = 0xE855A + 127 * 6 - 0xE717A
    assert blob[wfz:wfz + 6] == layouts['WFZ_1'][2][127]
    blob[wfz:wfz + 6] = layouts['WFZ_1'][0][127]
    for index in (144, 65, 29):
        assert blob[index * 6:index * 6 + 6] == layouts['EHZ_2'][1][index]
        del blob[index * 6:index * 6 + 6]
    blob.extend(bytes(24))
    restored[0xE717A:0xED000] = blob
    addresses = dict(OBJECT_ORDER)
    for index, name in enumerate(TABLE_ORDER):
        offset = 0xE6E00 + index * 2
        actual = symbols['Objects_' + name] - 0xE6E00
        assert rom[offset:offset + 2] == actual.to_bytes(2, 'big'), name
        restored[offset:offset + 2] = (addresses[name] - 0xE6E00).to_bytes(2, 'big')
    checksum, digest = PRE_LEVEL[kind]
    restored[0x18E:0x190] = bytes.fromhex(checksum)
    assert genesis_checksum(restored) == (int(checksum, 16),) * 2
    assert hashlib.sha256(restored).hexdigest() == digest, kind
    return restored
