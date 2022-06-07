import bpy
from . import menus
from . import lists
from . import panels

classes = (
    menus.PresetMenu,
    lists.AddonList,
    panels.MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
