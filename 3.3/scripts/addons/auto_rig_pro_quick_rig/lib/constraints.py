import bpy


def set_constraint_inverse_matrix(_cns, pbone):
    # set the inverse matrix of Child Of constraint 
    if _cns.target:
        if _cns.subtarget != '':
            bpy.ops.pose.select_all(action='DESELECT')
            bpy.context.active_object.data.bones.active = pbone.bone
            bpy.context.evaluated_depsgraph_get().update()
            context_copy = bpy.context.copy()
            context_copy["constraint"] = _cns
            try:
                bpy.ops.constraint.childof_set_inverse(context_copy, constraint=_cns.name, owner='BONE')  
            
            except:
                print("Could not set inverse matrix constraint", _cns.name, pbone.name)
           
            del context_copy
       
   