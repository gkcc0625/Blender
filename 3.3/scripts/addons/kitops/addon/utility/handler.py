import sys
import traceback

import bpy
from bpy.app.handlers import persistent, depsgraph_update_pre, depsgraph_update_post, load_pre, load_post, save_pre

from . import addon, shader, insert, remove, update, smart

authoring_enabled = True
try: from . import matrixmath
except:
    traceback.print_exc()
    authoring_enabled = False

# flag to determine whether we are saving or not.
is_saving = False
class pre:


    @persistent
    def depsgraph(none):

        global is_saving
        if is_saving:
            return

        if not insert.authoring():

            smart.insert_depsgraph_update_pre()

            insert.correct_ids()

        elif not authoring_enabled:
            for obj in bpy.data.objects:
                try:
                    obj.select_set(False)
                except RuntimeError: pass


        if not authoring_enabled:
            for obj in bpy.data.objects:
                if obj.kitops.main and not obj.kitops.id:
                    sys.exit()


    @persistent
    def load(none):
        # if shader.handler:
        #     bpy.types.SpaceView3D.draw_handler_remove(shader.handler, 'WINDOW')

        # shader.handler = None

        global is_saving
        if is_saving:
            return


        if not authoring_enabled:
            for obj in bpy.data.objects:
                if obj.kitops.main and not obj.kitops.id:
                    sys.exit()


    @persistent
    def save(none):
        global is_saving
        if is_saving:
            return

        option = addon.option()

        if authoring_enabled:
            matrixmath.authoring_save_pre()

        if not authoring_enabled:
            for obj in bpy.data.objects:
                if obj.kitops.main and not obj.kitops.id:
                    sys.exit()


class post:


    @persistent
    def depsgraph(none):
        global is_saving
        if is_saving:
            return

        preference = addon.preference()
        option = addon.option()

        if insert.authoring():
            if authoring_enabled:
                matrixmath.authoring_depsgraph_update_post()
        else:
            scene = bpy.context.scene
            if not insert.operator and scene and hasattr(scene, 'kitops') and scene.kitops and not scene.kitops.thumbnail:
                for obj in [ob for ob in bpy.data.objects if ob.kitops.duplicate]:
                    remove.object(obj, data=True)

            if addon.preference().mode == 'SMART':
                insert.select()

            if not insert.operator:
                smart.toggles_depsgraph_update_post()

        if not authoring_enabled:
            for obj in bpy.data.objects:
                if obj.kitops.main and not obj.kitops.id:
                    sys.exit()


    @persistent
    def load(none):
        global is_saving
        if is_saving:
            return
            
        option = addon.option()

        # shader.handler = bpy.types.SpaceView3D.draw_handler_add(shader.border, (None, bpy.context), 'WINDOW', 'POST_PIXEL')

        if insert.authoring():
            if authoring_enabled:
                matrixmath.authoring_load_post()
            else:
                for obj in bpy.data.objects:
                    obj.kitops.applied = True

        if not authoring_enabled:
            for obj in bpy.data.objects:
                if obj.kitops.main and not obj.kitops.id:
                    sys.exit()


def register():
    depsgraph_update_pre.append(pre.depsgraph)
    depsgraph_update_post.append(post.depsgraph)
    load_pre.append(pre.load)
    load_post.append(post.load)
    save_pre.append(pre.save)


def unregister():
    depsgraph_update_pre.remove(pre.depsgraph)
    depsgraph_update_post.remove(post.depsgraph)
    load_pre.remove(pre.load)
    load_post.remove(post.load)
    save_pre.remove(pre.save)
