# KIT OPS

## Release Log

### 2.20.53
- Added potential fix for boolean objects remaining as cutter even when deleted.

### 2.20.52
- Added cycles_visibility polyfiller fix for Blender 3.0.

### 2.20.51
- Added potential fix for erroneously deleting modifiers off of objects in the handler.

### 2.20.50
- Added initial implementation of Quick Create INSERT: Set object to bottom.

### 2.20.49
- Added Initial version of quick create INSERT code.

### 2.20.48
- Added initial capability for KIT OPS replacement of INSERTs.

### 2.20.47
- Bug fix for null check when auto scale is off.

### 2.20.46
- Added null checks to support BATCH.  This may need refactoring in the future (insert.add being used for multiple functions)


### 2.20.45
- Added potential fix for KIT OPS free crash bug.

### 2.20.44
- Added Smooth modifier to sort list.

### 2.20.43
- When adding a material, a material is now added to the active slot.

### 2.20.42
- Added fix for hdri not being removed in factory modes.
- Added fix (potential) for cutters being removed when thumbnail is rendered.

### 2.20.41
- Added auto packing when saving an INSERT in factory mode.

### 2.20.40
- Added fix for bug when separate material with same image is imported.

### 2.20.39
- Added warning message when adding an INSERT to another that does not have a target.

### 2.20.38
- Added fix for handling duplicate images in scene

### 2.20.37
- Rolled back "Remove INSERT properties if there is no target" feature.

### 2.20.36
- Moved menu item.

### 2.20.35
- Adding fix for INSERT relocate crashing Blender.

### 2.20.34
- Introducing Relocate INSERT feature

### 2.20.33
- Added fix for INSERT not being active object when placed after snap mode enabled.

### 2.20.32
- Fixed "remove wire" panel bug.

### 2.20.31
- Snap Mode will now snap to a selected object if the target is not selected.

### 2.20.30
- When adding an INSERT with no target, INSERT props will be removed.

### 2.20.29
- Fixed duplicate material in image bug.

### 2.20.28
- Introduction of INSERT replace feature

### 2.20.27
- Added same icon logic to category thumbnails as for favorites/recents.

### 2.20.26
- Removed Auto Save Preferences as this was causing wider issues.

### 2.20.25
- Added further UI improvements to Favorites and Recently Used.

### 2.20.24
- Added improvements to recently used anf favorites layout.

### 2.20.23
- Added fix for User Preferences bug when favorites were not saving.

### 2.20.22
- Increased favorite rows.

### 2.20.21
- Introduced fix for Blender 3 crash on Creation of INSERT.

### 2.20.20
- Removed labels from favorites

### 2.20.19
- Added favorites and recently used functionality.

### 2.20.18
- Fixed save INSERT bug where insert_name.blend was being saved if button clicked twice.

### 2.20.17
- Disabled show_solid_objects, show_cutter_objects, and show_wire_objects

### 2.20.16
- Fix for when adding INSERTs and no target selected.

### 2.20.15
- When Creating and INSERT/Material, the lscene will be saved (with warning to save if not saved at al).
- Refresh button on panel should remember previous INSERT setting.
- Fixed Deselected Object/Edit Insertion Bug.

### 2.20.14
- Fixed a crash bug reported on a Mac when Close Factory Scene is pressed.

### 2.20.13
- Allowed scale to remembered when adding an Insert.


### 2.20.12
- Added minor fix for 'render' error on Close Factory Scene.

### 2.20.11
- Introduced snap modes for Face/Edge/Vertex

### 2.20.10
- Changed sorting to only be for inserts, not folders

### 2.20.9
- Changed aut scale and parent parameters to be associated with Blender preferences.
- Added a sort to all enums so that they should sort alphabetically.

### 2.20.8
- Added initial version of snap-to-face feature.
- Removed 'Apply INSERT' feature.
- Removed 'Delete INSERT' feature.

### 2.20.7
- Added messaging to Preferences folder for thumbnail cache and automatically refresh KPACKs on Pillow install.

### 2.20.5
- Added Known Issue note about object removal call getting exponentially longer.

### 2.20.5
- Added further improvements to thumbnail caching.

### 2.20.4
- Disabled Pillow install button if already installed.

### 2.20.3
- Introduced Image Caching.

### 2.20.2
- Changed wording for adding an INSERT to include mouse scroll info.

### 2.20.1
- Changed panel target object layout.

### 2.20.00
- Made Smart Mode part of standard Free release; separated authoring code.

### 2.19.18
- Moved Auto Parent option to main panel.

### 2.19.17
- Fixed bug when adding an INSERT in auto scale mode and booleans are added.

### 2.19.16
- Removed references to auto scale in code.

### 2.19.15
- Added fix for magnitude error on shift click.

### 2.19.14
- Removed auto_add checkbox and made Smart Mode the same as Auto Select.

### 2.19.13
- In SMART mode, scale and rotation are maintained when shift+adding inserts.

### 2.19.12
- Added rotation ability when pressing ctrl key.

### 2.19.11
- Added efficiency saving for auto select

### 2.19.10

- Bug fix for active object not being reset when collections are rest.


### 2.19.9

#### Features
- Initial version of aligning insert rotation with target object rotation

### 2.19.8

#### Features
- Materials are now de-duplicated by default when adding an INSERT to the scene.
- Added fix for Open Scene factory bug, when an INSERT was being removed when thumbnail mode was closed.
- Cache thumbnails button created: Speed up KIT OPS by creating thumbnails.
- Search feature removed as although the functionality worked its value was limited
- Exposed ability to programmatically disable and re-enable Smart mode
- Added ability to parent INSERTs (Experimental, off by default)


