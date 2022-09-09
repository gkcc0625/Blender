import bpy



def add_shrinkwrap(obj, target, vgroup):
    shrinkwrap = obj.modifiers.new(name="Shrinkwrap", type="SHRINKWRAP")

    shrinkwrap.target = target
    shrinkwrap.wrap_method = 'NEAREST_VERTEX'
    shrinkwrap.vertex_group = vgroup
    shrinkwrap.show_expanded = False
    shrinkwrap.show_on_cage = True


def add_boolean(obj, operator, method='DIFFERENCE', solver='FAST'):
    boolean = obj.modifiers.new(name=method.title(), type="BOOLEAN")

    boolean.object = operator
    boolean.operation = 'DIFFERENCE' if method == 'SPLIT' else method
    boolean.show_in_editmode = True

    if method == 'SPLIT':
        boolean.show_viewport = False

    boolean.solver = solver

    return boolean



def apply_mod(modname):
    bpy.ops.object.modifier_apply(modifier=modname)
