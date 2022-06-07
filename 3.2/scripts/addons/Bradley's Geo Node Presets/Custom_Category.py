import bpy
import json
from pathlib import Path, PurePath
import bpy.utils.previews
import re
from bpy.props import StringProperty

from .Logger import log
from .constants import BRD_CONST_DATA


def add_button(self, context):
    if context.area.ui_type == "GeometryNodeTree":
        self.layout.menu(
            "NODE_MT_GEO", text="Bradley's preset", icon="KEYTYPE_JITTER_VEC"
        )


def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def geo_cat_generator():
    log.debug("Generating Custom category")

    BRD_GRP_Cache = BRD_CONST_DATA.Custom_Category

    known_groups = flatten([BRD_GRP_Cache[i] for i in BRD_GRP_Cache])

    with bpy.data.libraries.load(
        str(
            PurePath(
                BRD_CONST_DATA.Folder, BRD_CONST_DATA.__DYN__.B_Version, "preset.blend"
            )
        )
    ) as (
        data_from,
        __,
    ):
        kiki = []

        for i in data_from.node_groups:
            if i.startswith("G_"):
                kiki.append(i)

        if _ap := list(set(kiki) - set(known_groups)):
            BRD_GRP_Cache["Unknown"] = _ap
            log.debug("uncategorised groups :" + "\n".join(["- " + i for i in _ap]))

    log.debug(
        "Node category :\n" + str(json.dumps(BRD_GRP_Cache, indent=2)),
        multi_line=True,
    )

    for item in BRD_GRP_Cache.items():

        def custom_draw(self, context):
            layout = self.layout

            for group_name in BRD_GRP_Cache[self.bl_label]:
                props = layout.operator(
                    NODE_OT_Add.bl_idname,
                    text=re.sub(r".*?_", "", group_name),
                )
                props.group_name = group_name

        menu_type = type(
            "NODE_MT_category_" + item[0],
            (bpy.types.Menu,),
            {
                "bl_idname": "NODE_MT_category_" + "_BRD_" + item[0].replace(" ", "_"),
                "bl_space_type": "NODE_EDITOR",
                "bl_label": item[0],
                "draw": custom_draw,
            },
        )

        def generate_menu_draw(name, label):
            def draw_menu(self, context):
                self.layout.menu(name, text=label)

            return draw_menu

        bpy.utils.register_class(menu_type)
        bpy.types.NODE_MT_GEO.append(
            generate_menu_draw(menu_type.bl_idname, menu_type.bl_label),
        )


class NODE_MT_GEO(bpy.types.Menu):
    bl_label = "bradley Preset"
    bl_idname = "NODE_MT_GEO"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "GeometryNodeTree"

    def draw(self, context):
        pass


class NODE_OT_Add(bpy.types.Operator):
    bl_idname = "bradley.bradley_node_ot_add"
    bl_label = "Add node group"
    bl_options = {"REGISTER", "UNDO"}

    group_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.space_data.node_tree

    def execute(self, context):
        bpy.ops.node.add_node(type="GeometryNodeGroup")

        node = context.selected_nodes[0]
        node.node_tree = bpy.data.node_groups[self.group_name]
        bpy.ops.transform.translate("INVOKE_DEFAULT")

        return {"FINISHED"}
