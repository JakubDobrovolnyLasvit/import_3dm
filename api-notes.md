# Blender Python API Notes - Import 3DM Addon

Project-specific API patterns and solutions for the Import Rhinoceros 3D addon.

## 🚨 CRITICAL LESSONS LEARNED (v0.0.17-beta1)

### Material System Architecture - TWO PROCESSING PATHS
**CRITICAL**: Rhino materials have TWO separate processing paths in the import system:

1. **Render Materials** (PBR materials with render content):
   ```python
   m = model.RenderContent.FindId(mat.RenderMaterialInstanceId)
   if m:  # Has render content
       matname = rendermaterial_name(m)
   ```

2. **Basic Materials** (materials without render content):
   ```python
   else:  # No render content
       matname = material_name(mat)
   ```

**BUG PATTERN**: Original code only implemented reuse logic for render materials, causing basic materials to fall back to default materials or get versioned (.001, .002).

**SOLUTION**: Process BOTH material types with same reuse logic:
```python
# Process ALL materials comprehensively
for mat in model.Materials:
    # First: Handle render materials (PBR)
    render_mat = model.RenderContent.FindId(mat.RenderMaterialInstanceId)
    if render_mat:
        matname = rendermaterial_name(render_mat)
        # Apply reuse logic here
    else:
        # Second: Handle basic materials 
        if mat.Name != "":  # Skip empty names (use default)
            matname = material_name(mat)
            # Apply SAME reuse logic here
```

### Material Reuse Pattern (Universal)
**Apply to ALL material types** (default, render, basic):
```python
reuse_materials = options.get("reuse_existing_materials", True)

if reuse_materials:
    # Check if material already exists in blend data
    existing_mat = context.blend_data.materials.get(matname)
    if existing_mat is not None:
        blmat = existing_mat  # Reuse existing
        print(f"  → Found and reusing existing material: {matname}")
    else:
        print(f"  → No existing material found, creating new one")
        blmat = utils.get_or_create_iddata(context.blend_data.materials, tags, None)
else:
    # Create new versioned material (.001, .002, etc.)
    print(f"  → Creating new versioned material")
    blmat = utils.get_or_create_iddata(context.blend_data.materials, tags, None)
```

### UUID Collision in Block Processing
**CRITICAL**: `handle_instance_definitions()` and `populate_instance_definitions()` must use SAME layername to avoid UUID conflicts:

```python
# In handle_instance_definitions()
layername = get_layername_for_block(idef)  # Store in options
options[f"layername_{idef.Id}"] = layername

# In populate_instance_definitions()  
layername = options.get(f"layername_{idef.Id}")  # Reuse same layername
if not layername:  # Fallback
    layername = create_layername_fallback(idef)
```

## Import/Export Operator Patterns

### ImportHelper Integration
```python
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty

class Import3dm(Operator, ImportHelper):
    """Import Rhinoceros 3D files (.3dm)"""
    bl_idname = "import_3dm.some_data"
    bl_label = "Import Rhinoceros 3D file"
    
    # ImportHelper mixin class uses this
    filename_ext = ".3dm"
    filter_glob: StringProperty(default="*.3dm", options={'HIDDEN'})
    
    # Custom import options
    merge_distance: FloatProperty(
        name="Merge Distance",
        description="Distance for merging duplicate vertices (in meters)",
        default=0.000001,  # 0.001mm
        min=0.0000001,
        precision=6,
    )
```

### Error Handling in Import Operations
```python
def execute(self, context):
    try:
        result = read_3dm(context, options)
        if result == {'CANCELLED'}:
            self.report({'ERROR'}, f"Failed to import .3dm file: {self.filepath}")
            return {'CANCELLED'}
        elif result == {'FINISHED'}:
            self.report({'INFO'}, f"Successfully imported {self.filepath}")
            return {'FINISHED'}
    except Exception as e:
        self.report({'ERROR'}, f"Import failed with error: {str(e)}")
        return {'CANCELLED'}
```

## Collection Management for Imports

### Versioned Collection Creation
```python
def create_or_get_top_layer(context, filepath):
    base_name = Path(filepath).stem
    
    # Create versioned collection name to avoid contamination
    version = 1
    top_collection_name = base_name
    
    # Find next available version number
    while top_collection_name in context.blend_data.collections.keys():
        version += 1
        top_collection_name = f"{base_name}_v{version}"
    
    # Always create new collection with version suffix
    toplayer = context.blend_data.collections.new(name=top_collection_name)
    return toplayer
```

### Object Tracking with GUIDs
```python
# Tag objects with original IDs for re-import handling
def tag_data(idblock, tag_dict):
    guid = tag_dict.get('rhid', None)
    name = tag_dict.get('rhname', None)
    idblock['rhid'] = str(guid)
    idblock['rhname'] = name

# Retrieve objects by original GUID
def get_or_create_iddata(base, tag_dict, obdata):
    guid = tag_dict.get('rhid', None)
    if guid and str(guid) in object_cache:
        return object_cache[str(guid)]
    # Create new object if not found
    return base.new(name=tag_dict['rhname'], object_data=obdata)
```

## Material Import and Compatibility

### Blender 4.2+ Transparency API
```python
def setup_material_transparency(material, transparency):
    if transparency > 0.0:
        # Modern API (Blender 4.2+)
        if hasattr(material, 'render_method'):
            material.render_method = 'BLENDED'
        # Legacy fallback
        else:
            material.blend_method = 'BLEND'
```

### Material Node Setup
```python
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

def setup_pbr_material(rhino_material, blender_material):
    blender_material.use_nodes = True
    pbr = PrincipledBSDFWrapper(blender_material, is_readonly=False)
    
    # Set material properties
    pbr.base_color = get_color_field(rhino_material, "color")[0:3]
    pbr.transmission = get_float_field(rhino_material, "transparency") 
    pbr.roughness = 1.0 - get_float_field(rhino_material, "reflectivity")
    pbr.ior = get_float_field(rhino_material, "ior")
```

## Mesh Processing

### Configurable Vertex Merging
```python
def process_imported_mesh(mesh, options):
    if needs_welding:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        
        # Use configurable merge distance
        merge_dist = options.get("merge_distance", 0.000001)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_dist)
        
        bm.to_mesh(mesh)
        bm.free()
```

## Block/Instance Management

### Configurable Empty Display Size
```python
def setup_block_instance(iref, options):
    iref.instance_type = 'COLLECTION'
    iref.instance_collection = block_collection
    
    # Use configurable display size
    iref.empty_display_size = options.get("empty_display_size", 0.0001)
```

### Block Definition Preservation
```python
def populate_instance_definitions(context, model, options):
    update_block_defs = options.get("update_block_definitions", False)
    
    for idef in model.InstanceDefinitions:
        parent = get_or_create_collection(idef.Id, idef.Name)
        
        # Preserve existing user work by default
        if not update_block_defs and len(parent.objects) > 0:
            continue  # Skip updating, keep user's materials/UV work
        elif update_block_defs and len(parent.objects) > 0:
            parent.objects.clear()  # Clear for fresh update
        
        # Populate with new geometry
        populate_block_geometry(parent, idef, context)
```

## Advanced Import Patterns

### Options Dictionary Management
```python
def setup_import_options(operator):
    return {
        "filepath": operator.filepath,
        "merge_distance": operator.merge_distance,
        "empty_display_size": operator.empty_display_size, 
        "update_block_definitions": operator.update_block_definitions,
        "import_meshes": operator.import_meshes,
        # ... other options
    }
```

### Fresh Object Creation on Re-import
```python
def init_fresh_dict(context):
    """Initialize dictionary structure without populating existing objects.
    This ensures fresh objects are created for each import session."""
    global all_dict
    all_dict = dict()
    bases = [
        context.blend_data.objects,
        context.blend_data.materials,
        context.blend_data.collections,
    ]
    for base in bases:
        t = repr(base).split(',')[1]
        all_dict[t] = dict()  # Empty dict without population
```

## UI Layout for Import Options

### Advanced Options Panel
```python
def draw(self, context):
    layout = self.layout
    
    # Basic options boxes...
    
    # Advanced options
    box = layout.box()
    box.label(text="Advanced")
    row = box.row()
    row.prop(self, "merge_distance", text="Merge Distance (m)")
    row = box.row() 
    row.prop(self, "empty_display_size", text="Empty Size (m)")
    box.prop(self, "update_block_definitions")
```

## Key Documentation References

For complete API documentation, see `/docs/blender_python_reference_4_5/`:
- `bpy.types.Operator.html` - Import operator base class
- `bpy.data.html` - Access to collections, materials, meshes
- `bpy.props.html` - Property types for import settings
- `bmesh.html` - Mesh processing operations