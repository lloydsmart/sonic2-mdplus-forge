"""Audited selective object policy; binary inputs live only in pinned clones."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from .common import BuildError

FIXED_ROOT = 'Utility Project Files/Fixed Files/'


@dataclass(frozen=True)
class ObjectEntry:
    """Six-byte REV01 placement, including orientation and respawn flags."""

    raw: bytes

    @property
    def x(self) -> int:
        return int.from_bytes(self.raw[:2], 'big')

    @property
    def y(self) -> int:
        return int.from_bytes(self.raw[2:4], 'big') & 0xFFF

    @property
    def flags(self) -> int:
        return int.from_bytes(self.raw[2:4], 'big') >> 12

    @property
    def object_id(self) -> int:
        return self.raw[4] & 0x7F

    @property
    def subtype(self) -> int:
        return self.raw[5]


def parse_objects(data: bytes) -> tuple[ObjectEntry, ...]:
    # BINCLUDE supplies the separate terminator; these files contain entries only.
    if len(data) % 6:
        raise BuildError('Object layout must contain complete six-byte entries')
    entries = tuple(ObjectEntry(data[i:i + 6]) for i in range(0, len(data), 6))
    if any(a.x > b.x for a, b in zip(entries, entries[1:], strict=False)):
        raise BuildError('Object layout X coordinates are not sorted')
    return entries


# Shapes contain only (operation, pristine index, old count, new count).
# Indices refer to retail, so ARZ's rejected deletion cannot shift our insertion.
@dataclass(frozen=True)
class LevelPolicy:
    pristine_sha256: str
    reference_sha256: str
    target_sha256: str
    reference_shapes: tuple[tuple[str, int, int, int], ...]
    selected_shapes: tuple[tuple[str, int, int, int], ...]


EHZ_SHAPES = (
    ('insert', 29, 0, 1),  # Cave-entrance invisible wall.
    ('insert', 64, 0, 1),  # Sonic Jam wall/spring floor boundary.
    ('insert', 142, 0, 1),  # Sonic Jam corridor pathswapper.
)
ARZ_PATH_SHAPE = ('insert', 119, 0, 1)
WFZ_SHAPE = ('replace', 127, 1, 1)
LEVEL_POLICIES = {
    'level/objects/EHZ_2.bin': LevelPolicy(
        '7b3384fe361309fd2a36961116bf8d89c22399acb88fa7d632a467cc062c1560',
        'ba2b2db75688f309847a90172991f151e233d41c272fbd5eb3462f3650c00e5d',
        'ba2b2db75688f309847a90172991f151e233d41c272fbd5eb3462f3650c00e5d',
        EHZ_SHAPES, EHZ_SHAPES),
    'level/objects/ARZ_2.bin': LevelPolicy(
        '08f21b09e76d4920e5861d9cdc25329ee304ea69e3171d8551b5c5c729d82297',
        '2b52c83cdc3a87bf594292c9a2769c7d99595a04159231ed9879588d6d59f39e',
        '30fea857b2209a2b33f1befec90c446081356a8203f9e665874746bda0720ad2',
        (('delete', 33, 1, 0), ARZ_PATH_SHAPE), (ARZ_PATH_SHAPE,)),
    'level/objects/WFZ_1.bin': LevelPolicy(
        'b5afcb63c936ae62d860292a3ec4a7c4e7ff5cb24cf88130e4a6ae231bb737c4',
        '570e79e93a71296f69f91413b6f615de83c662ab3d6f9e31ff864cc001b9cbab',
        '570e79e93a71296f69f91413b6f615de83c662ab3d6f9e31ff864cc001b9cbab',
        (WFZ_SHAPE,), (WFZ_SHAPE,)),
}


def semantic_diff(pristine: bytes, reference: bytes) -> tuple:
    before = tuple(e.raw for e in parse_objects(pristine))
    after = tuple(e.raw for e in parse_objects(reference))
    return tuple((op, i, before[i:j], after[k:end])
                 for op, i, j, k, end in SequenceMatcher(
                     None, before, after, autojunk=False).get_opcodes() if op != 'equal')


def edit_shapes(edits: tuple) -> tuple[tuple[str, int, int, int], ...]:
    """Describe semantic edits without retaining any object-entry payload."""
    return tuple((op, index, len(old), len(new)) for op, index, old, new in edits)


def transform_layout(pristine: bytes, reference: bytes, name: str) -> bytes:
    policy = LEVEL_POLICIES.get(name)
    if policy is None:
        raise BuildError(f'Unselected level layout: {name}')
    for label, data, expected in (
        ('pristine', pristine, policy.pristine_sha256),
        ('reference', reference, policy.reference_sha256),
    ):
        if hashlib.sha256(data).hexdigest() != expected:
            raise BuildError(f'{name} {label} hash changed')
    reference_edits = semantic_diff(pristine, reference)
    if edit_shapes(reference_edits) != policy.reference_shapes:
        raise BuildError(f'{name} unexpected reference semantic differences')
    # Select whole derived edits only, in retail order. No payload is supplied by
    # Forge, and neither a duplicate selection nor an absent reference edit passes.
    selected_edits = tuple(edit for edit in reference_edits
                           if edit_shapes((edit,))[0] in policy.selected_shapes)
    if edit_shapes(selected_edits) != policy.selected_shapes:
        raise BuildError(f'{name} unexpected selected reference shapes')
    entries = [e.raw for e in parse_objects(pristine)]
    for _, index, old, new in reversed(selected_edits):
        if tuple(entries[index:index + len(old)]) != old:
            raise BuildError(f'{name} selected placement changed')
        entries[index:index + len(old)] = new
    target = b''.join(entries)
    if semantic_diff(pristine, target) != selected_edits:
        raise BuildError(f'{name} unexpected selected semantic differences')
    if hashlib.sha256(target).hexdigest() != policy.target_sha256:
        raise BuildError(f'{name} post-policy hash changed')
    return target


def prepare_layouts(work: Path) -> dict[str, bytes]:
    """Validate every reference and target before the caller writes any inputs."""
    return {name: transform_layout((work / name).read_bytes(),
                                   (work / (FIXED_ROOT + name)).read_bytes(), name)
            for name in LEVEL_POLICIES}
