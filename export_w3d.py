#Written by Stephan Vedder and Michael Schnabel
#Last Modification 19.4.2015
#Exports the W3D Format used in games by Westwood & EA
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

#TODO 

#support for 2 bone vertex influences

#fix WriteRGBA method

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
    WriteUnsignedByte(file, rgba.r)
    WriteUnsignedByte(file, rgba.g)
    WriteUnsignedByte(file, rgba.b)
    WriteUnsignedByte(file, rgba.a)

def WriteLong(file, num):
    file.write(struct.pack("<L", num))

def WriteSignedLong(file, num):
    file.write(struct.pack("<l", num))	
	
def WriteShort(file, num):
    file.write(struct.pack("<H", num))
	
def WriteLongArray(file, array):
    print("todo: write Long array")
	
def WriteFloat(file, num):
    file.write(struct.pack("<f", num))

def WriteUnsignedByte(file, num):
    file.write(struct.pack("<b", num))

def WriteSignedShort(file, num):
    file.write(struct.pack("<h", num))
	
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

def WriteMeshVerticesArray(file, size, vertices):
    WriteLong(file, 2) #chunktype
    WriteLong(file, size) #chunksize
	
    for vert in vertices:
        WriteVector(file, vert)

def WriteMeshVertexInfluences(file, size, influences):
    WriteLong(file, 14) #chunktype
    WriteLong(file, size) #chunksize

    for inf in influences:
        WriteShort(file, inf.boneIdx)
        WriteShort(file, inf.xtraIdx)
        WriteShort(file, int(inf.boneInf))
        WriteShort(file, int(inf.xtraInf))		

#######################################################################################
# Normals
#######################################################################################
	
def WriteMeshNormalArray(file, size, normals):
    WriteLong(file, 3) #chunktype
    WriteLong(file, size) #chunksize
	
    for norm in normals:
        WriteVector(file, norm)
	
#######################################################################################
# Faces
#######################################################################################	

def WriteMeshFaceArray(file, size, faces):
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
# Materials
#######################################################################################	

def WriteW3DMaterial(file, size, mat):
    WriteLong(file, 44) #chunktype
    WriteLong(file, 16) #chunksize  #has to be size of the string
	
    WriteString(mat.vmName)
	
    WriteLong(file, 45) #chunktype
    WriteLong(file, size) #chunksize 
	
    WriteLong(file, mat.vmInfo.attributes)
    WriteRGBA(file, mat.vmInfo.ambient)
    WriteRGBA(file, mat.vmInfo.diffuse)
    WriteRGBA(file, mat.vmInfo.specular)
    WriteRGBA(file, mat.vmInfo.emissive)
    WriteFloat(file, mat.vmInfo.shininess)
    WriteFloat(file, mat.vmInfo.opacity)
    WriteFloat(file, mat.vmInfo.translucency)
	
    if vmArgs0size > 0:
        WriteLong(file, 46) #chunktype
        WriteLong(file, vmArgs0size) #chunksize 
        WriteString(file, mat.vmArgs0)
    
	if vmArgs1size > 0:
        WriteLong(file, 47) #chunktype
        WriteLong(file, vmArgs1size) #chunksize 
        WriteString(file, mat.vmArgs1)

def WriteMeshMaterialArray(file, size, matls):
    WriteLong(file, 43) #chunktype
    WriteLong(file, size) #chunksize

    for mat in mats:
        WriteW3DMaterial(fil, size, mat)
	
#######################################################################################
# Box
#######################################################################################	

def WriteBox(file, box):
    WriteLong(file, 1856) #chunktype
    WriteLong(file, 44) #chunksize
	
    WriteLong(file, MakeVersion(box.version)) 
    WriteLong(file, box.attributes)
    WriteLongFixedString(file, box.name)
    WriteRGBA(file, box.color)
    WriteVector(file, box.center)
    WriteVector(file, box.extend)
 	
#######################################################################################
# Mesh
#######################################################################################	

def WriteMeshHeader(file, size, header): 
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
    vertSize = len(mesh.verts)*12
    normSize = len(mesh.normals)*12
    faceSize = len(mesh.faces)*32
    infSize = len(mesh.vertInfs)*8
    matSize = len(mesh.vertMatls)
    size = head + headerSize + head + vertSize + head + normSize + head + faceSize + head + infSize + head + matSize
    WriteLong(file, size) #chunksize
	
    print("### NEW MESH: ###")
    WriteMeshHeader(file, headerSize, mesh.header)
    print("Header")
    WriteMeshVerticesArray(file, vertSize, mesh.verts)
    print("Vertices")
    WriteMeshNormalArray(file, normSize, mesh.normals)
    print("Normals")
    WriteMeshFaceArray(file, faceSize, mesh.faces)
    print("Faces")
    WriteMeshVertexInfluences(file, infSize, mesh.vertInfs) 
    print("Vertex Influences")
    WriteMeshVertexMaterials(file, matSize, mesh.vertMatls)
    print("Materials")
	
#######################################################################################
# SKN file
#######################################################################################	

def WriteSkn(file, context):
    # Get all the mesh objects in the scene.
    objList = [object for object in bpy.context.scene.objects if object.type == 'MESH']
    containerName = (os.path.splitext(os.path.basename(file.name))[0]).upper()
    for mesh_ob in objList:
        if mesh_ob.name == "BOUNDINGBOX":
            Box = struct_w3d.Box()
            ### Box.attributes = 0  ???
            Box.name = containerName + "." + mesh_ob.name
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
            vertInfs = []

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
			
            Header.faceCount = len(faces)
			
			#vertex influences
            group_lookup = {g.index: g.name for g in mesh_ob.vertex_groups}
            groups = {name: [] for name in group_lookup.values()}
            for v in mesh.vertices:
                if len(v.groups) > 0:
                    vertInf = struct_w3d.MeshVertInfs()
                    vertInf.boneIdx = v.groups[0].group
                    vertInf.boneInf = v.groups[0].weight * 100
                if len(v.groups) > 1:
                    vertInf.xtraIdx = v.groups[1].group
                    vertInf.xtraInf = v.groups[1].weight * 100
                if len(v.groups) > 2: 
                    context.report({'ERROR'}, "max 2 bone influences per vertex supported!")
                    print("Error: max 2 bone influences per vertex supported!")
                Mesh.vertInfs.append(vertInf)
				
            for mat in mesh.materials:
                print(mat.name)
                

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