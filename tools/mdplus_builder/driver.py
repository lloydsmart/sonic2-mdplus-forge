"""Check the compressed Z80 driver against what the 68000 loader actually loads."""
from __future__ import annotations

from .common import BuildError

# SUBQ.W #1,D7 / BCS.S exit / MOVE.B (A6)+,D0 / RTS / ADDQ.W #4,SP / RTS.
# Unlike the stock loader, this processes the final byte before returning.
LOADER_READ = bytes.fromhex('5347 6504 101e 4e75 584f 4e75')


def saxman_decode(data: bytes, *, stock_loader: bool = False) -> bytes:
    """Decode bounded Saxman data; optionally reproduce the stock loader's EOF bug."""
    position = 0
    output = bytearray()

    def read() -> int:
        nonlocal position
        if position >= len(data):
            raise EOFError
        value = data[position]
        position += 1
        if stock_loader and position == len(data):
            raise EOFError
        return value

    try:
        while True:
            descriptor = read()
            for bit in range(8):
                if descriptor & (1 << bit):
                    output.append(read())
                else:
                    low, high = read(), read()
                    offset = ((low | ((high & 0xF0) << 4)) + 0x12) & 0xFFF
                    offset |= len(output) & ~0xFFF
                    if offset > len(output):
                        offset -= 0x1000
                    if offset < 0:
                        output.extend(bytes((high & 15) + 3))
                        continue
                    for _ in range((high & 15) + 3):
                        if offset >= len(output):
                            raise BuildError('Saxman reference is outside loaded driver')
                        output.append(output[offset])
                        offset += 1
                if len(output) > 0x10000:
                    raise BuildError('Saxman output exceeds Z80 address space')
    except EOFError:
        return bytes(output)
