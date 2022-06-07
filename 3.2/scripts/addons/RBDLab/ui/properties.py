import bpy
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, BoolProperty, FloatProperty, StringProperty, IntProperty, FloatVectorProperty
from ..core.functions import encode_string
from ..core.update_functions import subdiv_update, part_count, part_second_count, target_collection_update, \
    scatter_type_update, mass_delimiter_by_mass_update, size_delimiter_update, auto_smooth_update, \
    show_emitter_viewport_update, show_emitter_render_update, explode_slider_update, colorize_update, show_boundingbox_update


class RBDLabProps(PropertyGroup):
    las_active_tool: StringProperty(default='builtin.select_box')
    in_annotation_mode: BoolProperty(default=False)

    target_collection: StringProperty(
        update=target_collection_update
    )

    collision_shapes = [
        ("CONVEX_HULL", "Convex Hull", "", 0),
        ("MESH", "Mesh", "", 1)
    ]
    collision_shape_combobox: EnumProperty(
        items=collision_shapes,
        name="Collision Shape",
        description="Type of collision shape",
        default="CONVEX_HULL"
    )
    use_collision_margin: BoolProperty(
        default=True,
    )
    collision_margin: FloatProperty(
        default=0.00010,
        min=0.00000,
        max=1,
        precision=5,
        name="Collision Margin",
    )
    string_items = [
        "Air",
        "Acrylic",
        "Asphalt (Crushed)",
        "Bark",
        "Beans (Cocoa)",
        "Beans (Soy)",
        "Brick (Pressed)",
        "Brick (Common)",
        "Brick (Soft)",
        "Brass",
        "Bronze",
        "Carbon (Solid)",
        "Cardboard",
        "Cast Iron",
        "Chalk (Solid)",
        "Concrete",
        "Charcoal",
        "Cork",
        "Copper",
        "Garbage",
        "Glass (Broken)",
        "Glass (Solid)",
        "Gold",
        "Granite (Broken)",
        "Granite (Solid)",
        "Gravel",
        "Ice (Crushed)",
        "Ice (Solid)",
        "Iron",
        "Lead",
        "Limestone (Broken)",
        "Limestone (Solid)",
        "Marble (Broken)",
        "Marble (Solid)",
        "Paper",
        "Peanuts (Shelled)",
        "Peanuts (Not Shelled)",
        "Plaster",
        "Plastic",
        "Polystyrene",
        "Rubber",
        "Silver",
        "Steel",
        "Stone",
        "Stone (Crushed)",
        "Timber",
    ]

    items = []
    for i, item in enumerate(string_items):
        row = (encode_string(item), item, "", i)
        items.append(row)

    avalidable_mass: EnumProperty(
        items=items,
        name="avalidable_mass",
        description="Item",
        default=encode_string("Concrete")
    )
    dynamic: BoolProperty(
        default=True
    )
    breakable: BoolProperty(
        default=True
    )
    glue_strength: FloatProperty(
        default=100.0
    )
    override_iterations: BoolProperty(
        default=True
    )
    iterations: IntProperty(
        default=100,
        min=1,
        max=100
    )
    glue_island_or_default: BoolProperty(
        default=False,
        description='To make the allocation of constraints per island (by name of each object)'
    )
    deactivation: BoolProperty(
        default=False
    )
    d_translation: FloatProperty(
        default=0.1,
        min=0,
        max=1
    )
    d_rotation: FloatProperty(
        default=0.5,
        min=0,
        max=1
    )
    rb_friction: FloatProperty(
        default=0.5,
        min=0,
        max=1
    )

    particle_count: IntProperty(
        default=30,
        min=7,
        update=part_count
    )
    particle_secondary_count: IntProperty(
        default=30,
        min=7,
        update=part_second_count
    )
    subdivision_level: IntProperty(
        default=0,
        min=0,
        max=6,
        update=subdiv_update
    )
    subdivision_simple: BoolProperty(
        default=False,
        update = subdiv_update
    )
    size_delimiter: FloatProperty(
        default=0.12,
        min=0,
        update=size_delimiter_update
    )
    mass_delimiter: FloatProperty(
        default=1,
        min=0,
        precision=6,
        update=mass_delimiter_by_mass_update
    )
    chunks_selected: IntProperty(
        default=0
    )
    smoke_density: FloatProperty(
        default=1.0,
        min=0.0,
        max=1.0,
        precision=4,
        options={'ANIMATABLE'}
    )
    iter_seed: IntProperty(
        default=0
    )
    use_auto_smooth: BoolProperty(
        default=False,
        update=auto_smooth_update
    )
    auto_smooth: FloatProperty(
        default=0.523599,
        min=0.0,
        max=3.141593,
        subtype='ANGLE',
        update=auto_smooth_update
    )
    scatter_types = [
        ("VOLUME", "Volume", "", 0),
        ("VERT", "Vertex", "", 1),
        ("FACE", "Faces", "", 2)
    ]
    scatter_types_combobox: EnumProperty(
        items=scatter_types,
        name="scatter_type",
        description="Type of scatter",
        update=scatter_type_update
    )

    ######################################################################################
    # particles
    ######################################################################################
    show_emitter_viewport: BoolProperty(
        default=True,
        update=show_emitter_viewport_update
    )
    show_emitter_render: BoolProperty(
        default=True,
        update=show_emitter_render_update
    )
    ps_debris_type = [
        ("VOLUME", "Volume", "", 0),
        ("VERT", "Vertex", "", 1),
        ("FACE", "Faces", "", 2)
    ]
    ps_debris_type_combobox: EnumProperty(
        items=ps_debris_type,
        name="Emit From",
        default="FACE"
    )
    ps_dust_type = [
        ("VOLUME", "Volume", "", 0),
        ("VERT", "Vertex", "", 1),
        ("FACE", "Faces", "", 2)
    ]
    ps_dust_type_combobox: EnumProperty(
        items=ps_dust_type,
        name="Emit From",
        default="FACE"
    )
    ps_smoke_type = [
        ("VOLUME", "Volume", "", 0),
        ("VERT", "Vertex", "", 1),
        ("FACE", "Faces", "", 2)
    ]
    ps_smoke_type_combobox: EnumProperty(
        items=ps_smoke_type,
        name="Emit From",
        default="FACE"
    )

    debris_count: IntProperty(
        default=15
    )
    dust_count: IntProperty(
        default=150
    )
    smoke_count: IntProperty(
        default=10
    )

    ps_from = [
        ("BROKEN", "Broken", "", 0),
        ("ALLCHUNKS", "All Chunks", "", 1)
    ]
    ps_debris_from: EnumProperty(
        items=ps_from,
        name="Emit From",
        description="Emit from"
    )
    ps_dust_from: EnumProperty(
        items=ps_from,
        name="Emit From",
        description="Emit from"
    )
    ps_smoke_from: EnumProperty(
        items=ps_from,
        name="Emit From",
        description="Emit from"
    )

    ######################################################################################
    # Cell Fracture properties
    ######################################################################################
    post_original_options = [
        ("HIDE", "Hide", "", 0),
        ("REMOVE", "Remove", "", 1),
    ]
    post_original: EnumProperty(
        items=post_original_options,
        name="Post Fracture Action",
        description="Action for original object",
        default="HIDE"
    )
    rbdlab_cf_source: EnumProperty(
        name="Source",
        items=(
            ('VERT_OWN', "Own Verts", "Use own vertices"),
            ('VERT_CHILD', "Child Verts", "Use child object vertices"),
            ('PARTICLE_OWN', "Own Particles", (
                "All particle systems of the "
                "source object"
            )),
            ('PARTICLE_CHILD', "Child Particles", (
                "All particle systems of the "
                "child objects"
            )),
            ('PENCIL', "Annotation Pencil", "Annotation Grease Pencil."),
        ),
        options={'ENUM_FLAG'},
        default={'PARTICLE_OWN'},
    )
    # max chunks:
    rbdlab_cf_source_limit: IntProperty(
        default=0,
        min=0,
        max=5000,
        name="Max Chunks",
        description="Limit the number of Chunks (Source Limit in Cell Fracture), 0 for unlimited",
    )
    rbdlab_cf_noise: FloatProperty(
        default=0.05,
        min=0.0,
        max=1.0,
        name="Noise",
        description="Randomize point distribution",
    )
    rbdlab_cf_cell_scale: FloatVectorProperty(
        name="Scale",
        description="Scale Cell Shape",
        size=3,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0),
        subtype='XYZ'
    )
    rbdlab_cf_recursion: IntProperty(
        name="Recursion",
        description="Break shards recursively",
        min=0, max=5000,
        default=0,
    )
    rbdlab_cf_recursion_source_limit: IntProperty(
        name="Source Limit",
        description="Limit the number of input points, 0 for unlimited (applies to recursion only)",
        min=0, max=5000,
        default=8,
    )
    rbdlab_cf_recursion_clamp: IntProperty(
        name="Clamp Recursion",
        description=(
            "Finish recursion when this number of objects is reached "
            "(prevents recursing for extended periods of time), zero disables"
        ),
        min=0, max=10000,
        default=250,
    )
    rbdlab_cf_recursion_chance: FloatProperty(
        name="Random Factor",
        description="Likelihood of recursion",
        min=0.0, max=1.0,
        default=0.25,
    )
    rbdlab_cf_recursion_chance_select: EnumProperty(
        name="Recurse Over",
        items=(
            ('RANDOM', "Random", ""),
            ('SIZE_MIN', "Small", "Recursively subdivide smaller objects"),
            ('CURSOR_MIN', "Cursor Close", "Recursively subdivide objects closer to the cursor"),
            ('SIZE_MAX', "Big", "Recursively subdivide bigger objects"),
        ),
        default='SIZE_MIN',
    )
    rbdlab_cf_use_sharp_edges_apply: BoolProperty(
        name="Apply Split Edge",
        description="Split sharp hard edges",
        default=True,
    )
    rbdlab_cf_margin: FloatProperty(
        name="Margin",
        description="Gaps for the fracture (gives more stable physics)",
        min=0.0,
        max=1.0,
        # default=0.001,
        default=0.00001,
    )
    rbdlab_cf_collection_name: StringProperty(
        name="Collection",
        description=(
            "Create objects in a collection "
            "(use existing or create new)"
        ),
    )
    optinoal_auto_name: BoolProperty(
        default=True
    )

    # EXPLODE
    explode_slider: IntProperty(
        default=0,
        min=0,
        update=explode_slider_update
    )
    exploding: BoolProperty(
        default=False
    )
    colorize: BoolProperty(
        default=True,
        update=colorize_update
    )

    show_boundingbox: BoolProperty(
        default=False,
        description="Show Chunks as Bounding Box",
        update=show_boundingbox_update
    )

    def get_default_properties(self, target_prop):
        for prop in self.bl_rna.properties:
            if prop.name == target_prop:
                if hasattr(prop, "default"):
                    default = prop.default
                    return default
