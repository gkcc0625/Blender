from . import box_primitive
from . import _prefs
from . import _m_duplication
from . import _m_main
from . import _m_modes
from . import _m_render
from . import _m_bookmarks
from . import _m_selection
from . import _m_modeling
from . import _m_direct_loop_cut
from . import _m_multicut
from . import _m_subd
from . import _m_unrotator
from . import _m_fitprim
from . import _m_tt
from . import _m_id_materials
from . import _m_cleanup
from . import _m_contexttools
from . import _m_piemenu_ops
from . import ke_cursormenu


bl_info = {
    "name": "keKit",
    "author": "Kjell Emanuelsson",
    "category": "",
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar",
    "warning": "",
    "description": "Extensive Script Collection",
    "doc_url": "https://artbykjell.com/wiki.html",
}


modules = (
    _prefs,
    box_primitive,
    _m_modes,
    _m_duplication,
    _m_main,
    _m_render,
    _m_bookmarks,
    _m_selection,
    _m_modeling,
    _m_direct_loop_cut,
    _m_multicut,
    _m_subd,
    _m_unrotator,
    _m_fitprim,
    _m_tt,
    _m_id_materials,
    _m_cleanup,
    _m_contexttools,
    _m_piemenu_ops,
    ke_cursormenu
)


def register():
    for m in modules:
        m.register()


def unregister():
    for m in modules:
        m.unregister()


if __name__ == "__main__":
    register()
