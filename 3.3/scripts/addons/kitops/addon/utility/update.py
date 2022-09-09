import os

from copy import deepcopy as copy

import bpy

from bpy.utils import register_class, unregister_class

from . import addon, insert, math, modifier, ray, regex, id, enums, previews, constants

from mathutils import Vector

smart_mode = True
try: from . import smart
except: smart_mode = False


def kpacks(prop, context):
    option = addon.option()

    for index, category in enumerate(option.kpack.categories):
        if category.name == option.kpacks:
            option.kpack.active_index = index
            if (index < len(option.kpack.categories) and \
                option.kpack.categories[index].blends):
                thumb_active_index = option.kpack.categories[index].active_index
                thumb_name = option.kpack.categories[index].blends[thumb_active_index].name
                option.kpack.categories[index].thumbnail = option.kpack.categories[index].blends[thumb_active_index].name

                #push most recently used to top of stack.
                to_add = option.kpack.categories[index]

                preference = addon.preference()
                recently_used = preference.recently_used

                if to_add.name not in recently_used:
                    recently_used.add().name = to_add.name

                #move to top
                recently_used.move(recently_used.find(to_add.name), 0)

                #reduce recently used list.
                if len(recently_used) > constants.recently_used_limit:
                    for i in range(constants.recently_used_limit, len(recently_used)):
                        recently_used.remove(i)

            break



def kpack(prop, context):
    preference = addon.preference()
    option = addon.option()
    previews.clear()

    if not option:
        return

    def add_blend(location, folder, category):
        for file in os.listdir(os.path.join(location, folder)):
            if file.endswith('.blend') and regex.clean_name(file, use_re=preference.clean_names) not in [blend.name for blend in category.blends]:
                blend = category.blends.add()
                blend.name = regex.clean_name(file, use_re=preference.clean_names)
                blend.location = os.path.join(location, folder, file)

                filepath = os.path.join(location, folder, file[:-6] + '.png')
                if os.path.exists(filepath):
                    icon_path = filepath
                else:
                    icon_path = addon.path.default_thumbnail()

                blend.icon_path = icon_path

    def add_folder(master):
        for folder in [file for file in os.listdir(master.location) if os.path.isdir(os.path.join(master.location, file))]:
            if regex.clean_name(folder, use_re=preference.clean_names) not in [category.name for category in option.kpack.categories]:
                category = option.kpack.categories.add()
                category.name = regex.clean_name(folder, use_re=preference.clean_names)
                category.folder = folder

                add_blend(master.location, folder, category)

                if not len(category.blends):
                    option.kpack.categories.remove([category.name for category in option.kpack.categories].index(category.name))
            else:
                category = option.kpack.categories[regex.clean_name(folder, use_re=preference.clean_names)]

                add_blend(master.location, folder, category)

            if len(category.blends):
                name = category.name
                number = id.convert_to_number(name)
                icon_path = get_icon_path(category)
                icon_path = icon_path if icon_path else addon.path.default_thumbnail()
                enums.kitops_category_enums.append([name, name, '', icon_path, number])

                enum_items_id = []

                for index, blend in enumerate(category.blends):
                    name = blend.name
                    number = id.convert_to_number(name)
                    icon_path = blend.icon_path
                    enum_items_id.append([name, name[:14], name, icon_path, number])

                enums.kitops_insert_enum_map[folder] = enum_items_id

                # NOTE: Enum items are stored as lists instead of tuples, with icon_path instead of icon_id.
                # In the items getter functions, these will be overwritten properly.

    option.kpack.categories.clear()
    enums.kitops_category_enums.clear()
    enums.kitops_insert_enum_map.clear()

    reset = False
    for master in preference.folders:
        if master.location and master.location != 'Choose Path' and master.visible:
            if os.path.isdir(master.location):
                add_folder(master)
            else:
                master.name = 'KPACK'
                master.location = addon.path.default_kpack()

                add_folder(master)

                reset = True

    # clean up favorites, remove any favorites that have been lost.
    to_remove = []
    for favorite in preference.favorites:
        if favorite.name not in option.kpack.categories:
            to_remove.append(favorite.name)
    to_remove = list(set(to_remove))
    for fav_to_remove in to_remove:
        preference.favorites.remove(preference.favorites.find(fav_to_remove))

    # clean up recently used, remove any recently used that have been lost.
    to_remove = []
    for rec_used in preference.recently_used:
        if rec_used.name not in option.kpack.categories:
            to_remove.append(rec_used.name)
    to_remove = list(set(to_remove))
    for rec_used_to_remove in to_remove:
        preference.recently_used.remove(preference.recently_used.find(rec_used_to_remove))

    if reset:
        kpack(None, context)

    elif len(enums.kitops_category_enums):
        item = enums.kitops_category_enums[0]
        option.kpacks = item[0]
        option.kpack.active_index = 0
        if option.kpack.categories and option.kpack.categories[0].blends:
            option.kpack.categories[0].thumbnail = option.kpack.categories[0].blends[0].name

def options():
    option = addon.option()

    kpack(None, bpy.context)


def icons():
    addon.icons.clear()

    for file in os.listdir(addon.path.icons()):
        if file.endswith('.png'):
            addon.icons[file[:-4]] = os.path.join(addon.path.icons(), file)
            previews.get(addon.icons[file[:-4]])


def libpath(prop, context):
    preference = addon.preference()

    for folder in preference.folders:
        if folder.location and folder.location != 'Choose Path':
            folder['location'] = os.path.abspath(bpy.path.abspath(folder.location))
            if not folder.name:
                folder.name = regex.clean_name(os.path.basename(folder.location), use_re=True)
        elif not folder.location:
            folder['location'] = 'Choose Path'

    kpack(None, context)


def thumbnails(prop, context):
    option = addon.option()
    prop['active_index'] = [blend.name for blend in prop.blends].index(prop.thumbnail)
    option.kpack.active_index = [kpack.name for kpack in option.kpack.categories].index(prop.name)
    # reset the scale amount if we are changing the insert.
    option.scale_amount = 1

def get_icon_path(category):
    #determine icon path
    icon_path = None
    if len(category.blends):
        category_folder_path = os.path.join( os.path.dirname(os.path.realpath(category.blends[0].icon_path)), 'k_icon.png')
        if os.path.isfile(category_folder_path):
            icon_path = category_folder_path
    if not icon_path and len(category.blends):
        active_folder_path = os.path.realpath(category.blends[0].icon_path)
        if os.path.isfile(active_folder_path) and active_folder_path != addon.path.default_thumbnail():
            icon_path = active_folder_path
    return icon_path

def get_icon_id(category):
    #determine icon
    icon_id = 0
    icon_path = get_icon_path(category)
    if icon_path:
        return previews.get(icon_path).icon_id
    return 0


def mode(prop, context):
    inserts = [obj for obj in bpy.data.objects if obj.kitops.insert]

    for obj in inserts:
        obj.kitops.applied = True

        if prop.mode == 'REGULAR':
            obj.kitops['insert_target'] = None

    if prop.mode == 'SMART':
        insert.select()


def show_modifiers(prop, context):
    option = addon.option()

    inserts = insert.collect(all=True)

    for obj in bpy.data.objects:
        for modifier in obj.modifiers:
            if modifier.type == 'BOOLEAN' and modifier.object and modifier.object in inserts:
                modifier.show_viewport = option.show_modifiers

# DEPRECATED METHOD WILL DO NOTHING TODO remove if no issues are found.
def show_solid_objects(prop, context):
    return
    option = addon.option()

    for obj in insert.collect(solids=True, all=True):
        obj.hide_viewport = not option.show_solid_objects

# DEPRECATED METHOD WILL DO NOTHING TODO remove if no issues are found.
def show_cutter_objects(prop, context):
    return
    option = addon.option()

    for obj in insert.collect(cutters=True, all=True):
        obj.hide_viewport = not option.show_cutter_objects

# DEPRECATED METHOD WILL DO NOTHING TODO remove if no issues are found.
def show_wire_objects(prop, context):
    return
    option = addon.option()

    for obj in insert.collect(wires=True, all=True):
        obj.hide_viewport = not option.show_wire_objects


def location():
    if ray.success:
        track_quaternion = ray.to_track_quat
        matrix = track_quaternion.to_matrix().to_4x4()

        scale = insert.operator.main.matrix_world.to_scale()
        insert.operator.main.matrix_world = matrix
        insert.operator.main.matrix_world.translation = ray.location
        insert.operator.main.scale = scale


def insert_scale(prop, context):
    preference = addon.preference()
    option = addon.option()

    if preference.auto_scale:
        if not insert.operator:
            mains = insert.collect(context.selected_objects, mains=True)
        else:
            mains = [insert.operator.main] if insert.operator.main else []

        modifiers_shown = bool(option.show_modifiers)
        option.show_modifiers = False
        context.view_layer.update()

        for main in mains:
            if main.kitops.reserved_target and smart_mode or insert.operator and not smart_mode:
                init_hide = copy(main.hide_viewport)
                main.hide_viewport = False

                scale = getattr(preference, '{}_scale'.format(preference.insert_scale.lower()))

                if not main.kitops.reserved_target:
                    continue

                bounds = modifier.unmodified_bounds(main.kitops.reserved_target)
                coords = math.coordinates_dimension(bounds)
                largest_dimension = max(*coords) * (scale * 0.01)

                dimension = main.dimensions
                if dimension.length == 0:
                    dimension = main.scale.copy()

                axis = 'x'
                if dimension.y > dimension.x:
                    axis = 'y'
                if dimension.z > getattr(dimension, axis):
                    axis = 'z'

                setattr(main.scale, axis, largest_dimension / getattr(dimension, axis) * getattr(main.scale, axis))
                remaining_axis = [a for a in 'xyz' if a != axis]
                setattr(main.scale, remaining_axis[0], getattr(main.scale, axis))
                setattr(main.scale, remaining_axis[1], getattr(main.scale, axis))



                main.hide_viewport = init_hide

        if modifiers_shown:
            option.show_modifiers = True

    # context.view_layer.depsgraph.update()


sort_options = (
    'sort_modifiers',
    'sort_bevel',
    'sort_array',
    'sort_mirror',
    'sort_solidify',
    'sort_weighted_normal',
    'sort_simple_deform',
    'sort_triangulate',
    'sort_decimate',
    'sort_remesh',
    'sort_subsurf',
    'sort_bevel_last',
    'sort_array_last',
    'sort_mirror_last',
    'sort_solidify_last',
    'sort_weighted_normal_last',
    'sort_simple_deform_last',
    'sort_triangulate_last',
    'sort_decimate_last',
    'sort_remesh_last',
    'sort_subsurf_last')


def sync_sort(prop, context):
    for option in sort_options:
        if addon.hops() and hasattr(addon.hops().property, option):
            addon.hops().property[option] = getattr(prop, option)
        else:
            print(F'Unable to sync sorting options with Hard Ops; KIT OPS {option}\nUpdate Hard Ops!')

        if addon.bc() and hasattr(addon.bc().behavior, option):
            addon.bc().behavior[option] = getattr(prop, option)
        else:
            print(F'Unable to sync sorting options with Box Cutter; KIT OPS {option}\nUpdate Box Cutter!')


def sort_ignore_char(prop, context):
    if not prop.sort_ignore_char:
        prop.sort_ignore_char = ' '

    sync_sort(prop, context)


def sort_stop_char(prop, context):
    if not prop.sort_stop_char:
        prop.sort_stop_char = '_'

    sync_sort(prop, context)

