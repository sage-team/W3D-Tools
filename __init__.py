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

bl_info = {
    'name': 'Import Westwood W3D Format (.w3d)',
    'author': 'Arathorn',
    'version': (0, 1, 1),
    "blender": (2, 6, 0),
    "api": 36079,
    'location': 'File > Import > Westerwood W3D (.w3d)',
    'description': 'Imports the Westerwood W3D-Format (.w3d)',
    'warning': 'Still in Progress',
	'tracker_url': 'http://forum.modding-union.com/index.php/topic,15838.0.html',
    'category': 'Import-Export'}

# To support reload properly, try to access a package var, if it's there,
# reload everything
if "bpy" in locals():
    import imp
    if 'import_w3d' in locals():
        imp.reload(import_w3d)

import time
import datetime
import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper


class ImportW3D(bpy.types.Operator, ImportHelper):
    '''Import from Westerwood 3D file format (.w3d)'''
    bl_idname = 'import_mesh.westerwood_w3d'
    bl_label = 'Import W3D'
    bl_options = {'UNDO'}

    filename_ext = '.w3d'
    filter_glob = StringProperty(default='*.w3d', options={'HIDDEN'})

    def execute(self, context):
        from . import import_w3d
        print('Importing file', self.filepath)
        t = time.mktime(datetime.datetime.now().timetuple())
        with open(self.filepath, 'rb') as file:
            import_w3d.MainImport(self.filepath, context, self)
        t = time.mktime(datetime.datetime.now().timetuple()) - t
        print('Finished importing in', t, 'seconds')
        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportW3D.bl_idname, text='Westwood W3D (.w3d)')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
#   bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
#   bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
