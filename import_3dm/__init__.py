# MIT License

# Copyright (c) 2018-2024 Nathan Letwory, Joel Putnam, Tom Svilans, Lukas Fertig

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


bl_info = {
    "name": "Import Rhinoceros 3D (Fixed) - Lasvit Fork v0.0.18",
    "author": "Jakub Dobrovolný (Lasvit) - Fork of original by Nathan 'jesterKing' Letwory, Joel Putnam, Tom Svilans, Lukas Fertig, Bernd Moeller",
    "version": (0, 0, 18),
    "blender": (5, 0, 0),
    "location": "File > Import > Rhinoceros 3D (.3dm)",
    "description": "LASVIT FORK: Import Rhinoceros 3dm files with versioned collections and improved defaults",
    "warning": "The importer doesn't handle all data in 3dm files yet",
    "wiki_url": "https://github.com/JakubDobrovolnyLasvit/import_3dm",
    "category": "Import-Export",
}

# with extentions bl_info is deleted, we keep a copy of the version
bl_info_version = bl_info["version"][:]

import bpy
# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
from bpy.types import Operator

from typing import Any, Dict

from .read3dm import read_3dm


class Import3dm(Operator, ImportHelper):
    """Import Rhinoceros 3D files (.3dm). Currently does render meshes only, more geometry and data to follow soon."""
    bl_idname = "import_3dm.some_data"  # important since its how bpy.ops.import_3dm.some_data is constructed
    bl_label = "Import Rhinoceros 3D file"

    # ImportHelper mixin class uses this
    filename_ext = ".3dm"

    filter_glob: StringProperty(
        default="*.3dm",
        options={'HIDDEN'},
        maxlen=1024,  # Max internal buffer length, longer would be clamped.
    ) # type: ignore

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    import_hidden_objects: BoolProperty(
        name="Hidden Geometry",
        description="Import hidden geometry.",
        default=True,
    ) # type: ignore

    import_hidden_layers: BoolProperty(
        name="Hidden Layers",
        description="Import hidden layers.",
        default=True,
    ) # type: ignore

    import_annotations: BoolProperty(
        name="Annotations",
        description="Import annotations.",
        default=True,
    ) # type: ignore

    import_curves: BoolProperty(
        name="Curves",
        description="Import curves.",
        default=True,
    ) # type: ignore

    import_meshes: BoolProperty(
        name="Meshes",
        description="Import meshes.",
        default=True,
    ) # type: ignore

    import_subd: BoolProperty(
        name="SubD",
        description="Import SubDs.",
        default=True,
    ) # type: ignore

    import_extrusions: BoolProperty(
        name="Extrusions",
        description="Import extrusions.",
        default=True,
    ) # type: ignore

    import_brep: BoolProperty(
        name="BRep",
        description="Import B-Reps.",
        default=True,
    ) # type: ignore

    import_pointset: BoolProperty(
        name="PointSet",
        description="Import PointSets.",
        default=True,
    ) # type: ignore

    import_views: BoolProperty(
        name="Standard",
        description="Import standard views (Top, Front, Right, Perspective) as cameras.",
        default=False,
    ) # type: ignore

    import_named_views: BoolProperty(
        name="Named",
        description="Import named views as cameras.",
        default=True,
    ) # type: ignore

    import_groups: BoolProperty(
        name="Groups",
        description="Import groups as collections.",
        default=False,
    ) # type: ignore

    import_nested_groups: BoolProperty(
        name="Nested Groups",
        description="Recreate nested group hierarchy as collections.",
        default=False,
    ) # type: ignore

    import_instances: BoolProperty(
        name="Blocks",
        description="Import blocks as collection instances.",
        default=True,
    ) # type: ignore

    import_instances_grid_layout: BoolProperty(
        name="Grid Layout",
        description="Lay out block definitions in a grid ",
        default=False,
    ) # type: ignore

    import_instances_grid: IntProperty(
        name="Grid",
        description="Block layout grid size (in import units)",
        default=10,
        min=1,
    ) # type: ignore

    link_materials_to : EnumProperty(
        items=(("PREFERENCES", "Use Preferences", "Use the option defined in preferences."),
               ("OBJECT", "Object", "Link material to object."),
               ("DATA", "Object Data", "Link material to object data.")),
        name="Link To",
        description="Set how materials should be linked",
        default="PREFERENCES",
    )  # type: ignore

    # Advanced import options
    empty_display_size: FloatProperty(
        name="Empty Display Size",
        description="Display size for block instance empties (in meters)",
        default=0.0001,  # 0.1mm
        min=0.000001,    # 0.001mm minimum
        max=0.01,        # 10mm maximum  
        step=0.0001,
        precision=6,
    ) # type: ignore
    
    merge_vertices: BoolProperty(
        name="Merge Duplicate Vertices",
        description="Merge duplicate vertices in mesh geometry",
        default=True,
    ) # type: ignore
    
    merge_distance: FloatProperty(
        name="Vertex Merge Distance", 
        description="Distance for merging duplicate vertices (in millimeters)",
        default=0.001,     # 0.001mm
        min=0.0001,        # 0.0001mm minimum
        max=10.0,          # 10mm maximum
        step=0.001,
        precision=3,       # Three digits after decimal
    ) # type: ignore
    
    block_import_mode: EnumProperty(
        items=(("PRESERVE", "Use Existing Definitions", "Keep existing block definitions and add only new blocks (preserves your materials and UV work)"),
               ("FRESH", "Create Fresh Definitions", "Create new block definition collections with fresh geometry for all blocks")),
        name="Block Import Mode",
        description="Choose how to handle block definitions during import",
        default="PRESERVE",
    ) # type: ignore
    
    material_handling: EnumProperty(
        items=(("PRESERVE", "Preserve Existing", "Keep existing material properties unchanged, reuse materials by name"),
               ("UPDATE", "⚠️ Update Properties", "Reuse materials by name but update their properties from 3DM file (affects existing materials!)"),
               ("CREATE_NEW", "Create New Versions", "Create new material versions (.001, .002) with 3DM properties")),
        name="Material Handling",
        description="Choose how to handle materials during import",
        default="PRESERVE",
    ) # type: ignore

    def execute(self, context : bpy.types.Context):
        options : Dict[str, Any] = {
            "filepath":self.filepath,
            "import_views":self.import_views,
            "import_named_views":self.import_named_views,
            "import_annotations":self.import_annotations,
            "import_curves":self.import_curves,
            "import_meshes":self.import_meshes,
            "import_subd":self.import_subd,
            "import_extrusions":self.import_extrusions,
            "import_brep":self.import_brep,
            "import_pointset":self.import_pointset,
            "update_materials":(self.material_handling in ["UPDATE", "CREATE_NEW"]),
            "import_hidden_objects":self.import_hidden_objects,
            "import_hidden_layers":self.import_hidden_layers,
            "import_groups":self.import_groups,
            "import_nested_groups":self.import_nested_groups,
            "import_instances":self.import_instances,
            "import_instances_grid_layout":self.import_instances_grid_layout,
            "import_instances_grid":self.import_instances_grid,
            "link_materials_to":self.link_materials_to,
            "empty_display_size":self.empty_display_size,
            "merge_vertices":self.merge_vertices,
            "merge_distance":self.merge_distance / 1000.0,  # Convert mm to meters
            "create_fresh_block_definitions":(self.block_import_mode == "FRESH"),
            "reuse_existing_materials":(self.material_handling != "CREATE_NEW"),
        }
        
        try:
            result = read_3dm(context, options)
            if result == {'CANCELLED'}:
                self.report({'ERROR'}, f"Failed to import .3dm file: {self.filepath}")
                return {'CANCELLED'}
            elif result == {'FINISHED'}:
                self.report({'INFO'}, f"Successfully imported {self.filepath}")
                return {'FINISHED'}
            else:
                return result
        except Exception as e:
            self.report({'ERROR'}, f"Import failed with error: {str(e)}")
            return {'CANCELLED'}

    def draw(self, _ : bpy.types.Context):
        layout = self.layout
        layout.label(text="Import .3dm v{}.{}.{}".format(bl_info_version[0], bl_info_version[1], bl_info_version[2]))

        box = layout.box()
        box.label(text="🔺 Geometry")
        
        # Meshes first, in its own row
        box.prop(self, "import_meshes")
        
        # Mesh-specific settings (indented under meshes)
        if self.import_meshes:
            mesh_box = box.box()
            mesh_box.prop(self, "merge_vertices")
            if self.merge_vertices:
                mesh_box.label(text="Vertex Merge Distance:")
                mesh_box.prop(self, "merge_distance", text="Distance (mm)")
        
        # Other geometry types in grid layout
        row = box.row()
        row.prop(self, "import_brep")
        row.prop(self, "import_extrusions") 
        row = box.row()
        row.prop(self, "import_subd")
        row.prop(self, "import_curves")
        row = box.row()
        row.prop(self, "import_annotations")
        row.prop(self, "import_pointset")

        box = layout.box()
        box.label(text="📦 Blocks")
        box.prop(self, "import_instances")
        box.label(text="Block Import Mode:")
        box.prop(self, "block_import_mode", text="")
        row = box.row() 
        row.prop(self, "empty_display_size", text="Empty Size (m)")

        box = layout.box()
        box.label(text="👁 Hidden Content")
        box.prop(self, "import_hidden_objects", text="Import Hidden Objects")
        box.prop(self, "import_hidden_layers", text="Import Hidden Layers")

        box = layout.box()
        box.label(text="📷 Cameras")
        row = box.row()
        row.prop(self, "import_views")
        row.prop(self, "import_named_views")

        box = layout.box()
        box.label(text="🎨 Materials")
        box.label(text="Material Handling:")
        box.prop(self, "material_handling", text="")
        box.prop(self, "link_materials_to")

        box = layout.box()
        box.label(text="📁 Groups → Collections")
        row = box.row()
        row.prop(self, "import_groups", text="Convert Groups")
        row.prop(self, "import_nested_groups", text="Nested Groups")

        box = layout.box()
        box.label(text="🔲 Grid Layout")
        box.prop(self, "import_instances_grid_layout")
        box.prop(self, "import_instances_grid")

        # Advanced section removed as merge_distance moved to Objects panel

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, _ : bpy.types.Context):
    self.layout.operator(Import3dm.bl_idname, text="Rhinoceros 3D (.3dm)")


def register():
    bpy.utils.register_class(Import3dm)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(Import3dm)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_3dm.some_data('INVOKE_DEFAULT')
