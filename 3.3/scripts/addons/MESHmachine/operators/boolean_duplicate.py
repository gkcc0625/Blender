import bpy
from bpy.props import BoolProperty
from .. utils.object import parent


class BooleanDuplicate(bpy.types.Operator):
    bl_idname = "machin3.boolean_duplicate"
    bl_label = "MACHIN3: Boolean Duplicate"
    bl_description = "Duplicate Boolean Objects with their Cutters\nALT: Instance the Object and Cutter Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    instance: BoolProperty(name="Instance", default=False)

    @classmethod
    def poll(cls, context):
        return [obj for obj in context.selected_objects if any(mod.type == 'BOOLEAN' and mod.object for mod in obj.modifiers)]

    def invoke(self, context, event):
        self.instance = event.alt
        return self.execute(context)

    def execute(self, context):

        self.recursive_dup(context, debug=False)

        bpy.ops.transform.translate('INVOKE_DEFAULT')

        return {'FINISHED'}

    def get_operants(self, objs, boolean_operants, depth=0, debug=False):

        if debug and depth == 0:
            print()

        for obj in objs:
            if debug:
                print(" " * depth, obj.name)

            booleans = [(mod, mod.object) for mod in obj.modifiers if mod.type == 'BOOLEAN' and mod.object]

            for boolean, boolean_obj in booleans:
                if debug:
                    print("  " * depth, boolean.operation, boolean_obj.name)

                boolean_operants.add((obj, boolean, boolean_obj))

                self.get_operants([boolean_obj], boolean_operants, depth=depth + 1, debug=debug)

    def recursive_dup(self, context, debug=False):

        view_layer = context.view_layer

        if debug:
            print()

        selected_objs = {obj for obj in context.selected_objects}

        if debug:
            print("selected objs:", [obj.name for obj in selected_objs])

        boolean_objs = {obj for obj in selected_objs if any(mod.type == 'BOOLEAN' and mod.object for mod in obj.modifiers)}

        if debug:
            print(" boolean objs:", [obj.name for obj in boolean_objs])

        operant_objs = set()
        self.get_operants(boolean_objs, operant_objs, depth=0, debug=debug)

        if debug:
            print(" operant objs:", [f"{parent.name}: {mod.name}: {obj.name}" for parent, mod, obj in operant_objs])

        other_objs = selected_objs.difference(boolean_objs, {obj for _, _, obj in operant_objs})

        if debug:
            print("   other objs:", [obj.name for obj in other_objs])

        duplicate_objs = {obj: None for obj in boolean_objs | {obj for _, _, obj in operant_objs} | other_objs}

        for obj in duplicate_objs:
            obj.select_set(False)

            is_active = obj == context.active_object

            dup = obj.copy()
            duplicate_objs[obj] = dup

            if obj.data and not self.instance:
                dup.data = obj.data.copy()

            for col in obj.users_collection:
                col.objects.link(dup)

            dup.select_set(True)

            if is_active:
                context.view_layer.objects.active = dup

        if debug:
            print(" duplicate objs:", [f"{obj.name}: {dup.name}" for obj, dup in duplicate_objs.items()])

        for obj, mod, operant in operant_objs:
            dup_obj = duplicate_objs[obj]
            dup_operant = duplicate_objs[operant]

            dup_mod = dup_obj.modifiers.get(mod.name, None)

            if dup_mod:
                dup_mod.object = dup_operant

            if operant.parent and operant.parent in duplicate_objs:
                parent(dup_operant, dup_obj)

                if operant not in selected_objs:
                    dup_operant.select_set(False)

            dup_operant.hide_set(operant.hide_get(view_layer=view_layer), view_layer=view_layer)

        for obj in boolean_objs:
            if obj.parent and obj.parent in duplicate_objs:
                parent(duplicate_objs[obj], duplicate_objs[obj.parent])

    def old_dup(self, context):
        objs = [obj for obj in context.selected_objects if any(mod.type == 'BOOLEAN' and mod.object for mod in obj.modifiers)]

        for obj in objs:

            obj.select_set(False)
            is_active = obj == context.active_object

            cols = obj.users_collection
            dup = obj.copy()

            if not self.instance:
                dup.data = obj.data.copy()

            for col in cols:
                col.objects.link(dup)

            dup.select_set(True)

            if is_active:
                context.view_layer.objects.active = dup

            booleans = [mod for mod in dup.modifiers if mod.type == 'BOOLEAN' and mod.object]

            for mod in booleans:
                orig = mod.object
                cols = orig.users_collection

                cutter = orig.copy()

                if not self.instance:
                    cutter.data = orig.data.copy()

                for col in cols:
                    col.objects.link(cutter)

                cutter.hide_set(orig.hide_get())
                mod.object = cutter

                parent(cutter, dup)

        bpy.ops.transform.translate('INVOKE_DEFAULT')
