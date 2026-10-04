"""Fast negative policy tests without dependency checkouts or binary assets."""
from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace
from unittest.mock import patch

from tools.mdplus_builder.common import BuildError
from tools.mdplus_builder.level_data import LEVEL_POLICIES, LevelPolicy, parse_objects, transform_layout


class LevelDataPolicyTests(unittest.TestCase):
    def test_entry_coordinates_flags_id_and_subtype(self):
        # Artificial values exercise all decoded fields, including the ID mask.
        entry, = parse_objects(bytes.fromhex('0123a456de7f'))
        self.assertEqual((entry.x, entry.y, entry.flags, entry.object_id, entry.subtype),
                         (0x123, 0x456, 10, 0x5E, 0x7F))
        for data in (bytes(5), bytes.fromhex('000200005566000100005566')):
            with self.assertRaises(BuildError):
                parse_objects(data)

    def test_only_approved_files_are_selected(self):
        self.assertEqual(set(LEVEL_POLICIES), {
            'level/objects/EHZ_2.bin', 'level/objects/ARZ_2.bin', 'level/objects/WFZ_1.bin',
            'level/objects/CPZ_1.bin', 'level/objects/CPZ_2.bin', 'level/objects/DEZ_1.bin'})
        for name in ('OOZ_2', 'HTZ_1', 'MTZ_3'):
            with self.assertRaisesRegex(BuildError, 'Unselected'):
                transform_layout(b'', b'', f'level/objects/{name}.bin')
        with self.assertRaisesRegex(BuildError, 'Unselected'):
            transform_layout(b'', b'', 'level/rings/ARZ_2.bin')

    def test_hashes_semantic_diff_and_target_independently_fail_closed(self):
        name = 'level/objects/ARZ_2.bin'
        # Artificial sorted placements, unrelated to any retail game records.
        first, removed, middle, inserted, last = (
            bytes.fromhex(value) for value in (
                '00100101ee11', '00200202ee22', '00300303ee33',
                '00400404ee44', '00500505ee55'))
        pristine = first + removed + middle + last
        reference = first + middle + inserted + last
        target = first + removed + middle + inserted + last
        deletion, insertion = ('delete', 1, 1, 0), ('insert', 3, 0, 1)
        policy = LevelPolicy(
            *(hashlib.sha256(x).hexdigest() for x in (pristine, reference, target)),
            (deletion, insertion), (insertion,))
        with patch.dict(LEVEL_POLICIES, {name: policy}):
            self.assertEqual(transform_layout(pristine, reference, name), target)
            for data, ref, message in (
                (pristine + bytes(6), reference, 'pristine hash'),
                (pristine, reference + bytes(6), 'reference hash'),
            ):
                with self.assertRaisesRegex(BuildError, message):
                    transform_layout(data, ref, name)
        for field, value, message in (
            ('reference_shapes', (), 'reference semantic'),
            ('reference_shapes', (('delete', 1, 2, 0), insertion), 'reference semantic'),
            ('reference_shapes', (deletion, ('insert', 3, 0, 2)), 'reference semantic'),
            ('reference_shapes', (deletion, ('replace', 3, 0, 1)), 'reference semantic'),
            ('reference_shapes', (deletion, ('insert', 2, 0, 1)), 'reference semantic'),
            ('selected_shapes', (('insert', 0, 0, 1),), 'selected reference shapes'),
            ('selected_shapes', (insertion, insertion), 'selected reference shapes'),
            ('selected_shapes', (insertion, deletion), 'selected reference shapes'),
            ('target_sha256', '0' * 64, 'post-policy hash'),
        ):
            with (patch.dict(LEVEL_POLICIES, {name: replace(policy, **{field: value})}),
                  self.assertRaisesRegex(BuildError, message)):
                transform_layout(pristine, reference, name)
        # A valid but broader selection still fails the exact selective target hash.
        with (patch.dict(LEVEL_POLICIES, {name: replace(policy, selected_shapes=(deletion, insertion))}),
              self.assertRaisesRegex(BuildError, 'post-policy hash')):
            transform_layout(pristine, reference, name)

    def test_replacement_derives_payload_and_rejects_same_shape_payload_drift(self):
        # Artificial subtype replacement, with all values chosen for this test.
        name = 'level/objects/WFZ_1.bin'
        pristine = bytes.fromhex('01230234ee11')
        reference = bytes.fromhex('01230234ee22')
        changed = bytes.fromhex('01230234ee33')
        shape = (('replace', 0, 1, 1),)
        policy = LevelPolicy(
            *(hashlib.sha256(x).hexdigest() for x in (pristine, reference, reference)),
            shape, shape)
        with patch.dict(LEVEL_POLICIES, {name: policy}):
            self.assertEqual(transform_layout(pristine, reference, name), reference)
        # Even accepting a different reference hash cannot bypass the target lock.
        changed_policy = replace(policy, reference_sha256=hashlib.sha256(changed).hexdigest())
        with (patch.dict(LEVEL_POLICIES, {name: changed_policy}),
              self.assertRaisesRegex(BuildError, 'post-policy hash')):
            transform_layout(pristine, changed, name)


if __name__ == '__main__':
    unittest.main()
