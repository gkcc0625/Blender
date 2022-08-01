import bpy
from pathlib import Path, PurePath
from bpy.app.handlers import persistent
import bpy.utils.previews
import json

# local modules
from .Custom_Category import (
    NODE_OT_Add,
    NODE_MT_GEO,
    add_button,
    geo_cat_generator,
)
from .Preset import preset_help
from .constants import BRD_CONST_DATA
from .utils import flatten

# from .Localizer import panels_helper
from . import Panels

bl_info = {
    "name": "Bradley's Geo Node Presets",
    "description": "This is a geometry node preset made by Bradley's animation, and possibly ferret",
    "author": "Possibly Ferret | Bradley",
    "version": (0, 0, 2),
    "blender": (3, 0, 0),
    "location": "GeometryNode",
    "support": "COMMUNITY",
    "category": "Node",
    "warning": "Restart Blender after disabling/uninstalling",
}

#### Variables ####

BRD_preview_collections = {}
BRD_SESSION = True

##################


def updater(self, context):
    print(self.debugging)
    with open(BRD_CONST_DATA.Folder / "settings.json", "r") as f:
        stuff = json.load(f)

        stuff["__DYN__"]["Debug"] = self.debugging
        with open(BRD_CONST_DATA.Folder / "settings.json", "w") as f:
            f.write(json.dumps(stuff))


class BRD_Preference(bpy.types.AddonPreferences):
    bl_idname = __name__

    ui_tab: bpy.props.EnumProperty(
        name="Preferences Tab",
        items=[
            ("Socials", "Socials", ""),
            ("Settings", "Settings", ""),
        ],
        default="Socials",
    )

    debugging: bpy.props.BoolProperty(update=updater, default=False)

    experimental: bpy.props.BoolProperty(default=False)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "ui_tab", expand=True)
        box = layout.box()

        if self.ui_tab == "Socials":
            col = box.column()

            for i in BRD_CONST_DATA.Socials:

                op = col.operator(
                    "wm.url_open",
                    text=i.Name,
                    emboss=True,
                    depress=False,
                    icon_value=BRD_preview_collections["Social_icons"][i.Name].icon_id,
                )
                op.url = i.Url

        elif self.ui_tab == "Settings":

            col = box.column()
            row = col.row()
            row.operator(
                "bradley.folder",
                text="Open Folder of Presets File ",
                icon="FILE_FOLDER",
            )

            row = col.row()

            row.operator("bradley.force_update", text="Force Update Presets")

            row = col.row()
            row.prop(self, "debugging", toggle=True)
            row.prop(self, "experimental", toggle=True)


####################################


@persistent
def run_after_load(*dummy):
    global BRD_SESSION

    if BRD_SESSION:
        bpy.ops.bradley.update()

    if any("preset.blend" in a for a in [i.name for i in bpy.data.libraries]):

        bpy.ops.wm.lib_relocate(
            library=[
                s for s in [i.name for i in bpy.data.libraries] if "preset.blend" in s
            ][0],
            directory=str(
                Path(
                    PurePath(
                        BRD_CONST_DATA.Folder,
                        BRD_CONST_DATA.__DYN__.B_Version,
                    )
                ).resolve()
            ),
            filename="preset.blend",
        )

    bpy.ops.bradley.link()

    if BRD_SESSION:
        geo_cat_generator()
        BRD_SESSION = False


classes = flatten(
    [
        BRD_Preference,
        NODE_OT_Add,
    ]
    + preset_help
    + Panels.panels
)


def register():
    print("=" * 20)
    print(__package__)
    print("=" * 20)
    pcoll = bpy.utils.previews.new()
    icon_dir = PurePath(Path(__file__).parents[0], "icons")

    for i in BRD_CONST_DATA.Socials:
        pcoll.load(i.Name, str(PurePath(icon_dir, i.Icon)), "IMAGE")

    BRD_preview_collections["Social_icons"] = pcoll

    if not hasattr(bpy.types, "NODE_MT_GEO"):
        bpy.utils.register_class(NODE_MT_GEO)
        bpy.types.NODE_MT_add.append(add_button)

    for i in classes:
        bpy.utils.register_class(i)

    bpy.app.handlers.load_post.append(run_after_load)


def unregister():
    if hasattr(bpy.types, "NODE_MT_GEO"):
        bpy.types.NODE_MT_add.remove(add_button)
    for i in classes:
        bpy.utils.unregister_class(i)


if __name__ == "__main__":
    register()
