from bpy.types import PropertyGroup, Property
from typing import Union, Tuple, Dict, List, Generator

Value = Union[bool, int, float, str]

# Instances of Value can be replaced with Storage here,
# but a recursive type hint won't make things easier to read.
Storage = Union[Dict[str, Value], List[Value], Value]

LOGGING = True


def log(message: str):
    if LOGGING:
        print(message)


def valid_keys(group: PropertyGroup) -> Generator[str, None, None]:
    '''Yield valid keys for this property group,
    meaning everything except rna_type and bl_idname.'''
    for key in group.bl_rna.properties.keys():
        if key not in {'rna_type', 'bl_idname'}:
            yield key


def pref_prop(group: PropertyGroup, name: str) -> Tuple[Value, Property]:
    '''Call pref_prop_stored but without stored. Used for saving.'''
    pref, prop, _ = pref_prop_stored(group, None, name)
    return pref, prop


def pref_prop_stored(
    group: PropertyGroup,
    storage: Storage,
    name: str,
) -> Tuple[Value, Property, Value]:
    '''Get the the value and property of group[name],
    as well as the value from storage. Report the reason if it failed.'''
    pref = getattr(group, name, None)
    prop = group.bl_rna.properties.get(name)
    stored = storage.get(name) if storage else None

    if pref is None:
        log(f'SKIPPING {group}["{name}"] because it is NONE')

    elif prop.is_skip_save:
        log(f'SKIPPING {group}["{name}"] because it is SKIP SAVE')

    elif prop.is_readonly and prop.type not in {'POINTER', 'COLLECTION'}:
        log(f'SKIPPING {group}["{name}"] because it is READ ONLY')

    elif invalid_enum_item(group, storage, name, pref, prop, stored):
        log(f'SKIPPING {group}["{name}"] because it is INVALID ENUM ITEM')

    elif storage and stored is None:
        log(f'SKIPPING {group}["{name}"] because it is NOT STORED')

    else:
        return pref, prop, stored

    return None, None, None


def invalid_enum_item(
    group: PropertyGroup,
    storage: Storage,
    name: str,
    pref: Value,
    prop: Property,
    stored: Value,
) -> bool:
    '''Check whether a value is valid for an enum
    by trying it and catching the exception.'''
    if prop.type != 'ENUM' or not storage:
        return False
    if not storage:
        return False
    if stored in {x.identifier for x in prop.enum_items}:
        return False

    try:
        if stored:
            setattr(group, name, stored)
        return False
    except:
        return True
    finally:
        if pref:
            setattr(group, name, pref)


def save_recursive_group(group: PropertyGroup) -> Storage:
    '''Recursively save a property group.'''
    if group is not None:
        keys = valid_keys(group)
        storage = {k: save_recursive_by_name(group, k) for k in keys}
        return {k: v for k, v in storage.items() if v is not None}


def save_recursive_by_name(group: PropertyGroup, name: str) -> Storage:
    '''Save an item from a property group.'''
    pref, prop = pref_prop(group, name)

    if pref is None:
        return None

    elif prop.type == 'POINTER':
        return save_recursive_group(pref)

    elif prop.type == 'COLLECTION':
        return [save_recursive_group(x) for x in pref]

    elif getattr(prop, 'is_array', None):
        return [x for x in pref]

    elif isinstance(pref, (bool, int, float, str)):
        return pref


def load_recursive_group(group: PropertyGroup, storage: Storage):
    '''Recursively load a property group.'''
    for key in valid_keys(group):
        load_recursive_by_name(group, storage, key)


def load_recursive_by_name(group: PropertyGroup, storage: Storage, name: str):
    '''Load an item from a property group.'''
    pref, prop, stored = pref_prop_stored(group, storage, name)

    if pref is None or stored is None:
        return

    elif prop.type == 'POINTER':
        load_recursive_group(pref, stored)

    elif prop.type == 'COLLECTION':
        try:
            while len(pref) < len(stored):
                pref.add()
            while len(pref) > len(stored):
                pref.remove(0)
            for a, b in zip(pref, stored):
                load_recursive_group(a, b)

        except Exception as exception:
            log(f'SKIPPING {group}["{name}"] because of EXCEPTION: {exception}')

    elif getattr(prop, 'is_array', None):
        try:
            indices = range(len(pref))
            for index, value in zip(indices, stored):
                if pref[index] != value:
                    pref[index] = value

        except Exception as exception:
            log(f'SKIPPING {group}["{name}"] because of EXCEPTION: {exception}')

    elif pref != stored:
        try:
            setattr(group, name, stored)

        except Exception as exception:
            log(f'SKIPPING {group}["{name}"] because of EXCEPTION: {exception}')
