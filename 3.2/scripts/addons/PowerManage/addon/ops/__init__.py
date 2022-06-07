import bpy
from . import refresh_list
from . import toggle_addon
from . import new_preset
from . import update_preset
from . import reload_preset
from . import remove_preset
from . import open_preferences
from . import backup

classes = (
    refresh_list.RefreshList,
    toggle_addon.ToggleAddon,
    new_preset.NewPreset,
    update_preset.UpdatePreset,
    reload_preset.ReloadPreset,
    remove_preset.RemovePreset,
    open_preferences.OpenPreferences,
    backup.BackupPreferences,
    backup.RestorePreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
