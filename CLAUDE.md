# Claude Code Documentation for Import 3DM Addon (Fixed)

## Project Information
- **Original Repository**: [jesterKing/import_3dm](https://github.com/jesterKing/import_3dm)
- **Fork Repository**: [JakubDobrovolnyLasvit/import_3dm](https://github.com/JakubDobrovolnyLasvit/import_3dm) 
- **Current Version**: v0.0.17
- **Fork Maintainer**: Jakub Dobrovolný (Lasvit)

This is a fork of the official Blender 3DM import addon with specific fixes for collection management and improved default settings.

## Recent Changes (v0.0.17-alpha3)

### Fresh Blocks Import Bug Fix (v0.0.17-alpha3)
**Problem**: When using "Update Block Definitions" (fresh blocks), block instances weren't properly linking to their definitions due to UUID collision between `handle_instance_definitions()` and `populate_instance_definitions()` functions.

**Root Cause**: Both functions independently generated versioned collection names, potentially creating different version numbers and mismatched UUIDs for the same block definition.

**Solution**: Modified `populate_instance_definitions()` to reuse the layername already determined by `handle_instance_definitions()`, ensuring consistent UUID generation.
- **Location**: `import_3dm/converters/instances.py:141-152`
- **Fix**: Added fallback logic and proper layername coordination between functions

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