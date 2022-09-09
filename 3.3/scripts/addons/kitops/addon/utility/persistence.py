# Utility methods for saving INSERT data.
import bpy
import os
from . import addon, id, modifier, handler

def insert_path(insert_name, context):
    file_name = '_'.join(insert_name.split(' ')) + '.blend'
    directory = directory_from(context.window_manager.kitops.kpack)
    return os.path.join(directory, file_name)

def insert_thumb_path(insert_name, context):
    file_name = '_'.join(insert_name.split(' ')) + '.png'
    directory = directory_from(context.window_manager.kitops.kpack)
    return os.path.join(directory, file_name)

def link_object_to(bpy_type, obj, children=False):
    if children:
        for child in obj.children:
            link_object_to(bpy_type, child, children=True)

    if hasattr(bpy_type, 'collection') and obj.name not in bpy_type.collection.all_objects:
        bpy_type.collection.objects.link(obj)

        return

    if obj.name not in bpy_type.objects:
        bpy_type.objects.link(obj)

def directory_from(kpack):
    current = kpack.categories[kpack.active_index]
    return os.path.realpath(os.path.dirname(current.blends[current.active_index].location))


def bool_objects(obj):
    bools = []
    for mod in obj.modifiers:
        if mod.type != 'BOOLEAN' or not mod.object:
            continue
        bools.append(mod.object)
        for ob in bool_objects(mod.object):
            bools.append(ob)

    return list(set(bools))

def create_snapshot(self, context, path):
    original_path = context.scene.render.filepath

    if not path:
        self.report({'WARNING'}, 'Unable to save rendered thumbnail, no reference PATH (Save your file first?)')
        return {'FINISHED'}

    if not context.scene.camera:
        for obj in context.scene.collection.all_objects:
            if obj.kitops.temp and obj.type == 'CAMERA':
                context.scene.camera = obj

                break

    context.scene.render.filepath = path
    
    bpy.ops.render.render(write_still=True)

    context.scene.render.filepath = original_path

    return {'FINISHED'}


def remove_object(obj, log=True): # TODO dupe method in smart
    collection_lookup = {
        "ARMATURE": bpy.data.armatures,
        "CAMERA": bpy.data.cameras,
        "CURVE": bpy.data.curves,
        "FONT": bpy.data.curves,
        "GPENCIL": bpy.data.grease_pencils,
        "LATTICE": bpy.data.lattices,
        "LIGHT": bpy.data.lights,
        "LIGHT_PROBE": bpy.data.lightprobes,
        "MESH": bpy.data.meshes,
        "SPEAKER": bpy.data.speakers,
        "SURFACE": bpy.data.curves,
        "VOLUME": bpy.data.volumes}

    if obj.type in collection_lookup:
        if log:
            print(F'        KITOPS: Removing {obj.type.lower()} datablock: {obj.data.name}')
        try:
            collection_lookup[obj.type].remove(obj.data)
        except ReferenceError:
            pass

    if obj in bpy.data.objects[:]:
        if log:
            print(F'        KITOPS: Removing object datablock: {obj.name}')
        try:
            bpy.data.objects.remove(obj)
        except ReferenceError:
            pass




def remove_temp_objects(duplicates=False, log=True):
    if log:
        print('')
    # material_base = False
    for obj in bpy.data.objects:
        # if not material_base and obj.kitops.material_base:
        #     material_base = True
        if obj.data and hasattr(obj.data, 'materials'):
            for mat in obj.data.materials:
                if mat and 'KITOPS FACTORY' in mat.name:
                    if log:
                        print(F'        KITOPS: Removing material datablock: {mat.name}')
                    try:
                        bpy.data.materials.remove(mat)
                    except ReferenceError:
                        pass


        if obj.kitops.temp or (duplicates and (obj.kitops.duplicate or obj.kitops.bool_duplicate)) or 'KITOPS FACTORY' in obj.name or obj.kitops.material_base:
            if log:
                print(F'        KITOPS: Removing object datablock: {obj.name}')
            remove_object(obj, log=log)

            continue
    
    factory_worlds = [w for w in bpy.data.worlds if w.kitops.is_factory_scene]
    for world in factory_worlds:
        try:
            bpy.data.worlds.remove(world)
        except ReferenceError:
            pass
    factory_images = [img for img in bpy.data.images if img.kitops.is_factory_scene]
    for img in factory_images:
        try:
            bpy.data.images.remove(img)
        except ReferenceError:
            pass


    if bpy.app.version > (2, 83, 0):
        for lib in bpy.data.libraries:
            if lib.filepath in {addon.path.material()}:
                try:
                    bpy.data.libraries.remove(lib)
                except ReferenceError:
                    pass

def new_factory_scene(context, link_selected=False, link_children=False, duplicate=False, material_base=False):
    # global original_materials
    preference = addon.preference()
    path = addon.path.thumbnail()

    strip_num = lambda string: string.rstrip('0123456789.') if len(string.split('.')) == 2 else string

    context.window_manager.kitops.author = preference.author

    original = bpy.data.scenes[context.scene.name]
    active_name = context.active_object.name
    material = context.active_object.active_material
    materials = [slot.material for slot in context.active_object.material_slots if slot.material]

    insert = []
    bools = []
    if not material_base:
        for obj in context.selected_objects[:]:
            insert.append(obj)
            insert.extend(bool_objects(obj))
            bools.extend(bool_objects(obj))

            # if hasattr(obj, 'material_slots'):
            #     original_materials[obj.name] = [slot.material.name for slot in obj.material_slots if slot.material]

        for obj in insert:
            insert.extend([o for o in bpy.data.objects if o.parent == obj])

        # for obj in bpy.data.objects:
        #     if obj.parent in context.visible_objects[:]:
        #         insert.append(obj)

    insert = sorted(list(set(insert)), key=lambda o: o.name)
    bools = sorted(bools, key=lambda o: o.name)

    with bpy.data.libraries.load(path) as (blend, imported):
        imported.scenes = blend.scenes
        imported.objects = blend.objects
        imported.images = blend.images
        imported.worlds = blend.worlds

    objects = imported.objects[:]
    images = imported.images[:]
    worlds = imported.worlds[:]
    scene = imported.scenes[0]


    if material_base:
        with bpy.data.libraries.load(addon.path.material()) as (blend, imported):
            imported.objects = blend.objects

        objects.append(*imported.objects) # should only ever be one object

    scene.name = 'KITOPS FACTORY'
    scene.kitops.factory = True
    scene.kitops.thumbnail = True
    context.window.scene = scene

    context.scene.kitops.last_edit = ''

    for obj in objects:
        obj.kitops.is_factory_scene = True
        obj.kitops.id = ''
        obj.kitops.insert = False
        obj.kitops.insert_target = None
        obj.kitops.main = False
        obj.kitops.temp = True
        obj.select_set(False)

        if obj.kitops.material_base:
            obj.kitops.temp = False
            link_object_to(scene, obj)
            context.view_layer.objects.active = obj
            context.window_manager.kitops.insert_name = material.name

            for mat in materials:
                mat.kitops.id = id.uuid()
                mat.kitops.material = True
                obj.data.materials.append(mat)

    for image in images:
        image.kitops.is_factory_scene = True

    for world in worlds:
        world.kitops.is_factory_scene = True

    if link_selected:
        for obj in insert:
            link_object_to(scene, obj)
            obj.hide_set(False)
            obj.kitops.duplicate = duplicate

            if obj in bools:
                obj.kitops.duplicate = duplicate
                if not duplicate:
                    obj.kitops.type = 'CUTTER'
                    obj.kitops.boolean_type = 'INSERT'
                else:
                    obj.kitops.bool_duplicate = True

            for ob in bpy.data.objects:
                if not hasattr(ob, 'modifiers'):
                    continue

                for mod in ob.modifiers:
                    if mod.type != 'BOOLEAN' or mod.object != obj or mod.object not in insert or mod.object in bools:
                        continue

                    mod.object.kitops.type = 'CUTTER'

            if obj.name == active_name:
                context.view_layer.objects.active = obj
                obj.kitops.main = True

    for obj in context.visible_objects:
        if not obj.kitops.temp or obj.kitops.material_base:
            obj.select_set(True)

    if duplicate:
        # we need to stop the handler from firing when we are duplicating so that object visibility is not affected.
        old_is_saving = handler.is_saving
        handler.is_saving = True
        bpy.ops.object.duplicate()
        handler.is_saving = old_is_saving

        for obj in insert:
            obj.kitops.duplicate = False

        for obj in bools:
            obj.kitops.duplicate
            obj.kitops.bool_duplicate = False

        bpy.ops.object.delete({'selected_objects': list(set(insert + bools))})

        duplicates = [obj for obj in scene.collection.all_objects if not obj.kitops.temp]
        bases = [obj for obj in duplicates if not obj.kitops.bool_duplicate]

        for obj in duplicates:
            obj.kitops.duplicate = False
            if obj.parent in insert:
                for ob in bases:
                    for mod in ob.modifiers:
                        if mod.type != 'BOOLEAN' or not mod.object or mod.object != obj:
                            continue

                        obj['parent'] = ob

            if obj.kitops.bool_duplicate:
                obj.kitops.type = 'CUTTER'
                obj.kitops.boolean_type = 'INSERT'
            elif obj.kitops.type != 'CUTTER':
                obj.kitops.type = 'SOLID'
            else:
                obj.kitops.type = 'CUTTER'

            if hasattr(obj, 'data') and obj.data:
                obj.data = obj.data.copy()

            if strip_num(obj.name) == active_name:
                context.view_layer.objects.active = obj

            obj.kitops.bool_duplicate = False

        del insert
        del bools
        del duplicates
        del bases

    for obj in context.visible_objects:
        if not obj.kitops.temp or obj.kitops.material_base:
            obj.select_set(True)

    for obj in context.scene.collection.all_objects:
        if obj.kitops.temp and obj.type == 'CAMERA':
            context.scene.camera = obj

    scene.kitops.original_scene = original.name
    return original, scene

def set_active_category_from_last_edit(context):
    bpy.ops.ko.refresh_kpacks()
    option = context.window_manager.kitops

    kpack = context.window_manager.kitops.kpack
    for ic, category in enumerate(kpack.categories):
        for ib, blend in enumerate(category.blends):
            if os.path.realpath(blend.location) != context.scene.kitops.last_edit:
                continue

            option.kpacks = category.name
            option.kpack.active_index = ic
            current = option.kpack.categories[category.name]
            current.active_index = ib
            current.thumbnail = blend.name

            break


def save_insert(path='', objects=[]):
    context = bpy.context

    path = insert_path(context.window_manager.kitops.insert_name, context) if not path else path

    path = os.path.realpath(path)

    scene = bpy.data.scenes.new(name='main')
    scene.kitops.animated = context.scene.kitops.animated

    objs = objects if objects else [obj for obj in context.scene.collection.all_objects if not obj.kitops.temp]

    was_duplicate = False

    for obj in objs:
        link_object_to(scene, obj)

        obj.kitops.id = ''
        obj.kitops.author = context.window_manager.kitops.author
        obj.kitops.insert = False
        obj.kitops.applied = False
        obj.kitops.animated = scene.kitops.animated
        obj.kitops['insert_target'] = None
        obj.kitops['mirror_target'] = None
        obj.kitops['reserved_target'] = None
        obj.kitops['main_object'] = None

        if obj.kitops.duplicate:
            was_duplicate = True
            obj.kitops.duplicate = False

        if hasattr(obj, 'data') and obj.data:
            obj.data.kitops.id = id.uuid()
            obj.data.kitops.insert = False

        # if hasattr(obj, 'data') and obj.data and hasattr(obj.data, 'materials'):
            # for mat in obj.data.materials:
        if hasattr(obj, 'material_slots'):
            for slot in obj.material_slots:
                if slot.material and 'KITOPS FACTORY' in slot.material.name:
                    obj.active_material_index = 0
                    for _ in range(len(obj.material_slots)):
                        bpy.ops.object.material_slot_remove({'object': obj})

                    break

        if obj.kitops.material_base:
            obj.kitops.material_base = False
            for slot in reversed(obj.material_slots[:]):
                if slot.material and slot.material.name.rstrip('0123456789.') == 'Material':
                    slot.material.name = context.window_manager.kitops.insert_name


    bpy.ops.file.pack_all()

    bpy.data.libraries.write(path, {scene}, compress=True)
    import subprocess
    subprocess.Popen([bpy.app.binary_path, '-b', path, '--python', os.path.join(addon.path(), 'addon', 'utility', 'save.py')])

    bpy.data.scenes.remove(scene)

    for obj in objs:
        obj.kitops.type = obj.kitops.type
        if was_duplicate:
            obj.kitops.duplicate = True

    context.scene.kitops.last_edit = path
    bpy.ops.ko.refresh_kpacks()
    set_active_category_from_last_edit(context)




def close_factory_scene(self, context, log=True):
    try: original_scene = bpy.data.scenes[context.scene.kitops.original_scene]
    except: original_scene = None

    if not original_scene:
        context.scene.name = 'Scene'
        context.scene.kitops.factory = False
        remove_temp_objects(log=False)
        return {'FINISHED'}

    remove_temp_objects(duplicates=True, log=False)

    if original_scene:
        to_remove = []
        for obj in bpy.data.scenes[context.scene.name].collection.all_objects:
            delete=True
            for scene in bpy.data.scenes:
                if scene.name != context.scene.name and obj.name in scene.collection.all_objects:
                    delete = False
                    break
            if delete:
                to_remove.append(obj)
        for obj in to_remove:
            remove_object(obj, log=log)
        bpy.data.scenes.remove(bpy.data.scenes[context.scene.name])
        context.window.scene = original_scene

    return {'FINISHED'}



class update:

    def author(prop, context):
        if not hasattr(context, 'active_object'):
            return

        for obj in bpy.data.objects:
            obj.kitops.author = context.active_object.kitops.author

    def type(prop, context):
        all_objects = [i for i in context.scene.collection.all_objects]
        
        try: ground_box = [obj for obj in all_objects if obj.kitops.ground_box][0]
        except: ground_box = None # ground box not detected

        for obj in all_objects:
            if obj.kitops.type == 'SOLID' or obj.type == 'GPENCIL':
                obj.display_type = 'SOLID' if obj.type != 'GPENCIL' else 'TEXTURED'

                if obj.type == 'MESH':
                    obj.hide_render = False



                    if hasattr(obj, 'cycles_visibility'):
                        obj.cycles_visibility.camera = True
                        obj.cycles_visibility.diffuse = True
                        obj.cycles_visibility.glossy = True
                        obj.cycles_visibility.transmission = True
                        obj.cycles_visibility.scatter = True
                        obj.cycles_visibility.shadow = True

                    if hasattr(obj, 'visible_camera'):
                        obj.visible_camera = True

                    if hasattr(obj, 'visible_diffuse'):
                        obj.visible_diffuse = True

                    if hasattr(obj, 'visible_glossy'):
                        obj.visible_glossy = True

                    if hasattr(obj, 'visible_transmission'):
                        obj.visible_transmission = True

                    if hasattr(obj, 'visible_volume_scatter'):
                        obj.visible_volume_scatter = True

                    if hasattr(obj, 'visible_shadow'):
                        obj.visible_shadow = True

            elif (obj.kitops.type == 'WIRE' or obj.kitops.type == 'CUTTER') and obj.type == 'MESH':
                obj.display_type = 'WIRE'

                obj.hide_render = True

                if hasattr(obj, 'cycles_visibility'):
                    obj.cycles_visibility.camera = False
                    obj.cycles_visibility.diffuse = False
                    obj.cycles_visibility.glossy = False
                    obj.cycles_visibility.transmission = False
                    obj.cycles_visibility.scatter = False
                    obj.cycles_visibility.shadow = False

                if hasattr(obj, 'visible_camera'):
                    obj.visible_camera = False

                if hasattr(obj, 'visible_diffuse'):
                    obj.visible_diffuse = False

                if hasattr(obj, 'visible_glossy'):
                    obj.visible_glossy = False

                if hasattr(obj, 'visible_transmission'):
                    obj.visible_transmission = False

                if hasattr(obj, 'visible_volume_scatter'):
                    obj.visible_volume_scatter = False

                if hasattr(obj, 'visible_shadow'):
                    obj.visible_shadow = False



        if ground_box and context.scene.kitops.factory:
            mats = [slot.material for slot in ground_box.material_slots if slot.material]
            for obj in sorted(all_objects, key=lambda o: o.name):
                if obj.kitops.temp or obj.type != 'MESH' or obj.kitops.material_base or obj.kitops.duplicate:
                    continue

                boolean = None
                for mod in ground_box.modifiers:
                    if mod.type == 'BOOLEAN' and mod.object == obj and obj.kitops.boolean_type != 'INSERT':
                        mod.show_viewport = obj.kitops.type == 'CUTTER' and obj.kitops.boolean_type != 'INSERT'
                        mod.show_render = mod.show_viewport
                        mod.operation = obj.kitops.boolean_type
                        boolean = mod

                if not boolean:
                    if obj.kitops.boolean_type != 'INSERT':

                        mod = ground_box.modifiers.new(name='KITOPS Boolean', type='BOOLEAN')
                        mod.object = obj
                        mod.operation = obj.kitops.boolean_type

                        if hasattr(mod, 'solver'):
                            mod.solver = addon.preference().boolean_solver

                        boolean = mod
                        modifier.sort(ground_box)

                if not obj.material_slots:
                    obj.data.materials.append(ground_box.material_slots[3].material)

                if not obj.material_slots or obj.material_slots[0].material in mats:
                    if obj.kitops.boolean_type == 'UNION':
                        boolean.operation = 'UNION'
                        obj.material_slots[0].material = ground_box.material_slots[1].material

                    elif obj.kitops.boolean_type == 'DIFFERENCE':
                        boolean.operation = 'DIFFERENCE'
                        obj.material_slots[0].material = ground_box.material_slots[2].material

                    else:
                        boolean.operation = 'INTERSECT'

                    if obj.kitops.type != 'CUTTER' or obj.kitops.boolean_type in {'INTERSECT', 'INSERT'}:
                        obj.material_slots[0].material = ground_box.material_slots[3].material
