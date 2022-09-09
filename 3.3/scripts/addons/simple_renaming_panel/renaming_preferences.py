import bpy
import rna_keymap_ui
from bpy.props import (
    EnumProperty,
    StringProperty,
)

from . import addon_updater_ops
from .renaming_panels import VIEW3D_PT_tools_renaming_panel, VIEW3D_PT_tools_type_suffix
from .renaming_vallidate import VIEW3D_PT_vallidation
from .renaming_keymap import get_hotkey_entry_item

def update_panel_category(self, context):
    is_panel = hasattr(bpy.types, 'VIEW3D_PT_tools_renaming_panel')
    if is_panel:
        try:
            bpy.utils.unregister_class(VIEW3D_PT_tools_renaming_panel)
        except:
            pass

    is_panel = hasattr(bpy.types, 'VIEW3D_PT_tools_type_suffix')
    VIEW3D_PT_tools_renaming_panel.bl_category = context.preferences.addons[__package__].preferences.renaming_category
    bpy.utils.register_class(VIEW3D_PT_tools_renaming_panel)

    if is_panel:
        try:
            bpy.utils.unregister_class(VIEW3D_PT_tools_type_suffix)
        except:
            pass
    VIEW3D_PT_tools_type_suffix.bl_category = context.preferences.addons[__package__].preferences.renaming_category
    bpy.utils.register_class(VIEW3D_PT_tools_type_suffix)
    return


def update_panel_category_vallidation(self, context):
    is_panel = hasattr(bpy.types, 'VIEW3D_PT_vallidation')

    if is_panel:
        try:
            bpy.utils.unregister_class(VIEW3D_PT_vallidation)
        except:
            pass

    VIEW3D_PT_vallidation.bl_category = context.preferences.addons[__package__].preferences.vallidation_category
    bpy.utils.register_class(VIEW3D_PT_vallidation)
    return


def toggle_validation_panel(self, context):
    if self.renaming_show_validation:
        bpy.utils.register_class(VIEW3D_PT_vallidation)
    else:
        bpy.utils.unregister_class(VIEW3D_PT_vallidation)
    return


# addon Preferences
class VIEW3D_OT_renaming_preferences(bpy.types.AddonPreferences):
    """Contains the blender addon preferences"""
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__  ### __package__ works on multifile and __name__ not

    # prefs_tabs: EnumProperty(items=(('ui', "UI", "UI"), ('keymaps', "Keymaps", "Keymaps"),
    #                                ('validate', "Validate (experimental)", "Validate (experimental)")), default='ui')

    prefs_tabs: EnumProperty(items=(('ui', "UI", "UI"), ('keymaps', "Keymaps", "Keymaps")), default='ui')

    renaming_category: StringProperty(name="Category",
                                      description="Defines in which category of the tools panel the simple renaimg panel is listed",
                                      default='Rename', update=update_panel_category)

    renaming_separator: StringProperty(
        name="Separator",
        description="Defines the separator between different operations",
        default='_',
    )

    renamingPanel_advancedMode: bpy.props.BoolProperty(
        name="Advanced UI",
        description="Enable or Disable Advanced Mode",
        default=True,
    )

    renamingPanel_showPopup: bpy.props.BoolProperty(
        name="Show Popup",
        description="Enable or Disable Popup",
        default=True,
    )
    numerate_start_number: bpy.props.IntProperty(
        name="Numerate Start",
        description="Defines the first number for iterating objects. E.g., 1 means that the first object will be named [objectname]001",
        default=1,
    )

    numerate_digits: bpy.props.IntProperty(
        name="Digits",
        description="Defines digits used for numerating. Number 1 with digits 3 would result in 001",
        default=3,
    )
    numerate_step: bpy.props.IntProperty(
        name="Numerate Step",
        description="Defines the steps between numbers. E.g., 1 results in 1, 2, 3, a step siye ot two results in 1,3,5",
        default=1,
    )

    renaming_stringHigh: StringProperty(
        name="High",
        description="",
        default="high",
        # update = update_panel_position,
    )
    renaming_stringLow: StringProperty(
        name="Low",
        description="",
        default='low',
        # update = update_panel_position,
    )
    renaming_stringCage: StringProperty(
        name="Cage",
        description="",
        default='cage',
        # update = update_panel_position,
    )
    renaming_user1: StringProperty(
        name="User 1",
        description="",
        default='',
        # update = update_panel_position,
    )
    renaming_user2: StringProperty(
        name="User 2",
        description="",
        default='',
        # update = update_panel_position,
    )
    renaming_user3: StringProperty(
        name="User 3",
        description="",
        default='',
        # update = update_panel_position,
    )

    renaming_show_validation: bpy.props.BoolProperty(
        name="Use Validation Panel",
        description="Enable or Disable Validation Panel",
        default=False,
        update=toggle_validation_panel)

    vallidation_category: StringProperty(name="Category",
                                         description="Defines in which category of the tools panel the simple renaimg vallidation panel is listed",
                                         default='Rename',
                                         update=update_panel_category_vallidation)  # update = update_panel_position,

    regex_Mesh: bpy.props.StringProperty(
        name="Naming Regex",
        description="",
        default='r"^[A-Za-z]{2}_[A-Za-z]{6}_[A-Za-z0-9]+(_[A-Za-z0-9]+)?$"',
    )

    assetRegex: bpy.props.StringProperty(
        name="Asset Regex",
        description="",
        default='r"^[A-Za-z]+(_[A-Za-z0-9]+)?$"',
    )
    materialRegex: bpy.props.StringProperty(
        name="Material Regex",
        description="",
        default='r"^[A-Za-z](_mat|_main_mat)?$"',
    )
    genericMaterialRegex: bpy.props.StringProperty(
        name="Generic Material Regex",
        description="",
        default='r"^Gen[A-Za-z]+_mat"',
    )

    socketPrefix: bpy.props.StringProperty(
        name="Socket Prefix",
        description="",
        default="SOCKET_",
    )

    # addon updater preferences

    auto_check_update: bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False,
    )
    updater_intrval_months: bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_intrval_days: bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
        max=31
    )
    updater_intrval_hours: bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_intrval_minutes: bpy.props.IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )

    def draw(self, context):
        '''
        simple preference UI to define custom inputs and user preferences
        '''
        layout = self.layout
        wm = context.window_manager

        row = layout.row(align=True)
        row.prop(self, "prefs_tabs", expand=True)

        if self.prefs_tabs == 'ui':
            row = layout.row()
            row.prop(self, "renaming_category", expand=True)
            row = layout.row()
            row.prop(self, "renamingPanel_showPopup")
            row = layout.row()
            row.prop(self, "renamingPanel_advancedMode")

            row = layout.row()
            row.prop(self, "renaming_separator")
            row = layout.row()
            row.prop(self, "numerate_start_number")
            row = layout.row()
            row.prop(self, "numerate_digits")
            row = layout.row()
            row.prop(self, "numerate_step")

            box = layout.box()
            row = box.row()
            row.prop(self, "renaming_stringLow")
            row = box.row()
            row.prop(self, "renaming_stringHigh")
            row = box.row()
            row.prop(self, "renaming_stringCage")
            row = box.row()
            row.prop(self, "renaming_user1")
            row = box.row()
            row.prop(self, "renaming_user2")
            row = box.row()
            row.prop(self, "renaming_user3")

        if self.prefs_tabs == 'keymaps':
            box = layout.box()
            col = box.column()

            wm = context.window_manager
            kc = wm.keyconfigs.addon
            km = kc.keymaps['3D View']

            kmis = []
            # Menus and Pies
            kmis.append(get_hotkey_entry_item(km, 'wm.call_panel', 'VIEW3D_PT_tools_renaming_panel'))
            kmis.append(get_hotkey_entry_item(km, 'wm.call_panel', 'VIEW3D_PT_tools_type_suffix'))

            for kmi in kmis:
                if kmi:
                    col.context_pointer_set("keymap", km)
                    rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

                else:
                    col.label(text="No hotkey entry found")
                    col.operator("renaming.add_hotkey", text="Add hotkey entry", icon='ADD')



        if self.prefs_tabs == 'validate':
            box = layout.box()
            row = box.row()
            row.prop(self, "renaming_show_validation", expand=True)
            row = box.row()
            row.prop(self, "vallidation_category", expand=True)
            row = box.row()
            row.prop(self, "regex_Mesh", expand=True)
            row = box.row()
            row.prop(self, "assetRegex", expand=True)
            row = box.row()
            row.prop(self, "materialRegex", expand=True)
            row = box.row()
            row.prop(self, "genericMaterialRegex", expand=True)

        addon_updater_ops.update_settings_ui(self, context)


classes = (
    VIEW3D_OT_renaming_preferences,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
