# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

bl_info = {
    'name' : 'Asset Wizard Pro',
    "version": (1, 2, 0),
    'author' : 'h0bB1T',
    'description' : 'Smart Assets Tools',
    'blender' : (3, 0, 0),
    'location' : 'View3D|NodeEditor > Panel',
    'category' : 'Export',
    'doc_url' : 'https://wp.h0bb1t.de/index.php/asset-wizard-pro-manual/',
}

import bpy, os

from .constants import config_dir, dev_config
from .registries.config_registry import ConfigRegistry
from .registries.key_registry import KeyRegistry, KeyEntry
from .registries.icons_registry import IconsRegistry
from .utils.io import read_json
from .utils.dev import Measure
from .awp.ui import asset_browser_header

from .preferences import PreferencesPanel
from .properties import Properties, PropertySection, TagProperty

from .menus.register import register_menus
from .operators.register import register_operators
from .panels.register import register_panels


ops = [
    TagProperty,
    PropertySection,
    Properties,
    PreferencesPanel,

    *register_menus,
    *register_operators,
    *register_panels,
]


def register():
    with Measure('Initialize Asset Wizard Pro'):
        # Register and setup Blender stuff.
        for op in ops:
            bpy.utils.register_class(op)

        # Create config dir.
        os.makedirs(config_dir, exist_ok=True)

        IconsRegistry.instance()

        # Eventually create default config and load current.
        ConfigRegistry.get().init_default()
        ConfigRegistry.get().read()

        # Eventually load config in dev env.
        if os.path.exists(dev_config):
            js = read_json(dev_config)
            PreferencesPanel.get().author = js.get('author', '')
            PreferencesPanel.get().auto_place = js.get('auto_place', False)
            PreferencesPanel.get().render_engine = js.get('engine', 'CYCLES')
            PreferencesPanel.get().cycles_samples = js.get('samples', 20)
            PreferencesPanel.get().dimension = js.get('dimension', 256)

        # Initialize several things.
        Properties.initialize()
        PreferencesPanel.get().transfer_defaults()

        # Add menu to Asset Browser header.
        bpy.types.FILEBROWSER_HT_header.append(asset_browser_header)

        # Bound keys to pies.
        KeyRegistry.instance().add_key('Pie Menus', 'Node Editor', 'NODE_EDITOR', [ KeyEntry('awp.invoke_pie', [], 'D') ])
        KeyRegistry.instance().add_key('Placer', 'Object Mode', 'EMPTY',  [ KeyEntry('awp.multi_purpose', [ ( 'mode', 'invoke_place' ), ], 'E') ])    
        KeyRegistry.instance().add_key('Replacer', 'Object Mode', 'EMPTY',  [ KeyEntry('awp.multi_purpose', [ ( 'mode', 'invoke_replace' ), ], 'E', shift=True) ])    


def unregister():
    with Measure('Dispose Asset Wizard Pro'):
        KeyRegistry.instance().dispose()

        # Cleanup addon.
        bpy.types.FILEBROWSER_HT_header.remove(asset_browser_header)

        Properties.dispose()

        for op in reversed(ops):
            bpy.utils.unregister_class(op) 


if __name__ == "__main__":
    register()    
