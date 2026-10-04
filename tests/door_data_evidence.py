"""Independent inverse binary audit against frozen released v3.0.1.

No forward policy/parser/transform imports and no placement payloads. Surviving
bytes move bijectively; each address operand is inverted from listing evidence.
The complete released digest checks every reconstructed byte, without masks.
"""
from __future__ import annotations

import hashlib
import json
import re

from tools.mdplus_builder.common import SOURCE_MODERN_DIR
from tools.mdplus_builder.source import _git_output, genesis_checksum

PIN = '380f37a731bfc720bb0371a35a593184a7ec5e43'
DOORS = {
    'CPZ_1': ((60, 136),
              '672c6b5ed672b889ad8629662f8e569fafca953046bfeeff999207bae17a4046',
              '79635ca9a52ca5052bcd2ad86bd9059d5815aadfe7391d170f2538442c47a66d'),
    'CPZ_2': ((42, 104, 154, 155),
              '316c884cb1a26233eb1c67682d679d8e0fa4a3d353f76b4ca740ae705507f61b',
              '0aeb9a4ef43f778976ea0c53493fbcc0df509c073d6291b28fa383e9a483a8a2'),
    'DEZ_1': ((0, 1, 3),
              '7418dacc85fae3b501637a3ff9bb93840f70f271916984530cdc03561c211492',
              '3d93d7b360bc05b417976d1d08f5aaa8f78f2fd69c492eef0ac22aa12d62e578'),
}
RELEASED = {
    'stock': ('53DB', 'ae378a1f8b41d9e804a0d05cb21f7951',
              '9ff0b7b577de237cf2fe9e13415a943b7d30e228a12b96b851793c95ece7184f'),
    'mdplus': ('C145', '50e81d88e257f8d14608e57801b628c5',
               'f33a1946a609b8045bb56ffce2aba05196190965fed6ddf5f8eb3b80c52a0c52'),
}
# Emitted intervals in the released listing. Gaps are exactly two stores and
# four explicit alignments ($20, $100, $200, $1000), never ignored ROM regions.
SPANS = ((0, 0x11910, 0), (0x11916, 0x1192A, -6),
         (0x11930, 0x50566, -12), (0x50580, 0xE4802, -32),
         (0xE4900, 0xE6CD8, -256), (0xE6E00, 0xEC382, -512),
         (0xED000, 0x200000, 0))
ALIGNMENTS = ((0x50566, 0x50580, -12, -32), (0xE4802, 0xE4900, -32, -256),
              (0xE6CD8, 0xE6E00, -256, -512), (0xEC382, 0xED000, -512, 0))
STORE = bytes.fromhex('117c00030028')  # MOVE.B #3,subtype(A0), not an object record.


def before(address):
    for start, end, delta in SPANS:
        if start + delta <= address < end + delta:
            return address - delta
    return address


def door_inputs():
    assert _git_output(SOURCE_MODERN_DIR, 'rev-parse', 'HEAD') == PIN
    result = {}
    for name, (indices, *hashes) in DOORS.items():
        blobs = [(SOURCE_MODERN_DIR / prefix / f'level/objects/{name}.bin').read_bytes()
                 for prefix in ('', 'Utility Project Files/Fixed Files')]
        for blob, digest in zip(blobs, hashes, strict=True):
            assert hashlib.sha256(blob).hexdigest() == digest, name
        retail, fixed = blobs
        assert len(retail) == len(fixed) and len(retail) % 6 == 0
        changed = tuple(i for i in range(len(retail) // 6)
                        if retail[i * 6:i * 6 + 6] != fixed[i * 6:i * 6 + 6])
        assert changed == indices
        assert tuple(i for i in range(len(retail) // 6) if retail[i * 6 + 4] & 127 == 0x2D) == indices
        for i in indices:
            a, b = retail[i * 6:i * 6 + 6], fixed[i * 6:i * 6 + 6]
            assert a[:5] == b[:5] and a[5] == 0 and b[5] == 2
        result[name] = retail, fixed
    return result


def emissions(listing, rom):
    """Read actual emitted bytes, joining AS continuation lines; exclude phased Z80."""
    pattern = re.compile(r'^.*?\b([0-9A-F]+) : ([0-9A-F ]+?) {2,}(.*)$')
    records = {}
    for line in listing.read_text().splitlines():
        match = pattern.match(line)
        if not match or not match[2].strip():
            continue
        address = int(match[1], 16)
        raw = bytes.fromhex(match[2].replace(' ', ''))
        text = match[3].strip().split(';')[0].strip()
        if rom[address:address + len(raw)] != raw:
            continue
        if not text and records:
            previous = next(reversed(records))
            data, source = records[previous]
            if previous + len(data) == address:
                records[previous] = data + raw, source
                continue
        records[address] = raw, text
    return records


def released_symbols(symbols, restored):
    result = {}
    for name, value in symbols.items():
        # Preserve the legacy parser's address-shaped listing artifacts too;
        # existing pre-door evidence hashes include them. These are not symbols.
        if re.fullmatch('[0-9A-F]+', name) and name[0].isdigit():
            address = int(name, 16)
            old_address = before(address)
            if old_address != address:
                name = f'{old_address:X}'
                value = int.from_bytes(restored[old_address:old_address + 2], 'big')
        elif name == 'paddingSoFar':
            value -= 12
        elif name not in ('used', 'PSG_Sample_Rate', 'MOMCPU', 'MDP_CTRL', 'MDP_CMD'):
            # Assembly constants and MD+ hardware registers are not ROM addresses.
            value = before(value)
        assert name not in result
        result[name] = value
    return result


def restore_v301(rom, symbols, listing, kind, report=None):
    """Reverse only doors, their two stores, and mathematically derived relocations."""
    assert len(rom) == 0x200000
    assert genesis_checksum(rom)[0] == genesis_checksum(rom)[1]
    restored = bytearray(len(rom))
    for start, end, delta in SPANS:
        restored[start:end] = rom[start + delta:end + delta]
    for start, end, left, right in ALIGNMENTS:
        assert not any(rom[start + left:end + right]), 'nonzero new alignment'
    for address in (0x11910, 0x1192A):
        restored[address:address + 6] = STORE
    fixups = []
    for address, (raw, text) in emissions(listing, rom).items():
        old_address = before(address)
        if ':' in text:
            text = text.split(':', 1)[1].strip()
        text = text.lstrip('-+ ').strip()
        words = text.split()
        opcode = words[0] if words else ''
        offsets = (range(0, len(raw) - 3, 4) if opcode == 'dc.l' else
                   [2] if opcode in ('jmp', 'jsr', 'lea', 'move.l', 'movea.l', 'cmpa.l', 'addi.l')
                   and len(raw) >= 6 else [])
        for offset in offsets:
            value = int.from_bytes(raw[offset:offset + 4], 'big')
            target = value & 0xFFFFFF
            old_value = (value & 0xFF000000) | before(target)
            tokens = re.findall(r'[A-Za-z_][\w.]*', re.sub(r'JmpTo\d*_', '', text))
            if old_value != value and any(t in symbols and before(symbols[t]) != symbols[t] for t in tokens):
                restored[old_address + offset:old_address + offset + 4] = old_value.to_bytes(4, 'big')
                fixups.append(('absolute', address + offset, old_address + offset, target, before(target), text))
        if opcode.lstrip('!') in ('bsr.w', 'bra.w', 'bpl.w') and len(raw) == 4:
            displacement = int.from_bytes(raw[2:4], 'big', signed=True)
            target = address + 2 + displacement
            previous = before(target) - (old_address + 2)
            if previous != displacement:
                restored[old_address + 2:old_address + 4] = previous.to_bytes(2, 'big', signed=True)
                fixups.append(('relative', address + 2, old_address + 2, target, before(target), text))
    # The two BNE.S branches skip the removed stores; no generic branch search.
    for address in (0x11902, 0x11916):
        assert rom[address:address + 2] == bytes.fromhex('660c')
        old_address = before(address)
        restored[old_address + 1] = before(address + 2 + rom[address + 1]) - (old_address + 2)
        fixups.append(('short_branch', address + 1, old_address + 1))
    # One relative word in the Obj2D dispatch table crosses the removed code.
    address = symbols['Obj2D_Index'] + 2
    assert int.from_bytes(rom[address:address + 2], 'big') == symbols['Obj2D_Main'] - symbols['Obj2D_Index']
    restored[address:address + 2] = (before(symbols['Obj2D_Main']) - before(symbols['Obj2D_Index'])).to_bytes(2, 'big')
    fixups.append(('index_word', address, address))
    for name, (retail, fixed) in door_inputs().items():
        address = symbols['Objects_' + name]
        assert rom[address:address + len(fixed)] == fixed
        restored[before(address):before(address) + len(retail)] = retail
    checksum, md5, digest = RELEASED[kind]
    restored[0x18E:0x190] = bytes.fromhex(checksum)
    assert genesis_checksum(restored) == (int(checksum, 16),) * 2
    assert hashlib.md5(restored, usedforsecurity=False).hexdigest() == md5
    assert hashlib.sha256(restored).hexdigest() == digest, kind
    old_symbols = released_symbols(symbols, restored)
    if report is not None:
        # Payload-free evidence: sites, expressions and movement, never object records.
        report.update(released_sha256=digest, candidate_sha256=hashlib.sha256(rom).hexdigest(),
                      changed_bytes=sum(a != b for a, b in zip(rom, restored, strict=True)),
                      fixups=fixups, spans=SPANS, alignments=ALIGNMENTS,
                      symbol_sha256=hashlib.sha256(json.dumps(old_symbols, sort_keys=True).encode()).hexdigest(),
                      symbols_before=old_symbols, symbols_after=symbols)
    return bytes(restored), old_symbols
