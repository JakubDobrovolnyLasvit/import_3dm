# Claude Code Documentation for Import 3DM Addon (Fixed)

## Project Information
- **Original Repository**: [jesterKing/import_3dm](https://github.com/jesterKing/import_3dm)
- **Fork Repository**: [JakubDobrovolnyLasvit/import_3dm](https://github.com/JakubDobrovolnyLasvit/import_3dm) 
- **Current Version**: v0.0.17
- **Fork Maintainer**: Jakub Dobrovolný (Lasvit)

This is a fork of the official Blender 3DM import addon with specific fixes for collection management and improved default settings.

## Project Status: v0.0.17-beta1 RELEASE READY ✅

### 🎯 Major Accomplishments (September 2024)

**✅ COMPREHENSIVE MATERIAL REUSE FIX**
- **Problem Solved**: Scenario #4 (Fresh Definitions + Preserve Materials) was creating new materials (.001, .002) instead of reusing existing ones
- **Root Cause**: Material processing had two separate paths - render materials (PBR) and basic materials. Only render materials had reuse logic.
- **Complete Solution**: Implemented comprehensive material reuse system for ALL material types:
  - Default materials (Rhino Default Material, Rhino Default Text)  
  - Render materials (PBR materials with render content)
  - Basic materials (simple materials without render content)
- **Location**: `import_3dm/converters/material.py:580-655`
- **Result**: All scenarios (1, 4, 6) now work perfectly

**✅ FRESH BLOCKS UUID COLLISION FIX**
- **Problem**: UUID collision between `handle_instance_definitions()` and `populate_instance_definitions()` functions
- **Solution**: Coordinated layername generation between both functions
- **Location**: `import_3dm/converters/instances.py:141-152`

**✅ UI/UX IMPROVEMENTS**
- Reorganized import dialog with emoji icons (🔺 Geometry, 📦 Blocks, 🎨 Materials, etc.)
- Added mesh vertex merging controls with millimeter precision
- Improved material handling options with clear descriptions
- Better panel organization and layout

**✅ TECHNICAL FIXES**
- Fixed `model.Settings` null check to prevent import crashes (`read3dm.py:121-126`)
- Added comprehensive debug output for troubleshooting
- Enhanced error handling for edge cases

### 🧪 Testing Results
- **Scenario #1** (Fresh + Create New): ✅ Working perfectly
- **Scenario #4** (Fresh + Preserve): ✅ **FIXED** - No more unwanted material versions
- **Scenario #6** (Preserve + Preserve): ✅ Working perfectly

### 📋 Current Status (September 9, 2024)
- **Version**: v0.0.17-beta1
- **Git Status**: All changes committed and pushed to GitHub
- **Release Assets**: `import_3dm_v0.0.17-beta1.zip` created and ready
- **GitHub Release**: Ready to publish (manual upload needed)
- **Documentation**: Updated with comprehensive change log

### 🚀 Next Steps
1. **READY FOR RELEASE**: Upload `import_3dm_v0.0.17-beta1.zip` to GitHub releases
2. **Future Development**: Monitor user feedback on beta1 release
3. **Potential v1.0**: If beta1 is stable, consider full release

### 🎯 Key User Scenarios Working
The fork successfully addresses the main user pain points:
- ✅ Material preservation during fresh imports (no more .001 versions)
- ✅ Block definition consistency (no more UUID conflicts)  
- ✅ Improved UI for better user experience
- ✅ Enhanced debugging capabilities for troubleshooting

**Status: COMPLETE AND RELEASE-READY** 🎉

## Previous Changes (v0.0.17)

### 1. Collection Management Fix (Issue Resolution)
**Problem**: Re-importing modified 3DM files caused collection management issues where old and new data would contaminate each other due to object sharing between imports.

**Root Cause**: The `get_or_create_iddata()` function used a global dictionary to track objects by Rhino GUID, causing re-imports to reuse existing objects instead of creating fresh ones.

**Solution**: 
- Modified `initialize()` function in `converters/__init__.py:59-64` to use `clear_all_dict()` instead of `reset_all_dict()`
- This ensures completely fresh objects are created for each import session
- The `create_or_get_top_layer()` function in `read3dm.py:58-73` creates versioned collections  
- Combined approach ensures both object-level and collection-level separation between imports

### 2. Advanced Import Options (NEW)
**UI Improvements**: Added configurable options in the import dialog's "Advanced" section:

**Empty Display Size**
- **UI Option**: "Empty Size (m)" with default 0.0001m (0.1mm)
- **Purpose**: Control display size of block instance empties
- **Location**: `import_3dm/converters/instances.py:85`

**Merge Distance** 
- **UI Option**: "Merge Distance (m)" with default 0.000001m (0.001mm) 
- **Purpose**: Distance for merging duplicate vertices during mesh import
- **Location**: `import_3dm/converters/render_mesh.py:110-111`

**Update Block Definitions**
- **UI Option**: Checkbox, default OFF (preserves user work)
- **Purpose**: Control whether to update existing block definitions or preserve user's materials/UV mapping work
- **Location**: `import_3dm/converters/instances.py:111-118`

### 3. Block Definition Preservation System (NEW)
**Problem Solved**: Users lose their material and UV mapping work on block definitions when re-importing
**Solution**: 
- **Default behavior**: Preserve existing block definitions (checkbox OFF)
- **Update mode**: Clear and rebuild block definitions (checkbox ON)
- **Smart logic**: Only affects block definitions that already contain objects

## Fork Identification
The addon properly identifies itself as a fork:
- Name: "Import Rhinoceros 3D (Fixed)"
- Authors include original maintainers plus "Jakub Dobrovolný"
- Description mentions "versioned collections to prevent data contamination on re-import"
- Wiki URL points to the fork repository

## Known Issues & TODOs

### Collection Management
The current versioning solution works but may need refinement:
- Consider more sophisticated collection naming strategies
- May need UI options for collection management preferences
- Need to test with complex nested hierarchies

### Testing Commands
```bash
# No specific test commands identified in the codebase
# Manual testing required with .3dm files in Blender

# Create ZIP for Blender addon installation
python -m zipfile -c import_3dm_v0.0.17-alphaX.zip import_3dm/
```

### Version Update Process
**IMPORTANT:** When creating new alpha versions, update BOTH files:

1. **`import_3dm/__init__.py`**:
   ```python
   "name": "Import Rhinoceros 3D (Fixed) - Lasvit Fork v0.0.17-alphaX"
   ```

2. **`import_3dm/blender_manifest.toml`**:
   ```toml
   version = "0.0.17-alphaX"
   name = "Import Rhinoceros 3D (Fixed) - Lasvit Fork v0.0.17-alphaX"
   ```

**Why Both?** Blender 4.2+ uses `blender_manifest.toml` for extension names in preferences, while older versions use `__init__.py`. Update both to ensure version visibility in all Blender versions.

## File Structure
```
import_3dm/
├── __init__.py                 # Main addon entry point, UI, and import options
├── read3dm.py                 # Core import logic and collection management
├── blender_manifest.toml      # Addon metadata for Blender 4.2+
└── converters/
    ├── __init__.py           # Converter initialization and object handling
    ├── instances.py          # Block/instance reference handling (modified)
    ├── render_mesh.py        # Mesh conversion and vertex welding
    ├── annotation.py         # Text and dimension handling
    ├── material.py           # Material conversion
    ├── layers.py            # Layer management
    ├── views.py             # Camera/view import
    ├── curve.py             # Curve geometry
    ├── groups.py            # Group management
    ├── utils.py             # Utility functions
    └── pointcloud.py        # Point cloud handling
```

## Development Notes
- The addon uses rhino3dm.py library for .3dm file parsing
- Blender version compatibility: 3.5.0+
- Unit system properly handles scale conversion from Rhino to Blender
- Material linking supports both object and data linking modes

## Documentation Resources
- **Project-specific API notes**: `api-notes.md` - Import/export specific Blender Python API patterns and solutions
- **Shared documentation**: `/docs/blender_python_reference_4_5/` - Complete Blender 4.5 Python API reference (shared across projects)