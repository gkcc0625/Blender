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
from mathutils import Color, Vector, Euler

import re

from . import needs_linking, UnsupportedNodeException, is_group_node
from . import nodepreview_worker


IGNORED_NODE_ATTRIBUTES = {
    "color",
    "dimensions",
    "width",
    "width_hidden",
    "height",
    "hide",
    "label",
    "location",
    "name",
    "select",
    "show_options",
    "show_preview",
    "show_texture",
    "type",
    "use_custom_color",
    "image",  # Handled by special code
    "node_tree",  # Handled by special code
    "inputs",
    "internal_links",
    "outputs",
    "parent",
    "rna_type",
    "node_preview",  # Only used in display.py, not in the background thread
}

node_attributes_cache = {}


def make_node_key(node, node_tree, material):
    return node.name + make_unique_name(node_tree) + make_unique_name(material)


def sort_topologically(nodes, get_dependent_nodes):
    # Depth-first search from https://en.wikipedia.org/wiki/Topological_sorting
    sorted_nodes = []
    temporary_marks = set()
    permanent_marks = set()
    unmarked_nodes = list(nodes)

    def visit(node):
        if node in permanent_marks:
            return

        temporary_marks.add(node)

        for subnode in get_dependent_nodes(node):
            visit(subnode)

        temporary_marks.remove(node)
        permanent_marks.add(node)
        unmarked_nodes.remove(node)
        sorted_nodes.insert(0, node)

    while unmarked_nodes:
        visit(unmarked_nodes[0])

    return sorted_nodes


def _get_attributes(source, ignore_list):
    return [attr for attr in dir(source)
            if not callable(getattr(source, attr))
            and not attr.startswith("__")
            and not attr.startswith("bl_")
            and not attr in ignore_list]


def build_node_attributes_cache():
    node_tree = bpy.data.node_groups.new(".NodePreviewTempTree", "ShaderNodeTree")

    for type_str in dir(bpy.types):
        if type_str.startswith("__"):
            continue

        if issubclass(getattr(bpy.types, type_str), bpy.types.ShaderNode):
            try:
                node = node_tree.nodes.new(type_str)
                node_attributes_cache[type_str] = _get_attributes(node, IGNORED_NODE_ATTRIBUTES)
            except:
                # Some classes like ShaderNode or node groups can't be instanced
                pass

    def register(type_str):
        node = node_tree.nodes.new(type_str)
        node_attributes_cache[type_str] = _get_attributes(node, IGNORED_NODE_ATTRIBUTES)

    register("NodeGroupInput")
    register("NodeGroupOutput")
    register("NodeReroute")
    register("NodeFrame")

    # Ignore named UV maps. Since they never exist on the preview mesh, they would make the UV output black
    uvmap_attributes = node_attributes_cache["ShaderNodeUVMap"]
    uvmap_attributes.remove("from_instancer")
    uvmap_attributes.remove("uv_map")

    bpy.data.node_groups.remove(node_tree)


def node_to_script(node, node_tree, material, node_scripts_cache, group_hashes, incoming_links, background_colors):
    script = [
        "node_tree = bpy.data.materials['Material'].node_tree",
        "output_node = node_tree.nodes['Material Output']",
        # Background color settings
        "background_tex = bpy.data.materials['checker_plane'].node_tree.nodes['Checker Texture']",
        "background_tex.inputs[1].default_value = " + str(background_colors[0]),
        "background_tex.inputs[2].default_value = " + str(background_colors[1]),
    ]

    images_to_load = set()
    images_to_link = set()

    node_name, node_script = _node_to_script_recursive(node, node_tree, material, images_to_load, images_to_link, node_scripts_cache, group_hashes, incoming_links)
    script += node_script

    outputs = node.outputs

    # Link the node
    # TODO allow to cycle through (used?) outputs, for example by setting a property on the node
    first_enabled = _find_first_enabled_socket(outputs)
    output_index = _find_first_linked_socket(outputs, fallback=first_enabled)

    if outputs[output_index].name == "Volume":
        input_index = 1
    else:
        input_index = 0

    script.append(f"node_tree.links.new({node_name}.outputs[{output_index}], output_node.inputs[{input_index}])")

    # print("--- script: ---")
    # print("\n".join(script))
    # print("---------------")
    return "\n".join(script), images_to_load, images_to_link


def _socket_interfaces_to_script(socket_interfaces, attr_name, script):
    for socket_interface in socket_interfaces:
        script.append(f"socket = node_tree.{attr_name}.new({repr(socket_interface.bl_socket_idname)}, {repr(socket_interface.name)})")

        if hasattr(socket_interface, "default_value"):
            value, success = _property_to_string(socket_interface.default_value)
            if success:
                script.append(f"socket.default_value = {value}")
            else:
                print("Conversion of default_value failed:", socket_interface.name,
                      socket_interface.default_value)


class AnnotatedNodeGroup:
    def __init__(self, group):
        self.group = group
        self.dependent_groups = set()


def node_groups_to_script(nodes):
    # Only set up the groups actually used in this list of nodes
    def find_groups_recursive(nodes, groups):
        for node in nodes:
            if is_group_node(node) and node.node_tree:
                groups.add(node.node_tree)
                find_groups_recursive(node.node_tree.nodes, groups)
    groups = set()
    find_groups_recursive(nodes, groups)

    # Build a DAG structure of groups and their dependent groups
    annotated_groups = {group: AnnotatedNodeGroup(group) for group in groups}
    for group in groups:
        for node in group.nodes:
            if is_group_node(node) and node.node_tree:
                annotated_groups[node.node_tree].dependent_groups.add(annotated_groups[group])

    # Make sure that groups that other groups depend on are evaluated first
    def get_dependent_groups(annotated_group):
        return annotated_group.dependent_groups
    sorted_groups = sort_topologically(annotated_groups.values(), get_dependent_groups)

    script = ["node_group_mapping = {}"]
    images_to_load = set()
    images_to_link = set()
    group_hashes = {}
    for annotated_group in sorted_groups:
        group = annotated_group.group
        unique_name = make_unique_name(group)
        group_script = []
        # Note: max length for node group names in Blender is 63 characters
        group_script.append(f"node_tree = bpy.data.node_groups.new({repr(unique_name)}, 'ShaderNodeTree')")
        # This is used in node group instances to set the correct node_tree for the instance node
        group_script.append(f"node_group_mapping[{repr(unique_name)}] = node_tree")

        # Create group inputs and outputs
        _socket_interfaces_to_script(group.inputs, "inputs", group_script)
        _socket_interfaces_to_script(group.outputs, "outputs", group_script)

        for node in group.nodes:
            _, node_script = _single_node_to_script(node, images_to_load, images_to_link, group_hashes)
            group_script += node_script

        # Create all links
        for source_node_index, source_node in enumerate(group.nodes):
            for source_socket_index, source_socket in enumerate(source_node.outputs):
                for link in source_socket.links:
                    target_node_index = group.nodes.find(link.to_node.name)
                    if target_node_index == -1:
                        raise Exception(f"Could not find target node: {link.to_node.name} in node group: {group.name}")

                    # Can't use find here because a node can have multiple sockets with the same name
                    target_socket_index = -1
                    for i, socket in enumerate(link.to_node.inputs):
                        if socket == link.to_socket:
                            target_socket_index = i
                            break
                    if target_socket_index == -1:
                        raise Exception(f"Could not find target socket: {link.to_socket.name} in node group: {group.name}")

                    group_script.append(f"node_tree.links.new(node_tree.nodes[{source_node_index}].outputs[{source_socket_index}], "
                                                            f"node_tree.nodes[{target_node_index}].inputs[{target_socket_index}])")

        group_script_joined = "\n".join(group_script)
        script.append(group_script_joined)
        group_hashes[unique_name] = hash(group_script_joined)

    return "\n".join(script), images_to_load, images_to_link, group_hashes


def _attributes_to_script(attributes, source, target_identifier, script):
    for attr in attributes:
        value, success = _property_to_string(getattr(source, attr))
        if success:
            # TODO is the try/except still needed?
            script.append(
f"""try:
    {target_identifier}.{attr} = {value}
except Exception:
    pass""")


def make_unique_name(datablock):
    # TODO what about long image/lib names? Blender names have a max length of 63 characters!
    return datablock.name + (datablock.library.name if datablock.library else "")


def _node_properties_to_script(node, node_name, script, images_to_load, images_to_link, group_hashes):
    _is_group_node = is_group_node(node)

    try:
        attributes = node_attributes_cache[node.bl_idname]
    except KeyError:
        if _is_group_node:
            # It is most likely a custom node with an internal node group.
            # Put it in the attributes cache and treat it like a group node.
            attributes = _get_attributes(node, IGNORED_NODE_ATTRIBUTES)
            node_attributes_cache[node.bl_idname] = attributes
        else:
            raise UnsupportedNodeException(f"Unsupported node type: {node.bl_idname}")

    # A change of the counter causes a change in the script hash, which
    # automatically updates this node and all dependent nodes
    script.append(f"# {node.node_preview.force_update_counter}")

    _attributes_to_script(attributes, node, node_name, script)

    if getattr(node, "image", None):
        image = node.image
        unique_name = make_unique_name(image)

        if needs_linking(image):
            # TODO handle case where image is from a library and the name collides with another image
            images_to_link.add(image.name)

        # Try to load the image even if we're linking it, as fallback in case the linking fails
        # (e.g. because the image was just packed, but the .blend was not saved yet)
        abspath = bpy.path.abspath(image.filepath, library=image.library)
        images_to_load.add((unique_name, abspath))

        # TODO what about image sequences/other image user settings?
        image_datablock_name = repr(unique_name)
        # The path is part of the script so a change of the path triggers an update through the script hash
        script.append(f"# {abspath}")
        script.append("try:")
        script.append(f"    image = bpy.data.images[{image_datablock_name}]")
        script.append(f"    {node_name}.image = image")
        script.append("except:")
        script.append(f'    print("failed to find image {image_datablock_name}")')

        # script.append(f"image.colorspace_settings.name = '{image.colorspace_settings.name}'")  # TODO doesn't work

    # Special properties: color ramp
    if hasattr(node, "color_ramp"):
        ramp = node.color_ramp
        _attributes_to_script(_get_attributes(ramp, []), ramp, f"{node_name}.color_ramp", script)

        # Ramp has two elements by default, but user might have deleted one, so remove it
        script.append(f"{node_name}.color_ramp.elements.remove({node_name}.color_ramp.elements[0])")
        # Then re-add as many elements as needed
        for i in range(len(ramp.elements) - 1):
            script.append(f"{node_name}.color_ramp.elements.new(0)")

        for i in range(len(ramp.elements)):
            script.append(f"{node_name}.color_ramp.elements[{i}].position = {ramp.elements[i].position}")
            color, _ = _property_to_string(ramp.elements[i].color)
            script.append(f"{node_name}.color_ramp.elements[{i}].color = {color}")

    # Special properties: RGB curve
    if node.bl_idname == "ShaderNodeRGBCurve":
        mapping = node.mapping
        _attributes_to_script(_get_attributes(mapping, []), mapping, f"{node_name}.mapping", script)

        for curve_index, curve in enumerate(mapping.curves):
            # Curves have 2 points by default, and a minimum of 2, so we ignore the first 2 points here
            for i in range(2, len(curve.points)):
                script.append(f"{node_name}.mapping.curves[{curve_index}].points.new(0, 0)")

            for point_index, point in enumerate(curve.points):
                handle_type, _ = _property_to_string(point.handle_type)
                script.append(
                    f"{node_name}.mapping.curves[{curve_index}].points[{point_index}].handle_type = {handle_type}")
                location, _ = _property_to_string(point.location)
                script.append(f"{node_name}.mapping.curves[{curve_index}].points[{point_index}].location = {location}")
    elif _is_group_node and node.node_tree:
        group_name = make_unique_name(node.node_tree)
        # The hash over the node group script is appended as a comment here so the node script hash changes
        # when the group hash changes, to flag this node for updating
        script.append(f"{node_name}.node_tree = node_group_mapping[{repr(group_name)}]  # {group_hashes[group_name]}")


def _node_outputs_to_script(node, node_name, script):
    if node.bl_idname == "NodeReroute":
        return

    for i, socket in enumerate(node.outputs):
        if hasattr(socket, "default_value"):
            value, success = _property_to_string(socket.default_value)
            if success:
                script.append(f"{node_name}.outputs[{i}].default_value = {value}")
            else:
                print("Conversion of default_value failed:", node, socket.name, socket.default_value)


def _single_node_to_script(node, images_to_load, images_to_link, group_hashes):
    """ Used in node group conversion. Only creates a single node without evaluating linked nodes. """
    node_name = re.sub("[^_0-9a-zA-Z]+", "__", node.name)
    bl_idname = "ShaderNodeGroup" if is_group_node(node) else node.bl_idname
    script = [f"{node_name} = node_tree.nodes.new('{bl_idname}')"]

    # Properties
    _node_properties_to_script(node, node_name, script, images_to_load, images_to_link, group_hashes)

    # Input sockets
    for i, socket in enumerate(node.inputs):
        if socket.name == "Scale" and node.node_preview.ignore_scale:
            continue

        if not socket.is_linked and hasattr(socket, "default_value"):
            value, success = _property_to_string(socket.default_value)
            if success:
                script.append(f"{node_name}.inputs[{i}].default_value = {value}")
            else:
                print("Conversion of default_value failed:", node, socket.name, socket.default_value)

    # Output sockets (used on nodes like Value or RGB)
    _node_outputs_to_script(node, node_name, script)

    return node_name, script


def _get_link_skipping_reroutes(socket, incoming_links):
    link = incoming_links[socket]

    while link.from_node.bl_idname == "NodeReroute":
        reroute_input = link.from_node.inputs[0]
        if reroute_input.is_linked:
            link = incoming_links[reroute_input]
        else:
            # If the left-most reroute has no input, it is like self.is_linked == False
            return None
    return link


def _node_to_script_recursive(node, node_tree, material, images_to_load, images_to_link, node_scripts_cache, group_hashes, incoming_links):
    # Inside a node tree, the name is unique
    # Note: name collisions aren't allowed to happen between this node and nodes linked to it
    node_name = nodepreview_worker.to_valid_identifier(node.name)
    bl_idname = "ShaderNodeGroup" if is_group_node(node) else node.bl_idname
    script = [f"{node_name} = node_tree.nodes.new('{bl_idname}')"]

    # Properties
    _node_properties_to_script(node, node_name, script, images_to_load, images_to_link, group_hashes)

    # Input sockets
    for i, socket in enumerate(node.inputs):
        if socket.name == "Scale" and node.node_preview.ignore_scale:
            continue

        if socket.is_linked:
            link = _get_link_skipping_reroutes(socket, incoming_links)
            if link and link.from_node.bl_idname != "NodeGroupInput":
                try:
                    sub_name, sub_script, sub_images_to_load, sub_images_to_link = node_scripts_cache[make_node_key(link.from_node, node_tree, material)]
                    script += sub_script
                    images_to_load.update(sub_images_to_load)
                    images_to_link.update(sub_images_to_link)
                    # I'm assuming here that a node never has two or more outputs with the same name
                    script.append(f"node_tree.links.new({sub_name}.outputs[{repr(link.from_socket.name)}], {node_name}.inputs[{i}])")
                except KeyError:
                    # link.from_node is an unsupported node and was not stored in the node_scripts_cache
                    pass
        elif hasattr(socket, "default_value"):
            value, success = _property_to_string(socket.default_value)
            if success:
                script.append(f"{node_name}.inputs[{i}].default_value = {value}")
            else:
                print("Conversion of default_value failed:", node, socket.name, socket.default_value)

    # Output sockets (used on nodes like Value or RGB)
    _node_outputs_to_script(node, node_name, script)

    node_scripts_cache[make_node_key(node, node_tree, material)] = node_name, script, images_to_load, images_to_link
    return node_name, script


def _property_to_string(prop):
    if isinstance(prop, (Color, Vector, bpy.types.bpy_prop_array)):
        return str(list(prop)), True
    elif isinstance(prop, (float, int)):
        return str(prop), True
    elif isinstance(prop, str):
        return repr(prop), True
    elif isinstance(prop, Euler):
        return f"mathutils.Euler({list(prop)}, '{prop.order}')", True

    return None, False


def _find_first_enabled_socket(outputs, fallback=0):
    for i, socket in enumerate(outputs):
        if socket.enabled:
            return i
    return fallback


def _find_first_linked_socket(outputs, fallback):
    for i, socket in enumerate(outputs):
        if socket.enabled and socket.is_linked:
            return i
    return fallback
