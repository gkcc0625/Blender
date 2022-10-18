#
#     This file is part of NodePreview.
#     Copyright (C) 2021 Simon Wendsche
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bpy
from bpy.app.handlers import persistent
from bpy.types import SpaceImageEditor, SpaceNodeEditor, AddonPreferences
import bgl
import blf
import gpu
from gpu_extras.batch import batch_for_shader

from time import time, sleep
from math import sqrt
import os
join_paths = os.path.join
import platform
import tempfile
import shutil
import subprocess
import threading
from multiprocessing import current_process
from multiprocessing.connection import Listener, Connection
from typing import Optional
import base64
import re
import queue

current_dir = os.path.dirname(os.path.realpath(__file__))

if platform.system() not in {"Windows", "Linux", "Darwin"}:
    raise Exception("\n\nUnsupported platform:", platform.system())

try:
    from . import nodepreview_worker
except ImportError as error:
    msg = ""
    py_version = platform.python_version_tuple()[:2]
    if py_version not in (("3", "7"), ("3", "9"), ("3", "10")):
        msg = (f"\n\nThe Python version of this Blender build (Python {py_version[0]}.{py_version[1]})"
               f" is not supported.\nSupported are Python 3.7, 3.9 and 3.10.\n"
               f"Check the documentation.txt file to see which Blender versions are supported.")
    elif platform.system() == "Windows":
        msg = ("\n\nYou have to install the following: https://aka.ms/vs/15/release/vc_redist.x64.exe\n"
               "Check the documentation.txt file for more information about how to install this addon.")
    # Raise from None to suppress the unhelpful
    # "during handling of the above exception, ..."
    raise Exception(msg + "\n\nImportError: %s" % error) from None


from . import (addon_name, THUMB_CHANNEL_COUNT, SUPPORTED_NODE_TREE, force_node_editor_draw,
               needs_linking, UnsupportedNodeException, BACKGROUND_PATTERNS, get_blend_abspath,
               make_unique_image_name)
from . import messages, node_converter, scene_converter
from .node_converter import node_to_script, make_node_key


images_failed_to_link_lock = threading.Lock()
images_failed_to_link = set()


class WatcherThread(threading.Thread):
    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while not self.stopped():
            if connection.poll(timeout=0.05):
                msg = connection.recv()
                tag, data = msg

                if tag == messages.BACKGROUND_PROCESS_READY:
                    global background_process_ready
                    background_process_ready = True
                    # Force one refresh to render all nodes that are currently visible
                    force_node_editor_draw()
                elif tag == messages.JOB_DONE:
                    node_key, result_array, thumb_resolution, job_timestamp, error_message, full_error_log = data
                    
                    if full_error_log:
                        addon_print(full_error_log)

                    try:
                        # The old thumbnail will be deleted. We need to free its OpenGL texture in the main thread later.
                        old_texture_id = thumbnails[node_key].texture_id
                        if old_texture_id != 0:
                            texture_ids_to_delete.put(old_texture_id)
                    except KeyError:
                        pass

                    thumb = Thumbnail()
                    thumb.buffer = bgl.Buffer(bgl.GL_BYTE, [len(result_array)], result_array)
                    thumb.width = thumb_resolution
                    thumb.height = thumb_resolution
                    thumb.channel_count = THUMB_CHANNEL_COUNT
                    thumb.text = error_message

                    thumbnails[node_key] = thumb

                    try:
                        last_timestamp = cached_nodes[node_key][1]
                        if job_timestamp < last_timestamp:
                            # Force re-sending the job if the last job didn't go through
                            del cached_nodes[node_key]
                    except KeyError:
                        pass

                    force_node_editor_draw()
                elif tag == messages.IMAGES_FAILED_TO_LINK:
                    with images_failed_to_link_lock:
                        images_failed_to_link.update(data)


handle = None  # Draw handler
thumbnails = {}  # filepath : Thumbnail
texture_ids_to_delete = queue.Queue()
cached_nodes = {}  # node_key : hash(node_script), timestamp
# Output directory where rendered thumbnails are saved by our Blender sub-process
temp_dir = join_paths(tempfile.gettempdir(), f"BlenderNodePreview_{os.getpid()}")
TEMP_DIR_REGEX_PATTERN = r"BlenderNodePreview_[0-9]+"

background_process_ready = False
background_process: Optional[subprocess.Popen] = None
listener: Optional[Listener] = None
connection: Optional[Connection] = None
watcher_thread: Optional[WatcherThread] = None


UNSUPPORTED_NODES = {
    "ShaderNodeShaderToRGB",
    "NodeReroute",
    "ShaderNodeHoldout",  # Makes no sense to render a black thumbnail every time
    "ShaderNodeEeveeSpecular",
    "ShaderNodeAttribute",
    "NodeGroupInput",
    "NodeGroupOutput",
}
NODES_NEEDING_MORE_SAMPLES = {
    "ShaderNodeSubsurfaceScattering",
    "ShaderNodeVolumeScatter",
    "ShaderNodeVolumePrincipled",
    "ShaderNodeBevel",
    "ShaderNodeMixShader",
    "ShaderNodeAddShader",
}
# Above these thresholds, procedural textures become too fine-grained for the preview (at default texture mapping)
SCALE_HELP_THRESHOLDS = {
    "ShaderNodeTexBrick": 11,
    "ShaderNodeTexChecker": 35,
    "ShaderNodeTexMagic": 16,
    "ShaderNodeTexMusgrave": 50,
    "ShaderNodeTexNoise": 40,
    "ShaderNodeTexWave": 11,
    "ShaderNodeTexVoronoi": 30,
}
NULL = 0

if not bpy.app.background:
    with open(join_paths(current_dir, "shaders", "thumbnail_vert.glsl")) as vert:
        with open(join_paths(current_dir, "shaders", "thumbnail_frag.glsl")) as frag:
            shader = gpu.types.GPUShader(vert.read(), frag.read())


class Thumbnail:
    def __init__(self):
        self.texture_id = 0
        self.texture_initialized = False
        self.buffer = None
        self.width = -1
        self.height = -1
        self.channel_count = -1
        self.text = ""

    def load_texture(self):
        """Has to be called from the main thread!"""
        texture = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenTextures(1, texture)
        self.texture_id = texture[0]

        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.texture_id)
        # Note: I always use bgl.GL_RGBA8 and bgl.GL_RGBA (4 channels).
        # According to the OpenGL specification, most graphics drivers transform anything
        # with less channels than 4 into GL_RGBA8. Unfortunately, this conversion seems
        # to be buggy (e.g. on my Nvidia driver), so I'm not using less channels than 4,
        # even though I would like to (to save memory).
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA8, self.width, self.height,
                         0, bgl.GL_RGBA, bgl.GL_BYTE, self.buffer)

        edge_mode = bgl.GL_CLAMP_TO_EDGE
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, edge_mode)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, edge_mode)

        interpolation_mode = bgl.GL_LINEAR
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, interpolation_mode)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, interpolation_mode)

        bgl.glBindTexture(bgl.GL_TEXTURE_2D, NULL)
        self.texture_initialized = True


    def draw(self, bottom_left, bottom_right, top_right, top_left, scaled_zoom):
        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.texture_id)

        shader.bind()
        shader.uniform_int("image", 0)
        shader.uniform_int("gamma_correct", bpy.app.version >= (2, 91, 0))

        batch = batch_for_shader(
            shader, 'TRI_FAN',  # TODO TRI_FAN deprecated, replace with 'TRI_STRIP' or 'TRIS' (https://developer.blender.org/rBe2d8b6dc06)
            {
                "pos": (bottom_left, bottom_right, top_right, top_left),
                "texCoord": ((0, 1), (1, 1), (1, 0), (0, 0)),  # Note: Mirrored along y axis
            },
        )
        batch.draw(shader)

        if self.text:
            position = (top_left[0], top_left[1] + 3 * scaled_zoom)
            draw_text(self.text, position, 10, scaled_zoom)


def draw_text(text, position, font_size, scaled_zoom):
    FONT_ID = 0
    FONT_DPI = 72

    x, y = position
    for line in reversed(text.split("\n")):
        blf.position(FONT_ID, x, y, 0)
        blf.size(FONT_ID, round(font_size * scaled_zoom), FONT_DPI)
        blf.draw(FONT_ID, line)
        y += font_size * scaled_zoom
    return y


def delete_old_textures_if_necessary():
    count = texture_ids_to_delete.qsize()
    if count > 40:  # Arbitrary threshold
        texture_ids = bgl.Buffer(bgl.GL_INT, [count])
        for i in range(count):
            texture_ids[i] = texture_ids_to_delete.get(block=True)
        bgl.glDeleteTextures(count, texture_ids)


def addon_print(*args, **kwargs):
    print("[NodePreview]", *args, **kwargs)


def view_to_region_scaled(context, x, y, clip=True):
    ui_scale = context.preferences.system.ui_scale
    return context.region.view2d.view_to_region(x * ui_scale, y * ui_scale, clip=clip)


def get_region_zoom(context):
    test_length = 1000
    x0, y0 = context.region.view2d.view_to_region(0, 0, clip=False)
    x1, y1 = context.region.view2d.view_to_region(test_length, test_length, clip=False)
    xl = x1 - x0
    yl = y1 - y0
    return sqrt(xl**2 + yl**2) / test_length


def needs_more_than_1_sample(node):
    bl_idname = node.bl_idname

    if node.bl_idname == "ShaderNodeGroup" and node.node_tree:
        for subnode in node.node_tree.nodes:
            if needs_more_than_1_sample(subnode):
                return True

    if bl_idname == "ShaderNodeBsdfTransparent":
        return False

    if bl_idname == "ShaderNodeBsdfDiffuse" and node.inputs["Normal"].is_linked:
        return True

    if bl_idname in {"ShaderNodeBsdfDiffuse", "ShaderNodeBsdfGlossy"}:
        roughness_input = node.inputs["Roughness"]
        # At roughness = 0, there's no noise with 1 sample
        return roughness_input.is_linked or roughness_input.default_value > 0

    return (bl_idname.startswith("ShaderNodeBsdf")
            or bl_idname in NODES_NEEDING_MORE_SAMPLES)


def is_node_supported(node):
    if len(node.outputs) == 0:
        return False

    return node.bl_idname not in UNSUPPORTED_NODES


def to_valid_filename(name):
    return base64.urlsafe_b64encode(name.encode("UTF-8")).decode("UTF-8")


def handler():
    # from time import perf_counter
    # __start = perf_counter()

    if not background_process_ready:
        return

    context = bpy.context

    if context.space_data.tree_type != SUPPORTED_NODE_TREE:
        return

    if not context.space_data.path:
        return

    # Path contains a chain of nested node trees, the last one is the currently active one
    node_tree = context.space_data.path[-1].node_tree
    if not node_tree:
        return

    if not node_tree.node_preview.enabled:
        return

    preferences = context.preferences.addons[addon_name].preferences
    enabled_by_default = preferences.previews_enabled_by_default
    all_previews_disabled = True
    for node in node_tree.nodes:
        try:
            enabled = node.node_preview.enabled if node.node_preview.enabled_modified else enabled_by_default
            if enabled:
                all_previews_disabled = False
                break
        except AttributeError:  # Some special nodes might not have the node_preview attribute
            pass
    if all_previews_disabled:
        return

    if not node_converter.node_attributes_cache:
        node_converter.build_node_attributes_cache()

    area = context.area
    ui_scale = context.preferences.system.ui_scale
    zoom = get_region_zoom(context)
    scaled_zoom = zoom * ui_scale
    thumb_scale = preferences.thumb_scale / 100
    thumb_resolution = preferences.thumb_resolution

    using_checker_pattern = preferences.background_pattern == BACKGROUND_PATTERNS.CHECKER
    background_col_1 = list(preferences.background_color_1) + [1]
    background_col_2 = list(preferences.background_color_2) + [1] if using_checker_pattern else background_col_1
    background_colors = background_col_1, background_col_2

    # Sort nodes
    # Build node dependency mapping
    node_deps = {}
    for link in node_tree.links:
        try:
            node_deps[link.from_node].append(link.to_node)
        except KeyError:
            node_deps[link.from_node] = [link.to_node]

    def get_dependent_nodes(node):
        try:
            return node_deps[node]
        except KeyError:
            return []

    sorted_nodes = node_converter.sort_topologically(node_tree.nodes, get_dependent_nodes)

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    bgl.glBlendEquation(bgl.GL_FUNC_ADD)

    group_script, group_images_to_load, group_images_to_link, group_hashes = node_converter.node_groups_to_script(sorted_nodes)
    # node_tree_owner is the material, world etc. that contains the node_tree
    node_tree_owner = context.space_data.id

    # socket.links is a very expensive property to access, so we cache the link types we are interested in most in this dict
    incoming_links = {link.to_socket: link for link in node_tree.links}
    # node.name: node_creation_script, images_to_load, images_to_link
    node_scripts_cache = {}
    jobs_to_send = []

    # Set property without triggering an update
    node_tree.node_preview["update_first_part"] = not node_tree.node_preview.update_first_part
    # The nodes near the end of the list take the most time to convert, so we divide the list unevenly to get balanced execution times
    divider = int(len(sorted_nodes) * 0.82)
    if len(sorted_nodes) < 50:
        start = 0
        end = len(sorted_nodes)
    elif node_tree.node_preview.update_first_part:
        start = 0
        end = divider
        # context.region.tag_redraw()  # TODO needed?
    else:
        start = divider
        end = len(sorted_nodes)

    for node in sorted_nodes[start:end]:
        if not is_node_supported(node):
            continue

        try:
            # Even if the preview is disabled, we need to convert the script so dependent nodes can retrieve it from the node scripts cache
            node_script, images_to_load, images_to_link = node_to_script(node, node_tree, node_tree_owner, node_scripts_cache,
                                                                         group_hashes, incoming_links, background_colors)
        except UnsupportedNodeException:
            continue

        enabled = node.node_preview.enabled if node.node_preview.enabled_modified else enabled_by_default
        if not enabled:
            continue

        scene_script = scene_converter.scene_to_script(context, needs_more_than_1_sample(node), thumb_resolution)
        script_hash = hash(node_script)
        node_key = make_node_key(node, node_tree, node_tree_owner)

        if node_key not in cached_nodes or cached_nodes[node_key][0] != script_hash:
            timestamp = time()
            thumb_path = join_paths(temp_dir, to_valid_filename(node_key) + ".png")

            if getattr(node, "image", None):
                # This info is used to show accurate error messages when images failed to link or load
                image = node.image
                image_info = (
                    make_unique_image_name(image),
                    needs_linking(image),
                    bpy.path.abspath(image.filepath, library=image.library),
                )
            else:
                image_info = None

            job = (
                node_key,
                "\n".join((scene_script, group_script, node_script)),
                images_to_load | group_images_to_load,
                images_to_link | group_images_to_link,
                image_info,
                get_blend_abspath(),
                thumb_path,
                thumb_resolution,
                timestamp,
            )
            jobs_to_send.append(job)
            cached_nodes[node_key] = script_hash, timestamp

            # For debugging complex scripts
            # if False and node.name == "Math":
            #     test_file_path = join_paths(current_dir, "data", "script.py")
            #     with open(test_file_path, "w") as f:
            #         f.write("\n".join(("import bpy; import mathutils; ", scene_script, group_script, node_script)))
            #
            #     process_args = [
            #         bpy.app.binary_path,
            #         "--factory-startup",
            #         join_paths(current_dir, "data", "previewscene.blend"),
            #         "--python", test_file_path,
            #     ]
            #     subprocess.Popen(process_args)

    for node in sorted_nodes:
        if not is_node_supported(node):
            continue

        enabled = node.node_preview.enabled if node.node_preview.enabled_modified else enabled_by_default
        if not enabled:
            continue

        location = node.location.copy()
        n = node
        while n.parent:
            # Take (possibly nested) frames into account
            location += n.parent.location
            n = n.parent

        topleft_x, topleft_y = view_to_region_scaled(context, *location, clip=False)
        topright_x, _ = view_to_region_scaled(context, location[0] + node.width, 0, clip=False)
        node_width = (topright_x - topleft_x)

        BASE_WIDTH = 150
        size = BASE_WIDTH * scaled_zoom * thumb_scale
        offset_x = (node_width - size) / 2 + 1  # For some reason we are one pixel too far to the left, thus +1
        offset_y = 5 * scaled_zoom * thumb_scale  # Some vertical offset from the node

        bottom_left = (topleft_x + offset_x, topleft_y + offset_y)
        bottom_right = (topleft_x + offset_x + size, topleft_y + offset_y)
        top_right = (topleft_x + offset_x + size, topleft_y + offset_y + size)
        top_left = (topleft_x + offset_x, topleft_y + offset_y + size)

        # Don't draw the texture when it is out of bounds
        if bottom_right[0] < 0 or bottom_left[0] > area.width or top_left[1] < 0 or bottom_left[1] > area.height:
            continue

        try:
            node_key = make_node_key(node, node_tree, node_tree_owner)
            thumb = thumbnails[node_key]
        except KeyError:
            thumb = None

        if thumb is None or thumb.buffer is None:
            continue

        if not thumb.texture_initialized:
            thumb.load_texture()

        thumb.draw(bottom_left, bottom_right, top_right, top_left, scaled_zoom)

        text_x = topleft_x
        text_y = top_left[1] + 3 * scaled_zoom
        text_size = 10

        if not node.node_preview.auto_choose_output:
            output = node.outputs[node.node_preview.output_index].name
            text_y = draw_text(f"Output: {output}", (text_x, text_y), text_size, scaled_zoom)
            text_y += text_size * scaled_zoom * 0.5  # A bit of spacing in case of more text after

        if preferences.show_help and "Scale" in node.inputs:
            try:
                threshold = SCALE_HELP_THRESHOLDS[node.bl_idname]
                if node.inputs["Scale"].is_linked or abs(node.inputs["Scale"].default_value) > threshold:
                    if node.node_preview.ignore_scale:
                        text_y = draw_text("Scale ignored", (text_x, text_y), text_size, scaled_zoom)
                    else:
                        text_y = draw_text("Scale can be ignored\nwith Ctrl+Shift+i", (text_x, text_y), text_size, scaled_zoom)
            except KeyError:
                # Node doesn't have a known scale threshold, don't show the help message
                pass

    bgl.glBindTexture(bgl.GL_TEXTURE_2D, NULL)
    bgl.glDisable(bgl.GL_BLEND)

    # Send jobs in reversed order so the leftmost node (which was edited) is rendered first for fast feedback
    for job in reversed(jobs_to_send):
        connection.send((messages.NEW_JOB, job))

    delete_old_textures_if_necessary()

    # elapsed = perf_counter() - __start
    # print("1st" if node_tree.node_preview.update_first_part else "2nd", "draw handler took %.3f s (%d fps)" % (elapsed, round(1 / elapsed)))
    # draw_text("Node Preview Frametime: %.3f s (%d FPS)" % (elapsed, round(1 / elapsed)), (30, 30), 15, 1)


def free():
    cached_nodes.clear()

    texture_count = len(thumbnails)

    if texture_count > 0:
        texture_ids = bgl.Buffer(bgl.GL_INT, [texture_count])
        for i, thumb in enumerate(thumbnails.values()):
            texture_ids[i] = thumb.texture_id
        bgl.glDeleteTextures(texture_count, texture_ids)
        thumbnails.clear()


def stop_threads_and_process():
    global watcher_thread, connection, listener, background_process, background_process_ready
    background_process_ready = False

    if watcher_thread:
        watcher_thread.stop()
        watcher_thread.join()
        watcher_thread = None

    if connection:
        connection.send((messages.STOP, None))
        connection.close()
        connection = None

    if listener:
        listener.close()
        listener = None

    if background_process:
        try:
            background_process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            background_process.kill()
            background_process.communicate()
            addon_print("Background Process was killed after timeout.")

        background_process = None


def clean_temp_dir():
    os_temp_dir = os.path.dirname(temp_dir)
    addon_temp_dirs = [join_paths(os_temp_dir, name) for name in os.listdir(os_temp_dir)
                       if re.match(TEMP_DIR_REGEX_PATTERN, name)]

    for path in addon_temp_dirs:
        try:
            # Only delete old temp dirs. Recent ones might still be in use by another Blender process.
            seconds_since_last_modification = time() - os.path.getmtime(path)
            if seconds_since_last_modification > 60 * 60 * 24:
                shutil.rmtree(path)
        except Exception as error:
            addon_print("Could not delete temp dir:", path)
            addon_print(error)


@persistent
def load_pre(_=None):
    free()
    # Delete images in the background process to free up RAM
    if background_process_ready:
        connection.send((messages.FREE_RESSOURCES, None))

@persistent
def load_post(arg1, arg2):
    def notify_new_blend_loaded():
        while not background_process_ready:
            sleep(1/60)
        connection.send((messages.NEW_BLEND_ABSPATH, bpy.path.abspath(bpy.data.filepath)))

    if background_process_ready:
        notify_new_blend_loaded()
    else:
        # Wait until the process is ready to receive the message, because it must
        # arrive, otherwise all future jobs will be ignored
        notifier = threading.Thread(target=notify_new_blend_loaded)
        notifier.setDaemon(True)
        notifier.start()


@persistent
def save_post(arg1, arg2):
    with images_failed_to_link_lock:
        if images_failed_to_link:
            for mat in bpy.data.materials:
                if not mat.node_tree:
                    continue
                for node in mat.node_tree.nodes:
                    if getattr(node, "image", None) and node.image.name in images_failed_to_link:
                        node.node_preview.force_update()

            for node_tree in bpy.data.node_groups:
                if node_tree.bl_idname not in SUPPORTED_NODE_TREE:
                    continue
                for node in node_tree.nodes:
                    if getattr(node, "image", None) and node.image.name in images_failed_to_link:
                        node.node_preview.force_update()

        force_node_editor_draw()
        images_failed_to_link.clear()


def exit_callback():
    stop_threads_and_process()
    free()
    clean_temp_dir()


def start_background_process():
    authkey = current_process().authkey
    global listener

    port = 6000
    while port < 10000:
        try:
            listener = Listener(('localhost', port), authkey=authkey)
            break
        except OSError as error:
            if ((platform.system() == "Windows" and error.errno == 10048)
                or (platform.system() == "Linux" and error.errno == 98)
                or (platform.system() == "Darwin" and error.errno == 48)):
                # Windows: [WinError 10048] Only one usage of each socket address (protocol/network address/port) is normally permitted
                # Linux: [Errno 98] Address already in use
                # macOS: [Errno 48] Address already in use
                port += 1
            else:
                raise

    global background_process
    process_args = [
        bpy.app.binary_path,
        "--factory-startup",
        "--addons", f"{addon_name},io_import_images_as_planes",  # Without images as planes, bpy_extras doesn't contain the image_utils submodule
        "-b",  # Run in background without UI
        join_paths(current_dir, "data", "previewscene.blend"),
        "--python-expr", f"import {addon_name}; {addon_name}.background.run({port}, {authkey})",
    ]

    env_copy = os.environ.copy()
    custom_script_dir = bpy.context.preferences.filepaths.script_directory
    # Only use the custom script dir if the addon is installed there. If BLENDER_USER_SCRIPTS is set, but the addon
    # is installed in the default location, the background process will fail to import the addon.
    if custom_script_dir and os.path.exists(join_paths(custom_script_dir, "addons", addon_name)):
        env_copy["BLENDER_USER_SCRIPTS"] = bpy.context.preferences.filepaths.script_directory

    enable_debug_output = bpy.context.preferences.addons[addon_name].preferences.enable_debug_output
    if enable_debug_output:
        background_process = subprocess.Popen(process_args, env=env_copy)
    else:
        background_process = subprocess.Popen(process_args, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=env_copy)

    global connection
    connection = listener.accept()

    global watcher_thread
    watcher_thread = WatcherThread()
    watcher_thread.setDaemon(True)
    watcher_thread.start()


def display_register():
    import atexit
    # Make sure we only register the callback once
    atexit.unregister(exit_callback)
    atexit.register(exit_callback)

    handler_args = ()
    global handle
    # Note: not using "BACKDROP" because the thumbnails would be behind frames in that mode
    handle = SpaceNodeEditor.draw_handler_add(handler, handler_args, "WINDOW", "POST_PIXEL")

    bpy.app.handlers.load_pre.append(load_pre)
    bpy.app.handlers.load_post.append(load_post)
    bpy.app.handlers.save_post.append(save_post)

    process_starter = threading.Thread(target=start_background_process)
    # In case the background process throws an exception, the process_starter thread could get stuck
    # on listener.accept(). Enable the daemon flag to make sure the Blender process doesn't hang after
    # quit when this happens.
    process_starter.setDaemon(True)
    process_starter.start()


def display_unregister():
    SpaceNodeEditor.draw_handler_remove(handle, "WINDOW")
    bpy.app.handlers.load_pre.remove(load_pre)
    bpy.app.handlers.load_post.remove(load_post)
    bpy.app.handlers.save_post.remove(save_post)
    free()
    stop_threads_and_process()
