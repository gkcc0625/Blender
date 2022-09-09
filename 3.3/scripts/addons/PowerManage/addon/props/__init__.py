import bpy
from . import category
from . import addon
from . import preset
from . import prefs
from . import meta

classes = (
    category.Category,
    addon.Addon,
    preset.Preset,
    prefs.Prefs,
    meta.Meta,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.types.WindowManager
    wm.powermanage = bpy.props.PointerProperty(type=meta.Meta)


def unregister():
    del bpy.types.WindowManager.powermanage

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
