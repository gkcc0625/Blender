# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy, rna_keymap_ui

from bpy.types import UILayout, KeyConfig, KeyMap, KeyMapItem

from dataclasses import dataclass

from typing import Any, List, Tuple

@dataclass
class KeyEntry:
    operator: str
    operator_params: List[Tuple[str, Any]]
    type: str
    value: str = 'PRESS'
    shift: bool = False
    ctrl: bool = False
    alt: bool = False
    oskey: bool = False


class KeyRegistry:
    """
    Manages all things around hot-key bindings.
    """
    def __init__(self):
        self.__keys = [] # type: List[Tuple[str, KeyConfig, KeyMap, KeyMapItem]]


    def add_key(self, title: str, keymap_name: str, space_type: str, entries: List[KeyEntry]):
        key_config = bpy.context.window_manager.keyconfigs.addon
        if key_config:
            key_map = key_config.keymaps.new(name=keymap_name, space_type=space_type)
            if key_map:
                for e in entries:
                    key_map_item = key_map.keymap_items.new(
                        e.operator, 
                        type=e.type, 
                        value=e.value, 
                        shift=e.shift, 
                        ctrl=e.ctrl, 
                        alt=e.alt, 
                        oskey=e.oskey 
                    )
                    if key_map_item:
                        for n, v in e.operator_params:
                            setattr(key_map_item.properties, n, v)
                        self.__keys.append((key_config, key_map, key_map_item, title, e.operator_params))


    def dispose(self):
        for _, km, kmi, *_ in self.__keys:
            km.keymap_items.remove(kmi)
        self.__keys.clear()


    def keys(self) -> List[Tuple[str, KeyConfig, KeyMap, KeyMapItem]]:
        return self.__keys


    def render_prefs(self, l: UILayout):
        """
        Draw config in prefs.
        """
        # We have to find the correct entries in the real blender config,
        # than they were stored and correct after blender restart.
        keyconfig = bpy.context.window_manager.keyconfigs.user
        for _, km, ki, title, params in KeyRegistry.instance().keys():
            # Keymap by name.
            keymap = keyconfig.keymaps.get(km.name)
            if keymap and keymap.space_type == km.space_type:
                # Loop over all entries in this map.
                for keymap_item in keymap.keymap_items:
                    # Check if this key calls our searched operator.
                    if keymap_item.idname == ki.idname:
                        # As different keys may call the same operator, we have 
                        # to check for all operator properties as well.
                        failed = False
                        p: Tuple[str, Any]
                        for p in params:
                            if getattr(keymap_item.properties, p[0]) != p[1]:
                                failed = True
                                break

                        # If failed is false, all params match, this must be out key, render it.
                        if not failed:
                            sr = l.row(align=True)
                            sr.label(text=f'{title}:')
                            rna_keymap_ui.draw_kmi(['ADDON', 'USER', 'DEFAULT'], keyconfig, keymap, keymap_item, sr, 0)
                            break


    @staticmethod
    def instance() -> 'KeyRegistry':
        """
        Access as singleton.
        """
        global _key_instance
        return _key_instance


_key_instance = KeyRegistry()
