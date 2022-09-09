import bpy

def set_bone_layer(editbone, layer_idx, multi=False):
    editbone.layers[layer_idx] = True
    if multi:
        return
    for i, lay in enumerate(editbone.layers):
        if i != layer_idx:
            editbone.layers[i] = False