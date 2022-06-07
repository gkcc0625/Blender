import bpy
from .Logger import log
from .constants import BRD_CONST_DATA


def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


class BRD_Node_Localizer(bpy.types.Operator):
    bl_idname = "bradley.node_localize_used"
    bl_label = "Simple Node Operator"

    noodles = []

    def recursive_find(self, context):
        for n in context.node_tree.nodes:
            if hasattr(n, "node_tree"):
                self.noodles.append(n.node_tree.name)
                self.recursive_find(n)

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.tree_type == "GeometryNodeTree"
            and context.preferences.addons[__package__].preferences.experimental
        )

    def execute(self, context):

        tree = context.space_data
        self.recursive_find(tree)

        for i in self.noodles:
            bpy.data.node_groups[str(i)].make_local()
            bpy.data.node_groups[str(i)].use_fake_user = True

        log.debug(
            "Made Local :\n" + "\n".join(["- " + i for i in self.noodles]),
            multi_line=True,
        )

        self.noodles = []
        return {"FINISHED"}


class BRD_Node_Localizer_All(bpy.types.Operator):
    bl_idname = "bradley.node_localize_all"
    bl_label = "Simple Node Operator"

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.tree_type == "GeometryNodeTree"
            and context.preferences.addons[__package__].preferences.experimental
        )

    def execute(self, context):

        self.asd = flatten(
            [BRD_CONST_DATA.Custom_Category[i] for i in BRD_CONST_DATA.Custom_Category]
        )

        for i in self.asd:
            bpy.data.node_groups[str(i)].make_local()
            bpy.data.node_groups[str(i)].use_fake_user = True

        log.debug(
            "Made Local :\n" + "\n".join(["- " + i for i in self.asd]),
            multi_line=True,
        )

        return {"FINISHED"}


class BRD_PT_Localizer(bpy.types.Panel):
    bl_idname = "NODE_PT_BRD_PANEL"
    bl_label = "Localize"
    bl_region_type = "UI"
    bl_space_type = "NODE_EDITOR"
    bl_category = "Bradley"

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.tree_type == "GeometryNodeTree"
            and context.preferences.addons[__package__].preferences.experimental
        )

    def draw(self, context):
        if context.active_node is not None:
            layout = self.layout

            col = layout.column()
            col.operator(
                "bradley.node_localize_used", text="Localize Used Only", icon="SORT_ASC"
            )
            col.operator(
                "bradley.node_localize_all",
                text="Localize All Presets",
                icon="IMPORT",
            )
            col.scale_y = 3.0


panels_helper = [BRD_Node_Localizer, BRD_PT_Localizer, BRD_Node_Localizer_All]
