
#Bunch of functions related to collection 

import bpy


def get_recursive_childs(root):
    """Get a list of all context.scene collections."""
    
    all=[]
    for child in root.children:
        all.append(child)
        all += get_recursive_childs(child)
        
    return all


def exclude_all_view_layers(collection, exclude=True):
    """exclude a collection from all view layers f all scenes"""
        
    def recur_all_layer_collection(layer_collection,all_vl,):
        if len(layer_collection.children):
            all_vl += layer_collection.children
            for ch in layer_collection.children:
                recur_all_layer_collection(ch,all_vl)
        return all_vl

    for s in bpy.data.scenes:
        for v in s.view_layers:
            for lc in recur_all_layer_collection(v.layer_collection,[]):
                if (lc.collection==collection):
                    lc.exclude = exclude
    return None 


def create_new_collection(name, parent_name=None, prefix=False, exclude=False):
    """Create new collection and link in given parent (if not None)."""
        
    if prefix: #should be called "suffix" not prefix... anyway...
        from .. utils.str_utils import find_suffix
        name = find_suffix(name,bpy.data.collections,)

    if parent_name == None:
        parent = bpy.context.scene.collection
    else: 
        parent = bpy.data.collections.get(parent_name)
        if not parent:
            return 
    
    new_col = bpy.data.collections.get(name)

    #Create the new collection? 
    if not new_col:
        new_col = bpy.data.collections.new(name=name)
        
        #if new then need to link it in parent 
        if new_col.name not in parent.children :
            parent.children.link(new_col)

        #and also exclude it perhaps? 
        if exclude:
            exclude_all_view_layers(new_col)
    
    return new_col 


def collection_clear_obj(collection):
    """unlink all obj from a collection"""

    for obj in collection.objects:
        collection.objects.unlink(obj)

    return None


def get_viewlayer_coll(active_coll, collname):
    """Get viewlayer from collection name."""
    
    if (active_coll.name == collname): return active_coll
    found = None
    
    for layer in active_coll.children:
        found = get_viewlayer_coll(layer, collname)
        if found:
            return found

    return None 
    

def set_collection_active(name="", scene=False):
    """Set collection active by name, return False if failed."""

    if scene:
        name = bpy.context.scene.collection.name
        
    current_active = bpy.context.view_layer.layer_collection
    active_coll = get_viewlayer_coll(current_active, name)
    
    if active_coll:
        bpy.context.view_layer.active_layer_collection = active_coll
        
    return (active_coll !=None)


def close_collection_areas():
    """close level on all outliner viewlayer area"""

    override = bpy.context.copy()
    for a in bpy.context.window.screen.areas:
        if a.type=="OUTLINER":
            if a.spaces[0].display_mode=="VIEW_LAYER":
                a.tag_redraw()
                override["area"] = a
                override["regions"] = a.regions[0]
                override["space"] = a.spaces[0]
                bpy.ops.outliner.show_one_level((override),open=False)
                bpy.ops.outliner.show_one_level((override),open=False)
                bpy.ops.outliner.show_one_level((override),open=False)
                a.tag_redraw()

    return None 
    

def create_scatter5_collections():
    """Create scatter collection set-up."""
        
    #if run this function for the first time, then we'll need these collections to be closed by default    
    do_close = "Scatter5" not in bpy.data.collections
    
    parent = create_new_collection("Scatter5")
    create_new_collection("Scatter5 Geonode", parent_name=parent.name)
    create_new_collection("Scatter5 Ins Col", parent_name=parent.name, exclude=True,)
    create_new_collection("Scatter5 Import", parent_name=parent.name, exclude=True,)
    create_new_collection("Scatter5 Extra", parent_name=parent.name, exclude=True,)

    if do_close:
        def will_close():
            close_collection_areas()
        bpy.app.timers.register(will_close, first_interval=0.555)

    return None 
