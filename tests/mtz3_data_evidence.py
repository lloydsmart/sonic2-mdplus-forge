"""Independent MTZ3 inverse to frozen v3.0.2; no forward policy or payloads.

Hash-checked dependency bytes supply deleted entries. Exact slice movement,
table operands, zero alignment and whole-ROM/symbol hashes cover every byte.
"""
from __future__ import annotations

import hashlib
import json

from tools.mdplus_builder.common import SOURCE_MODERN_DIR
from tools.mdplus_builder.source import _git_output, genesis_checksum

PIN = '380f37a731bfc720bb0371a35a593184a7ec5e43'
INDICES = (53, 100, 217, 230, 233)
HASHES = ('9d64fd5640ec834d4814ace9c7e87955316ad3ed95e1ba37a287e439bdaae157',
          'ab3f9ea828c0e781797beaba3570aab55df93838afeb6b51e6131bb660930372')
RELEASED = {
    'stock': ('9BE7', 'bd93d95a110be99e9eb9bafb3d31806f',
              '909e5f229fc4052f3c3c3c9a97c3a6b345117990796b0226dffbc98f88f00bc7',
              '514692484d32d23162906361ac0af5781a0b56399b35124f5476ed8062a78178'),
    'mdplus': ('0951', '5d3e5979d3f110d2761da3166b14b7cf',
               'e9f56f0efd72844918918f2efdecf6183f5bdabb47f235b61cc511a16942d3b5',
               'c86e5b487df0ca1e97dfd01187dbf6830e21a1f6bbcb2f5122db5b28ad5dea62'),
}
TABLE_ORDER = (
    'EHZ_1', 'EHZ_2', *(['Null'] * 6), 'MTZ_1', 'MTZ_2', 'MTZ_3', 'MTZ_3',
    'WFZ_1', 'WFZ_2', 'HTZ_1', 'HTZ_2', 'HPZ_1', 'HPZ_2', 'Null', 'Null',
    'OOZ_1', 'OOZ_2', 'MCZ_1', 'MCZ_2', 'CNZ_1', 'CNZ_2', 'CPZ_1', 'CPZ_2',
    'DEZ_1', 'DEZ_2', 'ARZ_1', 'ARZ_2', 'SCZ_1', 'SCZ_2',
)
MOVED = frozenset(TABLE_ORDER) - {'EHZ_1', 'EHZ_2', 'MTZ_1', 'MTZ_2', 'MTZ_3'}
START, NEW_END, OLD_END, LOADER = 0xE7D00, 0xEC164, 0xEC182, 0xED000
CATEGORIES = {'checksum': (0x18E, 0x190), 'table_words': (0xE6C00, 0xE6C44),
              'MTZ3_survivors': (START, 0xE8336), 'downstream': (0xE8336, NEW_END),
              'alignment': (NEW_END, OLD_END)}
COUNTS = {'checksum': 2, 'table_words': 30, 'MTZ3_survivors': 982,
          'downstream': 13865, 'alignment': 10}


def mtz3_inputs():
    assert _git_output(SOURCE_MODERN_DIR, 'rev-parse', 'HEAD') == PIN
    result = tuple((SOURCE_MODERN_DIR / prefix / 'level/objects/MTZ_3.bin').read_bytes()
                   for prefix in ('', 'Utility Project Files/Fixed Files'))
    for data, size, digest in zip(result, (1620, 1590), HASHES, strict=True):
        assert len(data) == size and hashlib.sha256(data).hexdigest() == digest
    retail, fixed = (tuple(data[i:i + 6] for i in range(0, len(data), 6)) for data in result)
    # Independent filtering, no difflib/parser/production transformation imports.
    assert fixed == tuple(record for i, record in enumerate(retail) if i not in INDICES)
    assert len(retail) == 270 and len(fixed) == 265
    for records in (retail, fixed):
        xs = tuple(int.from_bytes(r[:2], 'big') for r in records)
        assert xs == tuple(sorted(xs)) and max(xs) < 0xFFFF
    assert tuple(retail[i][4] for i in INDICES) == (0x36, 0x2D, 0x65, 0x31, 0x31)
    assert tuple(retail[i][5] for i in INDICES) == (0x40, 1, 0x13, 2, 2)
    assert tuple(int.from_bytes(retail[i][:2], 'big') for i in INDICES) == (
        0xA98, 0x1174, 0x1D20, 0x1F80, 0x2080)
    assert tuple(int.from_bytes(retail[i][2:4], 'big') for i in INDICES) == (
        0x258, 0x5E0, 0x56D, 0x5FC, 0x5FC)  # No orientation/respawn flags.
    return result


def restore_v302(rom, symbols, kind, report=None):
    """Invert MTZ3 only, requiring exact released ROM AND entire symbol identity."""
    assert len(rom) == 0x200000
    assert genesis_checksum(rom)[0] == genesis_checksum(rom)[1]
    assert symbols.get('Objects_MTZ_3') == START
    assert symbols['Objects_WFZ_1'] == 0xE833C
    assert symbols['Objects_Null'] == 0xEC14C
    assert symbols['Off_Objects'] == 0xE6C00 and symbols['SoundDriverLoad'] == LOADER
    retail, fixed = mtz3_inputs()
    assert rom[START:START + len(fixed)] == fixed
    assert not any(rom[NEW_END:LOADER]), 'nonzero candidate alignment'
    restored = bytearray(rom)
    # Preserve the post-MTZ boundary and every downstream byte, including the
    # trailing unused object boundary data. No regeneration of unrelated layouts.
    restored[START:START + len(retail)] = retail
    restored[START + len(retail):OLD_END] = rom[START + len(fixed):NEW_END]
    restored[OLD_END:LOADER] = bytes(LOADER - OLD_END)
    old = dict(symbols)
    for name in MOVED:
        old['Objects_' + name] += 30
    old['paddingSoFar'] -= 30
    fixups = []
    for index, name in enumerate(TABLE_ORDER):
        address = 0xE6C00 + index * 2
        current = symbols['Objects_' + name] - 0xE6C00
        previous = old['Objects_' + name] - 0xE6C00
        assert rom[address:address + 2] == current.to_bytes(2, 'big'), name
        restored[address:address + 2] = previous.to_bytes(2, 'big')
        if previous != current:
            fixups.append((address, name, current, previous))
    checksum, md5, digest, symbol_digest = RELEASED[kind]
    restored[0x18E:0x190] = bytes.fromhex(checksum)
    assert genesis_checksum(restored) == (int(checksum, 16),) * 2
    assert hashlib.md5(restored, usedforsecurity=False).hexdigest() == md5
    assert hashlib.sha256(restored).hexdigest() == digest, kind
    assert hashlib.sha256(json.dumps(old, sort_keys=True).encode()).hexdigest() == symbol_digest
    counts = {name: sum(a != b for a, b in zip(rom[start:end], restored[start:end], strict=True))
              for name, (start, end) in CATEGORIES.items()}
    assert counts == COUNTS
    assert sum(counts.values()) == sum(a != b for a, b in zip(rom, restored, strict=True)) == 14889
    if report is not None:
        report.update(candidate_sha256=hashlib.sha256(rom).hexdigest(), released_sha256=digest,
                      changed_bytes=14889, categories=CATEGORIES, counts=counts, fixups=fixups,
                      movements={name: (old[name], value, value - old[name])
                                 for name, value in symbols.items() if old[name] != value},
                      symbols_before=old, symbols_after=symbols)
    return bytes(restored), old
