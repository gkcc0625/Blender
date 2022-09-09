
bl_info = {
    "name": "RBDLab",
    "author": "Jorge Hernández-Meléndez (zebus3d), Esteban Giménez-Vega Ferramola (TebitoSan)",
    "version": (1, 0, 1),
    "blender": (2, 93, 0),
    "location": "View3D > FHelper",
    "description": "Helpers for fracture",
    "warning": "",
    "doc_url": "",
    "category": "Physics",
}

import bpy
import addon_utils
from bpy.app.handlers import persistent
from bpy.utils import register_class, unregister_class

from .ui.properties import RBDLabProps

# operators 
from .core.subdivision import SUBDIVISION_OT_surface
from .core.paint import GOTO_OT_weight_paint, CLEAR_weight_paint, GOTO_OT_anotation_paint
from .core.scatter import ACCEPT_OT_scatter
from .core.scatter import SCATTER_OT_object
from .core.fracture import CELL_FRACTURE_OT_custom
from .core.explode import EXPLODE_OT_start
from .core.explode import EXPLODE_OT_end
from .core.explode import EXPLODE_OT_restart
from .core.rigidbodies import RBD_OT_update
from .core.rigidbodies import RBD_OT_add
from .core.rigidbodies import RBD_OT_rm
from .core.rigidbodies import RBD_OT_passive
from .core.extras import GROUND_OT_add
from .core.chipping import CHIPPING_OT_to_coll
from .core.constraints import CONST_OT_update
from .core.constraints import CONST_OT_add
from .core.constraints import CONST_OT_rm
from .core.acetone import ACETONE_OT_add_helper
from .core.acetone import ACETONE_OT_recording
from .core.acetone import ACETONE_OT_clean
from .core.debris import DEBRIS_OT_add
from .core.debris import DEBRIS_OT_rm
from .core.dust import DUST_OT_add
from .core.dust import DUST_OT_rm
from .core.smoke import SMOKE_OT_add
from .core.smoke import SMOKE_OT_rm

# ui 
from .ui.panels.paint_and_subsurf import PAINT_AND_SUBSURF_PT_ui
from .ui.panels.scatter import SCATTER_PT_ui
from .ui.panels.fracture import FRACTURE_PT_ui
from .ui.panels.target_collection import TARGET_COLL_PT_ui
from .ui.panels.explode import EXPLODE_PT_ui
from .ui.panels.rigidbodies import RBD_PT_ui
from .ui.panels.ground import GROUND_PT_ui
from .ui.panels.chipping import CHIPPING_PT_ui
from .ui.panels.constraints import CONSTRAINTS_PT_ui
from .ui.panels.acetone import ACETONE_PT_ui
from .ui.panels.physics import PHYSICS_PT_ui
from .ui.panels.physics import PHYSICS_PT_substeps
from .ui.panels.physics import PHYSICS_CACHE_PT_ui
from .ui.panels.extras import EXTRAS_PT_ui
from .ui.panels.particles import PARTICLES_PT_ui
from .ui.panels.debris import PARTICLES_PT_debris
from .ui.panels.dust import PARTICLES_PT_dust
from .ui.panels.smoke import PARTICLES_PT_smoke


all_classes = [
    PAINT_AND_SUBSURF_PT_ui,
    SUBDIVISION_OT_surface,
    GOTO_OT_weight_paint,
    CLEAR_weight_paint,
    GOTO_OT_anotation_paint,
    ACCEPT_OT_scatter,
    SCATTER_OT_object,
    SCATTER_PT_ui,
    CELL_FRACTURE_OT_custom,
    FRACTURE_PT_ui,
    TARGET_COLL_PT_ui,
    EXPLODE_PT_ui,
    EXPLODE_OT_start,
    EXPLODE_OT_end,
    EXPLODE_OT_restart,
    RBD_OT_update,
    RBD_OT_add,
    RBD_OT_rm,
    RBD_OT_passive,
    GROUND_OT_add,
    RBD_PT_ui,
    GROUND_PT_ui,
    CHIPPING_OT_to_coll,
    CHIPPING_PT_ui,
    CONSTRAINTS_PT_ui,
    CONST_OT_update,
    CONST_OT_add,
    CONST_OT_rm,
    ACETONE_OT_add_helper,
    ACETONE_OT_recording,
    ACETONE_OT_clean,
    ACETONE_PT_ui,
    PHYSICS_PT_ui,
    PHYSICS_PT_substeps,
    PHYSICS_CACHE_PT_ui,
    EXTRAS_PT_ui,
    PARTICLES_PT_ui,
    PARTICLES_PT_debris,
    DEBRIS_OT_add,
    DEBRIS_OT_rm,
    DUST_OT_rm,
    DUST_OT_add,
    SMOKE_OT_add,
    SMOKE_OT_rm,
    PARTICLES_PT_dust,
    PARTICLES_PT_smoke,
]

@persistent
def run_onload_scene(dummy):
    from .core.functions import set_active_collection_to_master_coll
    set_active_collection_to_master_coll()
    for area in bpy.context.screen.areas:
        if area.type == 'OUTLINER':
            for space in area.spaces:
                if space.type == 'OUTLINER':
                    if not space.show_restrict_column_hide:
                        space.show_restrict_column_hide = True
                        area.tag_redraw()
                    if not space.show_restrict_column_select:
                        space.show_restrict_column_select = True
                        area.tag_redraw()
                    if not space.show_restrict_column_viewport:
                        space.show_restrict_column_viewport = True
                        area.tag_redraw()

def register():
    addon_utils.enable("object_fracture_cell")

    register_class(RBDLabProps)
    bpy.types.Scene.rbdlab_props = bpy.props.PointerProperty(type=RBDLabProps)

    # register all classs
    for cls in all_classes:
        register_class(cls)

    bpy.app.handlers.load_post.append(run_onload_scene)


def unregister():

    # unreregister all classs
    for cls in reversed(all_classes):
        unregister_class(cls)

    unregister_class(RBDLabProps)
    del bpy.types.Scene.rbdlab_props

    bpy.app.handlers.load_post.remove(run_onload_scene)
