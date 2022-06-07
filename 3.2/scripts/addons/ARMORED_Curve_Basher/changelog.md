# CURVEBASHER CHANGELOG

## v1.3 (LATEST)
*(12/Apr/21)*
- NEW Tool: Curvecast (*C*).
- NEW Tool: Mesh to Curvebash (*RMB* Context Menu).
- Wire Generator Random algorithm: Parallel.
- Wire Generator Pattern: Array.
- Wire Generator Property: Gravity.
- Wire Generator Property: Handle Alignment.
- Wire Generator Behaviour: Handles are now hooked to the volumes (only noticeable with *Aligned* handles).
- Wire Generator Behaviour: Massive performance boost with high curve counts.
- Curvebasher Property: Transform Slide.
- Curvebasher Property: *Array* types support caps.
- Curvebasher Property: can toggle the array type between *Fit Curve*. and *Fixed Count*
- Curvebasher Property: *Shift + Scroll* or *Ctrl + Shift + Scroll* increases *Profiles Types* edge count in different ways.
- Curvebasher Property: *Shift + Scroll* switches *Array* types to *Fixed Count* mode and changes the array count.
- Curvebasher Behaviour: links assets to the scene instead of appending.
- Curvebasher Behaviour: leaves no orphan data when browsing through presets.
- Curvebasher Behaviour: HUD remembers user settings between Blender sessions.
- Curvebasher Behaviour: when possible, discard invalid selections instead of raising exceptions.
- Curvebasher Behaviour: all transforms are persistent between type switching.
- Curvebasher Behaviour: all transforms are persistent between type switching.
- Curvebasher Behaviour: Deletes IDs when the reference geometry is missing.

- BUGFIX: where random curvebash scales would reset if the operator was cancelled (RMB) without any changes.
- BUGFIX: when using Array Mode that would crash the addon if you cancelled the operator before applying a scale trasformation.
- BUGFIX: Previous feature enable smart filtering for 'Profile' curves was accidently disabled but is now working again.

### Revision 1:
*(13/Apr/21)*
- Curvebasher Preferences: added *Adapt to HiDPI* - Scale the HUD based on your system scale.
- Curvebasher Preferences: added *HUD Scale* - Make the HUD bigger or smaller'.
- Curvebasher BUGFIX: added a cleanup function to remove the linked preset library to prevent *Missing Lib messages* (harmless errors).
- Wire Generator BUFGIX: When using objects with no dimensions such as Empties, 
  enabling *Gravity* placed the gravity volume in the wrong location or crashed the operator.

### Revision 2:
*(15/Apr/21)*
- Curvebasher BUGFIX: applying scale on a curve transfers that scale to its control points. Added 2 developer functions that counteract
  it in different ways. Best method is enabled by default *mk_inverse_scale_points*.


## v1.2
*(05/Nov/20)*
- Added the Wire Generator Tool (Shift+A>Curve>Wire Generator).
- Can now Randomize scale by holding ALT or ALT+SHIFT when scaling.
- 'Uniform Scale' on 'Array' types no longer requires ALT press and is now called 'Scale'.
- 'Array' types now support Scale Reset and new curves utilize the last scale applied in 'Array' mode.
- Mouse wraps around the screen when the border is reached.
- Added expandable HUD (F1, or H during the modal).
- Curve Profiles for 'Basic' types now appear selected. Based on context, the addon can ignore their 
 selection to prevent recursion (curve profiles being applied to curve profiles).

- 'Curve Kitbash' Collection is now deleted automatically when empty.
- Performance increase when creating 'Array' types.
- Improvements when resetting or canceling transforms.
- Fixed a scaling issue on the chain preset.
- Fixed a bug that increased the Uniform Scale speed depending on how many 'Array' types were selected.
- Fixed a bug that created internal selection duplicates. Using a Set instead of List to store the internal slection fixed the issue.
- Edge to curve conversion was broken in the previous release. The issue has been fixed.
- The active curve, along with its transforms and kitbash, will be used for the next virgin curve/s.

Revision 1:
-Removed stray print statements.
-Fixed crash from pressing TAB during the modal. TAB now selects the curve points correctly.


## v1.1
*(23/Sep/20)*
- Added the Draw Curve Tool (Shift+A>Curve>Draw Curve).
- Added a button in the N Panel that opens the 'Default Presets' Blend file.
- Fixed a bug that was creating extra mesh data for Array Types.