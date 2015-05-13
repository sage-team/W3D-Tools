#Written by Stephan Vedder and Michael Schnabel
#Last Modification 13.5.2015
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

#recalculate size of vertex material chunk

#support for 2 bone vertex influences


HEAD = 8 #4(long = chunktype) + 4 (long = chunksize)

#######################################################################################
# Basic Methods
#######################################################################################

def WriteString(file, string):
	#TODO: check if it does write nullterminated strings
    file.write(bytes(string, 'UTF-8'))
	#write binary 0 to file
    file.write(struct.pack('B', 0))

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
    file.write(struct.pack("B", rgba.r))
    file.write(struct.pack("B", rgba.g))
    file.write(struct.pack("B", rgba.b))
    file.write(struct.pack("B", rgba.a))

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
    #changes the order from wxyz to xyzw
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
# Hierarchy
#######################################################################################

def WriteHierarchyHeader(file, size, header):
    WriteLong(file, 257) #chunktype
    WriteLong(file, size) #chunksize
	
    WriteLong(file, MakeVersion(header.version))
    WriteFixedString(file, header.name)
    WriteLong(file, header.pivotCount)
    WriteVector(file, header.centerPos)

def WritePivots(file, size, pivots):
    WriteLong(file, 258) #chunktype
    WriteLong(file, size) #chunksize
	
    for pivot in pivots:
        WriteFixedString(file, pivot.name)
        WriteSignedLong(file, pivot.parentID)
        WriteVector(file, pivot.position)
        WriteVector(file, pivot.eulerAngles)
        WriteQuaternion(file, pivot.rotation)

def WritePivotFixups(file, size, pivot_fixups):
    WriteLong(file, 259) #chunktype
    WriteLong(file, size) #chunksize
	
    for fixup in pivot_fixups: 
        WriteVector(file, fixup)

def WriteHierarchy(file, hierarchy):
    WriteLong(file, 256) #chunktype
    
    headerSize = 36
    pivotsSize = len(hierarchy.pivots)*60
    pivotFixupsSize = len(hierarchy.pivot_fixups)*12
    size = HEAD + headerSize + HEAD + pivotsSize + HEAD + pivotFixupsSize 
	
    WriteLong(file, size) #chunksize
	
    print("### NEW HIERARCHY: ###")
    WriteHierarchyHeader(file, headerSize, hierarchy.header)
    print("Header")
    WritePivots(file, pivotsSize, hierarchy.pivots)
    print("Pivots")
    WritePivotFixups(file, pivotFixupsSize, hierarchy.pivot_fixups)
    print("Pivot Fixups")
	
#######################################################################################
# HLod
#######################################################################################

def WriteHLodHeader(file, size, header):
    WriteLong(file, 1793) #chunktype
    WriteLong(file, size) #chunksize
	
    WriteLong(file, MakeVersion(header.version))
    WriteLong(file, header.lodCount)
    WriteFixedString(file, header.modelName)
    WriteFixedString(file, header.HTreeName)

def WriteHLodArrayHeader(file, size, arrayHeader):
    WriteLong(file, 1795) #chunktype
    WriteLong(file, size) #chunksize
	
    WriteLong(file, arrayHeader.modelCount)
    WriteFloat(file, arrayHeader.maxScreenSize)

def WriteHLodSubObject(file, size, subObject): 
    WriteLong(file, 1796) #chunktype
    WriteLong(file, size) #chunksize
	
    WriteLong(file, subObject.boneIndex)
    WriteLongFixedString(file, subObject.name)

def WriteHLodArray(file, size, lodArray, headerSize, subObjectSize):
    WriteLong(file, 1794) #chunktype
    WriteLong(file, size) #chunksize
	
    WriteHLodArrayHeader(file, headerSize, lodArray.header)
    for object in lodArray.subObjects:
        WriteHLodSubObject(file, subObjectSize, object)

def WriteHLod(file, hlod):
    WriteLong(file, 1792) #chunktype
	
    headerSize = 40
    arrayHeaderSize = 8
    subObjectSize = 36 
    arraySize = HEAD + arrayHeaderSize + (HEAD + subObjectSize) * len(hlod.lodArray.subObjects)
    size = HEAD + headerSize + HEAD + arraySize
	
    WriteLong(file, size) #chunksize
	
    print("### NEW HLOD: ###")
    WriteHLodHeader(file, headerSize, hlod.header)
    print("Header")
    WriteHLodArray(file, arraySize, hlod.lodArray, arrayHeaderSize, subObjectSize)
    print("Array")
	
#######################################################################################
# Box
#######################################################################################	

def WriteBox(file, box):
    WriteLong(file, 1856) #chunktype
    WriteLong(file, 68) #chunksize
	
    WriteLong(file, MakeVersion(box.version)) 
    WriteLong(file, box.attributes)
    WriteLongFixedString(file, box.name)
    WriteRGBA(file, box.color)
    WriteVector(file, box.center)
    WriteVector(file, box.extend)
	
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

def WriteW3DMaterial(file, mat):
    WriteLong(file, 44) #chunktype
    WriteLong(file, len(mat.vmName)+1) #chunksize  #has to be size of the string plus binary 0
	
    WriteString(file, mat.vmName)
	
    WriteLong(file, 45) #chunktype
    WriteLong(file, 32) #chunksize 
	
    WriteLong(file, mat.vmInfo.attributes)
    WriteRGBA(file, mat.vmInfo.ambient)
    WriteRGBA(file, mat.vmInfo.diffuse)
    WriteRGBA(file, mat.vmInfo.specular)
    WriteRGBA(file, mat.vmInfo.emissive)
    WriteFloat(file, mat.vmInfo.shininess)
    WriteFloat(file, mat.vmInfo.opacity)
    WriteFloat(file, mat.vmInfo.translucency)
	
    if len(mat.vmArgs0) > 0:
        WriteLong(file, 46) #chunktype
        WriteLong(file, len(mat.vmArgs0)+1) #chunksize 
        WriteString(file, mat.vmArgs0)
    
    if len(mat.vmArgs1) > 0:
        WriteLong(file, 47) #chunktype
        WriteLong(file, len(mat.vmArgs1)+1) #chunksize 
        WriteString(file, mat.vmArgs1)

def WriteMeshMaterialArray(file, size, matls):
    WriteLong(file, 43) #chunktype
    WriteLong(file, size) #chunksize

    for mat in matls:
        WriteW3DMaterial(file, mat)
 	
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
	
    headerSize = 116
    vertSize = len(mesh.verts)*12
    normSize = len(mesh.normals)*12
    faceSize = len(mesh.faces)*32
    infSize = len(mesh.vertInfs)*8
    matSize =  HEAD + len(mesh.vertMatls[0].vmName) + 1 + HEAD + 34 + HEAD + len(mesh.vertMatls[0].vmArgs0) + 1 + HEAD + len(mesh.vertMatls[0].vmArgs1) + 1
	
    size = HEAD + headerSize + HEAD + vertSize + HEAD + normSize + HEAD + faceSize + HEAD + infSize + HEAD + matSize
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
    WriteMeshMaterialArray(file, matSize, mesh.vertMatls)
    print("Materials")
	
#######################################################################################
# SKN file
#######################################################################################	

def WriteSknFile(file, context):
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
            #get box extend
            #Box.extend = 
			
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
                vertInf = struct_w3d.MeshVertexInfluences()
                if len(v.groups) > 0:
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
                meshMaterial = struct_w3d.MeshMaterial()
                
                meshMaterial.vmName = (os.path.splitext(os.path.basename(mat.name))[1])[1:]
                meshVMInfo = struct_w3d.VertexMaterial()
				
                meshMaterial.vmInfo = meshVMInfo
                Mesh.vertMatls.append(meshMaterial)

            Mesh.header = Header			
            WriteMesh(file, Mesh)
			
    HLod = struct_w3d.HLod()
    WriteHLod(file, HLod)

    Hierarchy = struct_w3d.Hierarchy()
    WriteHierarchy(file, Hierarchy)

#######################################################################################
# Main Export
#######################################################################################	

def MainExport(givenfilepath, self, context):
    print("Run Export")
	
	#switch to object mode
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
    sknFile = open(givenfilepath,"wb")
	
    WriteSknFile(sknFile, context) 
	
    sknFile.close()