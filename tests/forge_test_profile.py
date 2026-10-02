"""Select the ROM under test; default keeps the existing Production invocation."""
import os

from tools.mdplus_builder import modern
from tools.mdplus_builder.variants import BuildVariant

VARIANT = BuildVariant(os.environ.get('FORGE_TEST_VARIANT', 'production'))
LAYOUT = modern.LAYOUT_PROFILES[VARIANT]
PREPARED = VARIANT.prepared_dir
ROM = VARIANT.rom_path


def verify():
    return modern.verify_modern(ROM, strict_regression=True, variant=VARIANT)
