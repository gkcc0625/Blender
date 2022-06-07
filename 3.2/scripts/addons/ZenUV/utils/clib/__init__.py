
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.utils import register_class, unregister_class
# from ZenUV.prop.zuv_preferences import get_prefs
from shutil import copy
import os
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from ZenUV.utils.clib.lib_init import register_library, unregister_library, get_zenlib_name, is_zenlib_present
from ZenUV.ui.labels import ZuvLabels


class ZUVLibrary_OT_InstallFile(Operator, ImportHelper):
    bl_idname = "view3d.zenuv_install_library"
    bl_label = "Add " + ZuvLabels.CLIB_NAME
    bl_description = "Install Zen UV Dynamic Library"

    def extention():
        filename, file_extension = os.path.splitext(get_zenlib_name())
        return file_extension

    filter_glob: StringProperty(
        default="*{}".format(extention()),
        options={'HIDDEN'}
    )

    def execute(self, context):
        # addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        if is_zenlib_present():
            # addon_prefs.zen_lib = True
            self.report({"INFO"}, ZuvLabels.CLIB_NAME + " is already installed. Trying to activate...")
            register_library()
        else:
            path = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + get_zenlib_name()
            # Copy Library to
            copy(self.filepath, path)
            print("Zen UV: File ", self.filepath)
            print("          Copied to: ", path)
            if is_zenlib_present():
                # addon_prefs.zen_lib = True
                register_library()
                self.report({"INFO"}, ZuvLabels.CLIB_NAME + " was installed!")
            else:
                self.report({"ERROR"}, "For some reason, the library cannot be installed. Try to do it manually")
        return {'FINISHED'}


class ZUVLibrary_OT_Check(Operator):
    bl_idname = "view3d.zenuv_check_library"
    bl_label = "Check Library"
    bl_description = "Check Zen UV Dynamic Library"

    def execute(self, context):
        # addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        if is_zenlib_present():
            # addon_prefs.zen_lib = True
            self.report({"INFO"}, "The library is already installed.  Trying to activate...")
            register_library()
        else:
            self.report({"WARNING"}, "The library is not found. First, install in the Zen UV settings.")
        return {'FINISHED'}


# bpy.ops.preferences.addon_install(overwrite=True, target='DEFAULT', filepath="", filter_folder=True, filter_python=True, filter_glob="*.py;*.zip")

class ZUV_OT_Update(Operator, ImportHelper):
    bl_idname = "uv.zenuv_update_addon"
    bl_label = "Update Zen UV"
    bl_description = "Update Zen UV add-on"

    # filename_ext = ".zip"
    use_filter = True
    filter_glob: StringProperty(
        default="*.zip",
        options={'HIDDEN'}
    )

    def execute(self, context):
        unregister_library()
        bpy.ops.preferences.addon_install(
            overwrite=True,
            target='DEFAULT',
            filepath=self.filepath,
            filter_folder=True,
            filter_python=True,
            filter_glob="*.py;*.zip"
        )

        return {'FINISHED'}


class ZUVLibrary_OT_Unregister(Operator):
    bl_idname = "uv.zenuv_unregister_library"
    bl_label = "Unregister Zen UV Core"
    bl_description = "Unregister Zen UV Core Library"

    def execute(self, context):
        unregister_library()

        return {'FINISHED'}


classes = (
    ZUVLibrary_OT_InstallFile,
    ZUVLibrary_OT_Check,
    ZUVLibrary_OT_Unregister,
    ZUV_OT_Update
)


def register():
    for cl in classes:
        register_class(cl)

    register_library()


def unregister():

    for cl in classes:
        unregister_class(cl)

    unregister_library()


if __name__ == "__main__":
    pass
