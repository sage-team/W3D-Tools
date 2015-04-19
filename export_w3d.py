import bpy
import operator
import struct
import os
import math
import sys
import bmesh
from bpy.props import *
from mathutils import Vector, Matrix, Quaternion
from . import struct_w3d

#######################################################################################
# Basic Methods
#######################################################################################

def WriteString(file, string):
	#TODO: check if it does write nullterminated strings
   	file.write(string)

def WriteFixedString(file, string):
	#truncate the string to 16
	nullbytes = 16-len(string)
	if(nullbytes<0):
		print("Warning: Fixed string is too long")

	file.write(bytes(string, 'UTF-8'))
	for i in range(nullbytes):
		file.write(struct.pack("B", 0))

def WriteLongFixedString(file, string):
	#truncate the string to 32
	nullbytes = 32-len(string)
	if(nullbytes<0):
		print("Warning: Fixed string is too long")

	file.write(bytes(string, 'UTF-8'))
	for i in range(nullbytes):
		file.write(struct.pack("B", 0))
		
def WriteRGBA(file, rgba):
    print(rgba.a)
    file.write(rgba.a)
    file.write('\x' + rgba[1])
    file.write(rgba[2])
    file.write(rgba[3])

def WriteByte(file, num):
    file.write(struct.pack("<B", num))

def WriteSignedByte(file, num):
    file.write(struct.pack("<´b", num))

def WriteShort(file, num):
    file.write(struct.pack("<H", num))

def WriteSignedShort(file, num):
    file.write(struct.pack("<h", num))

def WriteLong(file, num):
    file.write(struct.pack("<L", num))

def WriteSignedLong(file, num):
    file.write(struct.pack("<l", num))

def WriteFloat(file, num):
    file.write(struct.pack("<f", num))
	
def WriteVector(file, vec):
    WriteFloat(file, vec[0])
    WriteFloat(file, vec[1])
    WriteFloat(file, vec[2])
	
def WriteQuaternion(file, quat):
    #change order from wxyz to xyzw
    WriteFloat(file, quat[1])
    WriteFloat(file, quat[2])
    WriteFloat(file, quat[3])
    WriteFloat(file, quat[0])
	
def MakeVersion(version):
    return (((version.major) << 16) | (version.minor))
	
#######################################################################################
# Triangulate
#######################################################################################	

def triangulate(mesh):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces = bm.faces)
    bm.to_mesh(mesh)
    bm.free()

	
#######################################################################################
# Vertices
#######################################################################################
	
def WriteMeshVertArray(file, vertices, size):
    WriteLong(file, 2) #chunktype
    WriteLong(file, size) #chunksize
	
    for vert in vertices:
        WriteVector(file, vert)
		
#######################################################################################
# Normals
#######################################################################################
	
def WriteMeshNormArray(file, normals, size):
    WriteLong(file, 3) #chunktype
    WriteLong(file, size) #chunksize
	
    for norm in normals:
        WriteVector(file, norm)
	
#######################################################################################
# Faces
#######################################################################################	

def WriteMeshFaceArray(file, faces, size):
    WriteLong(file, 32) #chunktype
    WriteLong(file, size) #chunksize
	
    for face in faces:
        WriteLong(file, face.vertIDs[0])
        WriteLong(file, face.vertIDs[1])
        WriteLong(file, face.vertIDs[2])
        WriteLong(file, face.attrs)
        WriteVector(file, face.normal)
        WriteFloat(file, face.distance)
	
#######################################################################################
# Box
#######################################################################################	

def WriteBox(file, box):
    WriteLong(file, 1856) #chunktype
    WriteLong(file, 52) #chunksize
	
    WriteLong(file, MakeVersion(box.version)) 
    WriteLong(file, box.attributes)
    WriteLongFixedString(file, box.name)
    WriteRGBA(file, box.color)
    WriteVector(file, box.center)
    WriteVector(file, box.extend)
 	
#######################################################################################
# Mesh
#######################################################################################	

def WriteMeshHeader(file, header, size): 
    WriteLong(file, 31) #chunktype
    WriteLong(file, size) #chunksize
	
    WriteLong(file, MakeVersion(header.version)) 
    WriteFloat(file, header.attrs) 
    WriteFixedString(file, header.meshName)
    WriteFixedString(file, header.containerName)
    WriteLong(file, header.faceCount) 
    WriteLong(file, header.vertCount) 
    WriteLong(file, header.matlCount)
    WriteLong(file, header.damageStageCount)
    WriteLong(file, header.sortLevel)
    WriteLong(file, header.prelitVersion)
    WriteLong(file, header.futureCount) 
    WriteLong(file, header.vertChannelCount) 
    WriteLong(file, header.faceChannelCount) 
    WriteVector(file, header.minCorner) 
    WriteVector(file, header.maxCorner) 
    WriteVector(file, header.sphCenter) 
    WriteFloat(file, header.sphRadius) 
	
def WriteMesh(file, mesh):
    WriteLong(file, 0) #chunktype
	
    head = 8 #4(long = chunktype) + 4 (long = chunksize)
    headerSize = 116
    vertSize = len(mesh.verts)*3*4
    normSize = len(mesh.normals)*3*4
    faceSize = len(mesh.faces)*32
    size = head + headerSize + head + vertSize + head + normSize + head + faceSize
    WriteLong(file, size) #chunksize
	
    WriteMeshHeader(file, mesh.header, headerSize)
    WriteMeshVertArray(file, mesh.verts, vertSize)
    WriteMeshNormArray(file, mesh.normals, normSize)
    WriteMeshFaceArray(file, mesh.faces, faceSize)
	
#######################################################################################
# SKN file
#######################################################################################	

def WriteSkn(file, context):
    # Get all the mesh objects in the scene.
    objList = [object for object in bpy.context.scene.objects if object.type == 'MESH']
    containerName = (os.path.splitext(os.path.basename(file.name))[0]).upper()
    for mesh_ob in objList:
        print(mesh_ob.name)
        if mesh_ob.name == "BOUNDINGBOX":
            Box = struct_w3d.Box()
            ### Box.attributes = 0  ???
            Box.name = containerName + mesh_ob.name
            ### Box.color = TODO
            Box.center = mesh_ob.location
			
            WriteBox(file, Box)
        else:
            Mesh = struct_w3d.Mesh()
            Header = struct_w3d.MeshHeader()
		
            verts = []
            normals = [] 
            faces = []
            uvs = []

            Header.meshName = mesh_ob.name
            Header.containerName = containerName
            mesh = mesh_ob.to_mesh(bpy.context.scene, False, 'PREVIEW', calc_tessface = True)
		
            triangulate(mesh)
		
            Header.vertCount = len(mesh.vertices)
            for vert in mesh.vertices:
                verts.append(vert.co.xyz)
            Mesh.verts = verts
		
            for vert in mesh.vertices:
                normals.append(vert.normal)
            Mesh.normals = normals

            for face in mesh.polygons:
                triangle = struct_w3d.MeshFace()
                triangle.vertIDs = [face.vertices[0], face.vertices[1], face.vertices[2]]
                ### triangle.attrs = ??
                triangle.normal = face.normal
                ### triangle.distance = ?? 
                faces.append(triangle)
            Mesh.faces = faces

            #for uv_layer in mesh.uv_layers:
            #    for x in range(len(uv_layer.data)):
            #        uvs.append(uv_layer.data[x].uv)

            Mesh.header = Header			
            WriteMesh(file, Mesh)

#######################################################################################
# Main Export
#######################################################################################	

def MainExport(givenfilepath, self, context):
    print("Run Export")
	
	#switch to object mode
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
    file = open(givenfilepath,"wb")
	
    WriteSkn(file, context)
    	
