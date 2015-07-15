# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# TODO:

bl_info = {
    'name': 'Import/Export Westwood W3D Format (.w3d)',
    'author': 'Arathorn & Tarcontar',
    'version': (1, 0, 0),
    "blender": (2, 6, 0),
    "api": 36079,
    'location': 'File > Import/Export > Westerwood W3D (.w3d)',
    'description': 'Import or Export the Westerwood W3D-Format (.w3d)',
    'warning': 'Still in Progress',
	'tracker_url': 'http://forum.modding-union.com/index.php/topic,15838.0.html',
    'category': 'Import-Export'}

# To support reload properly, try to access a package var, if it's there,
# reload everything
if "bpy" in locals():
    import imp
    if 'import_w3d' in locals():
        imp.reload(import_w3d)
        imp.reload(struct_w3d)

    if 'export_w3d' in locals():
        imp.reload(export_w3d)
        imp.reload(struct_w3d)

import time
import datetime
import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper


class ImportW3D(bpy.types.Operator, ImportHelper):
    '''Import from Westwood 3D file format (.w3d)'''
    bl_idname = 'import_mesh.westwood_w3d'
    bl_label = 'Import W3D'
    bl_options = {'UNDO'}
	
    filename_ext = '.w3d'
    filter_glob = StringProperty(default='*.w3d', options={'HIDDEN'})
	
    bpy.types.Object.sklFile = bpy.props.StringProperty(name = 'sklFile', options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        from . import import_w3d
        print('Importing file', self.filepath)
        t = time.mktime(datetime.datetime.now().timetuple())
        with open(self.filepath, 'rb') as file:
            import_w3d.MainImport(self.filepath, context, self)
        t = time.mktime(datetime.datetime.now().timetuple()) - t
        print('Finished importing in', t, 'seconds')
        return {'FINISHED'}
		
available_objects = []
		
def availableObjects(self, context):   
    available_objects.clear() 
    for ob in bpy.data.objects:   
        name = ob.name   
        if ob.type == 'MESH' and not name == "skl_bone":
            available_objects.append((name, name, name))   
    return available_objects  

class ExportW3D(bpy.types.Operator, ExportHelper):
    '''Export from Westwood 3D file format (.w3d)'''
    bl_idname = 'export_mesh.westwood_w3d'
    bl_label = 'Export W3D'
    bl_options = {'UNDO'}
	
    filename_ext = '.w3d'
    filter_glob = StringProperty(default='*.w3d', options={'HIDDEN'})
	
    EXPORT_MODE = EnumProperty(
            name="Export Mode",
            items=(('HM', "Hierarchical Model", "this will export a model without animation data"),
                   #('HAM', "Hierarchical Animated Model", "this will export the model with geometry and animation data"),
                   #('PA', "Pure Animation", "this will export the animation without any geometry data"),
                   ('S', "Skeleton", "this will export the hierarchy tree without any geometry or animation data"),
                   ('SM', "Simple Mesh", "this will export a single mesh. if there is more than one mesh, only the first one will be exported")
                   ),
            default='HM',
            )
	
    USE_SKL_FILE = BoolProperty(
            name = "export using existing skeleton",
            description = "no new skeleton file is created",
            default = True
            )

    OBJECTS = EnumProperty(name="the single mesh to export", items = availableObjects)		
			
    def draw(self, context):
        available_objects = availableObjects(self, context)
        layout = self.layout

        layout.prop(self, "EXPORT_MODE"),
        sub = layout.column()
        if (self.EXPORT_MODE == 'HM') or (self.EXPORT_MODE == 'HAM') or (self.EXPORT_MODE == 'PA'):
            sub.enabled = True
        else:
            sub.enabled = False

        sub.prop(self, "USE_SKL_FILE")
		
        sub = layout.column()
        if (self.EXPORT_MODE == 'SM'):
            sub.enabled = True
        else:
            sub.enabled = False
        sub.prop(self, "OBJECTS")	
		
    def execute(self, context):
        from . import export_w3d
        keywords = self.as_keywords(ignore=("filter_glob", "check_existing", "filepath"))		

        print('Exporting file', self.filepath)
        t = time.mktime(datetime.datetime.now().timetuple())
        export_w3d.MainExport(self.filepath, context, self, **keywords) # add **keywords as param
        t = time.mktime(datetime.datetime.now().timetuple()) - t
        print('Finished exporting in', t, 'seconds')
        return {'FINISHED'}	
		
def menu_func_export(self, context):
    self.layout.operator(ExportW3D.bl_idname, text='Westwood W3D (.w3d)')

def menu_func_import(self, context):
    self.layout.operator(ImportW3D.bl_idname, text='Westwood W3D (.w3d)')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
