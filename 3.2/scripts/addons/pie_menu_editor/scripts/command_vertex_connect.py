import bmesh
bm = bmesh.from_edit_mesh(C.object.data)
sh = bm.select_history
vert = None
for e in reversed(sh):
    if isinstance(e, bmesh.types.BMVert):
        vert = e.index
        break

O.object.select_all(action='DESELECT')

O.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
O.view3d.select('INVOKE_DEFAULT', deselect_all=True)
O.mesh.subdivide('INVOKE_DEFAULT', number_cuts=3)
O.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
O.mesh.select_less(use_face_step=False)
O.view3d.select('INVOKE_DEFAULT', deselect=True)
O.mesh.dissolve_verts()

if vert is not None:
    bm.verts[vert].select_set(True)
    sh.add(bm.verts[vert])

O.view3d.select('INVOKE_DEFAULT')

active_vert = sh[-1].index
if vert is not None:
    bm.verts[vert].select_set(True)
    O.mesh.vert_connect()
    O.view3d.select('INVOKE_DEFAULT', deselect_all=True)
    bm.verts[active_vert].select_set(True)
    sh.add(bm.verts[active_vert])

    # update viewport
    O.object.mode_set(mode='EDIT', toggle=True)
    O.object.mode_set(mode='EDIT', toggle=True)

O.ed.undo_push(message="Cut")