import bpy


class VIEW3D_OT_ke_solo_cutter(bpy.types.Operator):
    bl_idname = "view3d.ke_solo_cutter"
    bl_label = "Solo Cutter"
    bl_description = "Toggle for currently selected 'cutter' (any boolean type) object,\n" \
                     "hiding other modifiers in the viewport"
    bl_options = {'REGISTER', 'UNDO'}

    mode : bpy.props.EnumProperty(
        items=[("ALL", "", "", 1),
               ("PRE", "", "", 2)],
        name="Combo", options={"HIDDEN"},
        default="ALL")

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):

        # SELECTION CHECKS
        cat = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'HAIR', 'GPENCIL'}
        active = context.active_object
        if active is None:
            active = context.object

        if active.type not in cat:
            self.report({"INFO"}, "Invalid object type selected?")
            return {"CANCELLED"}

        cat_objects = [o for o in context.scene.objects if o.type in cat]

        # CHECK IF SOLO IS ON - (slow due to show_viewport - no faster solution idk)
        if active.children:
            unsolo = False

            for o in active.children:
                if o.name == "[ Solo ]":
                    bpy.data.objects.remove(object=o, do_unlink=True)
                    unsolo = True
                    break

            if unsolo:
                del active["ke_solo_cutter"]

                for obj in cat_objects:
                    keys = []
                    for k in obj.keys():
                        if "ks_cutter" in k:
                            obj.modifiers[obj[k]].show_viewport = True
                            keys.append(k)
                    if keys:
                        for k in keys:
                            del obj[k]

                return {"FINISHED"}

        # ELSE, SET SOLO
        tot_ouc = 0

        for obj in cat_objects:

            objects_using_cutter = []

            for m in obj.modifiers:
                if m.type == "BOOLEAN" and m.object == active:
                    objects_using_cutter.append(obj)
                    tot_ouc += 1
                    break

            if objects_using_cutter:

                hidden = []
                objects_using_cutter = list(set(objects_using_cutter))

                for c_obj in objects_using_cutter:

                    bfound = False

                    for m in c_obj.modifiers:
                        if not (m.type == "BOOLEAN" and m.object == active):
                            if self.mode == "ALL" and m.show_viewport:
                                hidden.append(m)
                                m.show_viewport = False
                            elif self.mode == "PRE" and m.show_viewport and bfound:
                                hidden.append(m)
                                m.show_viewport = False
                        else:
                            if self.mode == "PRE":
                                bfound = True

                    if hidden:

                        active["ke_solo_cutter"] = True

                        # Create Solo-status Empty
                        solo_empty = bpy.data.objects.new("[ Solo ]", None)
                        context.collection.objects.link(solo_empty)
                        solo_empty.empty_display_size = 0.0001
                        solo_empty.show_name = True
                        solo_empty.hide_select = True
                        solo_empty.parent = active

                        for i, h in enumerate(hidden):
                            n = str(i).rjust(3, "0")
                            str_name = "ks_cutter_" + n
                            c_obj[str_name] = h.name

        if tot_ouc == 0:
            self.report({"INFO"}, "Not a Cutter: Selected obj is not used in any boolean modifier?")
            return {"CANCELLED"}

        return {"FINISHED"}


# -------------------------------------------------------------------------------------------------
# Class Registration & Unregistration
# -------------------------------------------------------------------------------------------------
def register():
    bpy.utils.register_class(VIEW3D_OT_ke_solo_cutter)


def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_ke_solo_cutter)


if __name__ == "__main__":
    register()
