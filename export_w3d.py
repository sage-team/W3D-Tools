#Written by Stephan Vedder and Michael Schnabel
#Last Modification 10.07.2015
#Exports the W3D Format used in games by Westwood & EA
import bpy
import operator
import struct
import os
import math
import sys
import bmesh
from bpy.props import *
from mathutils import Vector, Quaternion
from . import struct_w3d, import_w3d

#TODO 

# support for export with existing skeleton file! (test if all the pivots exist and are equal)

# support for export as simple mesh (without HLOD and Hierarchy)

# write AABTree to file

# change test if we need to write normal map chunk

# fix sphere calculation

# export animation data (when import works)


HEAD = 8 #4(long = chunktype) + 4 (long = chunksize)

#######################################################################################
# Basic Methods
#######################################################################################

def WriteString(file, string):
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
	
# only if the chunk has subchunks -> else: WriteLong(file, data)
def MakeChunkSize(data):
    return (data | 0x80000000)

def WriteLong(file, num):
    file.write(struct.pack("<L", num))

def WriteSignedLong(file, num):
    file.write(struct.pack("<l", num))	
	
def WriteShort(file, num):
    file.write(struct.pack("<H", num))
	
def WriteLongArray(file, array):
    for a in array:
        WriteLong(file, a)

def WriteFloat(file, num):
    file.write(struct.pack("<f", num))
	
def WriteSignedByte(file, num):
    file.write(struct.pack("<b", num))

def WriteUnsignedByte(file, num):
    file.write(struct.pack("<B", num))
	
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
    #print("\n### NEW HIERARCHY: ###")
    WriteLong(file, 256) #chunktype
    
    headerSize = 36
    pivotsSize = len(hierarchy.pivots) * 60
    pivotFixupsSize = len(hierarchy.pivot_fixups) * 12
    size = HEAD + headerSize + HEAD + pivotsSize 
    if pivotFixupsSize > 0:
        size += HEAD + pivotFixupsSize 

    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    WriteHierarchyHeader(file, headerSize, hierarchy.header)
    #print("Header")
    WritePivots(file, pivotsSize, hierarchy.pivots)
    #print("Pivots")
	# still dont know what pivotFixups are for and what they are
    if pivotFixupsSize > 0:
        WritePivotFixups(file, pivotFixupsSize, hierarchy.pivot_fixups)
        print("Pivot Fixups")
	
#######################################################################################
# Animation
#######################################################################################
	
def WriteAnimationHeader(file, size, header):
    WriteLong(file, 513) #chunktype
    WriteLong(file, size) #chunksize

    WriteLong(file, MakeVersion(header.version))
    WriteFixedString(file, header.name)
    WriteFixedString(file, header.hieraName)
    WriteLong(file, header.numFrames)
    WriteLong(file, header.frameRate)

def WriteAnimationChannel(file, channel):
    WriteLong(file, 514) #chunktype
    size = 12 + (len(channel.data) * channel.vectorLen) * 4
    WriteLong(file, size) #chunksize
	
    WriteShort(file, channel.firstFrame)
    WriteShort(file, channel.lastFrame)
    WriteShort(file, channel.vectorLen)
    WriteShort(file, channel.type)
    WriteShort(file, channel.pivot)
    WriteShort(file, channel.pad)

    if channel.vectorLen == 1:
        for f in channel.data:
            WriteFloat(file, f)
    elif channel.vectorLen == 4:
        for quat in channel.data:
            WriteQuaternion(file, quat)

def WriteAnimation(file, animation):
    #print("\n### NEW ANIMATION: ###")
    WriteLong(file, 512) #chunktype
	
    headerSize = 44
    channelsSize = len(animation.channels) * (12 + HEAD)
    for channel in animation.channels:
        channelsSize += (len(channel.data) * channel.vectorLen) * 4
    size = HEAD + headerSize + channelsSize		
	
    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    WriteAnimationHeader(file, headerSize, animation.header)
    #print("Header")
    for channel in animation.channels:
        WriteAnimationChannel(file, channel)
        print("Channel")
			
def WriteCompressedAnimationHeader(file, size, header):
    WriteLong(file, 641) #chunktype
    WriteLong(file, size) #chunksize

    WriteLong(file, MakeVersion(header.version))
    WriteFixedString(file, header.name)
    WriteFixedString(file, header.hieraName)
    WriteLong(file, header.numFrames)
    WriteShort(file, header.frameRate)
    WriteShort(file, header.flavor)
	
def WriteTimeCodedAnimVector(file, size, animVector):
    WriteLong(file, 644) #chunktype
    WriteLong(file, size) #chunksize
	
    print("#####not implemented yet!!")
   	
def WriteCompressedAnimation(file, compAnimation):
    #print("\n### NEW COMPRESSED ANIMATION: ###")
    WriteLong(file, 640) #chunktype
	
    headerSize = 44
    vectorsSize = 0
    #for vec in compAnimation.animVectors:
        #vectorsSize += HEAD + 
    size = HEAD + headerSize #+ vectorsSize
	
    WriteLong(file, size) #chunksize

    WriteCompressedAnimationHeader(file, headerSize, compAnimation.header)	
    #print("Header")
    #for vec in compAnimation.animVectors:
        #WriteTimeCodedAnimVector(file, vec)
        #print("AnimVector")
	
#######################################################################################
# HLod
#######################################################################################

def WriteHLodHeader(file, size, header):
    WriteLong(file, 1793) #chunktype
    WriteLong(file, size) #chunksize
	
    WriteLong(file, MakeVersion(header.version))
    WriteLong(file, header.lodCount)
    WriteFixedString(file, header.modelName)
    WriteFixedString(file, "GUMAARMS_SKL") #header.HTreeName

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
    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    WriteHLodArrayHeader(file, headerSize, lodArray.header)
    for object in lodArray.subObjects:
        WriteHLodSubObject(file, subObjectSize, object)

def WriteHLod(file, hlod):
    #print("\n### NEW HLOD: ###")
    WriteLong(file, 1792) #chunktype
	
    headerSize = 40
    arrayHeaderSize = 8
    subObjectSize = 36 
    arraySize = HEAD + arrayHeaderSize + (HEAD + subObjectSize) * len(hlod.lodArray.subObjects)
    size = HEAD + headerSize + HEAD + arraySize
	
    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    WriteHLodHeader(file, headerSize, hlod.header)
    #print("Header")
    WriteHLodArray(file, arraySize, hlod.lodArray, arrayHeaderSize, subObjectSize)
    #print("Array")
	
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
# Texture
#######################################################################################	
	
def WriteTexture(file, texture):
    #print(texture.name)
    WriteLong(file, 49) #chunktype
    WriteLong(file,  MakeChunkSize(HEAD + len(texture.name) + 1))# + HEAD + 12)) #chunksize
	
    WriteLong(file, 50) #chunktype
    WriteLong(file, len(texture.name) + 1) #chunksize
    
    WriteString(file, texture.name)
	
    #WriteLong(file, 51) #chunktype
    #WriteLong(file, 12) #chunksize 
	
    #WriteShort(file, texture.textureInfo.attributes)
    #WriteShort(file, texture.textureInfo.animType)
    #WriteLong(file, texture.textureInfo.frameCount)
    #WriteFloat(file, texture.textureInfo.frameRate)

def WriteTextureArray(file, size, textures):
    WriteLong(file, 48) #chunktype
    WriteLong(file, MakeChunkSize(size)) #chunksize  
	
    for texture in textures:
        WriteTexture(file, texture)
		
#######################################################################################
# Material
#######################################################################################	

def WriteMeshTextureCoordArray(file, txCoords):
    WriteLong(file, 74) #chunktype
    WriteLong(file, len(txCoords) * 8) #chunksize 
    for coord in txCoords:
        WriteFloat(file, coord[0])
        WriteFloat(file, coord[1])

def WriteMeshTextureStage(file, size, textureStage):
    WriteLong(file, 72) #chunktype
    WriteLong(file, MakeChunkSize(size)) #chunksize  
	
    WriteLong(file, 73) #chunktype
    WriteLong(file, len(textureStage.txIds) * 4) #chunksize 
    WriteLongArray(file, textureStage.txIds)
	
    WriteMeshTextureCoordArray(file, textureStage.txCoords)

def WriteMeshMaterialPass(file, size, matlPass):
    WriteLong(file, 56) #chunktype
    WriteLong(file, MakeChunkSize(size)) #chunksize  
	
    WriteLong(file, 57) #chunktype
    WriteLong(file, len(matlPass.vmIds) * 4) #chunksize  

    WriteLongArray(file, matlPass.vmIds)
 
    WriteLong(file, 58) #chunktype
    WriteLong(file, len(matlPass.shaderIds) * 4) #chunksize 
	
    WriteLongArray(file, matlPass.shaderIds)
	
    if len(matlPass.dcg) > 0:
        WriteLong(file, 59) #chunktype
        WriteLong(file, len(matlPass.dcg) * 4) #chunksize 
 
        for dcg in matlPass.dcg: 
            WriteRGBA(file, dcg)
	
    if len(matlPass.txStage.txIds) > 0:
        WriteMeshTextureStage(file, HEAD + len(matlPass.txStage.txIds) * 4 + HEAD + len(matlPass.txStage.txCoords) * 8, matlPass.txStage)

def WriteMaterial(file, mat):
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
        WriteLong(file, len(mat.vmArgs0) + 1) #chunksize 
        WriteString(file, mat.vmArgs0)
    
    if len(mat.vmArgs1) > 0:
        WriteLong(file, 47) #chunktype
        WriteLong(file, len(mat.vmArgs1) + 1) #chunksize 
        WriteString(file, mat.vmArgs1)

def WriteMeshMaterialArray(file, size, materials):
    WriteLong(file, 42) #chunktype
    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    WriteLong(file, 43) #chunktype
    WriteLong(file, MakeChunkSize(size - HEAD)) #chunksize

    for mat in materials:
        WriteMaterial(file, mat)
		
def WriteMeshMaterialSetInfo (file, size, matSetInfo):
    WriteLong(file, 40) #chunktype
    WriteLong(file, size) #chunksize
	
    WriteLong(file, matSetInfo.passCount)
    WriteLong(file, matSetInfo.vertMatlCount)
    WriteLong(file, matSetInfo.shaderCount)
    WriteLong(file, matSetInfo.textureCount)
	
#######################################################################################
# Vertices
#######################################################################################

def WriteMeshVerticesArray(file, size, vertices):
    WriteLong(file, 2) #chunktype
    WriteLong(file, size) #chunksize
	
    for vert in vertices:
        WriteVector(file, vert)
		
def WriteMeshVerticesCopyArray(file, size, vertices):
    WriteLong(file, 3072) #chunktype
    WriteLong(file, size) #chunksize
	
    for vert in vertices:
        WriteVector(file, vert)

def WriteMeshVertexInfluences(file, size, influences):
    WriteLong(file, 14) #chunktype
    WriteLong(file, size) #chunksize

    for inf in influences:
        WriteShort(file, inf.boneIdx)
        WriteShort(file, inf.xtraIdx)
        WriteShort(file, int(inf.boneInf * 100))
        WriteShort(file, int(inf.xtraInf * 100))		

#######################################################################################
# Normals
#######################################################################################
	
def WriteMeshNormalArray(file, size, normals):
    WriteLong(file, 3) #chunktype
    WriteLong(file, size) #chunksize
	
    for norm in normals:
        WriteVector(file, norm)
		
def WriteMeshNormalCopyArray(file, size, normals):
    WriteLong(file, 3073) #chunktype
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
        WriteLong(file, face.vertIds[0])
        WriteLong(file, face.vertIds[1])
        WriteLong(file, face.vertIds[2])
        WriteLong(file, face.attrs)
        WriteVector(file, face.normal)
        WriteFloat(file, face.distance)
		
#######################################################################################
# Shader
#######################################################################################
	
def WriteMeshShaderArray(file, size, shaders):
    WriteLong(file, 41) #chunktype
    WriteLong(file, size) #chunksize
    for shader in shaders:
        WriteUnsignedByte(file, shader.depthCompare)
        WriteUnsignedByte(file, shader.depthMask)
        WriteUnsignedByte(file, shader.colorMask)
        WriteUnsignedByte(file, shader.destBlend)
        WriteUnsignedByte(file, shader.fogFunc)		
        WriteUnsignedByte(file, shader.priGradient)
        WriteUnsignedByte(file, shader.secGradient)
        WriteUnsignedByte(file, shader.srcBlend)
        WriteUnsignedByte(file, shader.texturing)
        WriteUnsignedByte(file, shader.detailColorFunc)
        WriteUnsignedByte(file, shader.detailAlphaFunc)		
        WriteUnsignedByte(file, shader.shaderPreset)
        WriteUnsignedByte(file, shader.alphaTest)
        WriteUnsignedByte(file, shader.postDetailColorFunc)
        WriteUnsignedByte(file, shader.postDetailAlphaFunc)
        WriteUnsignedByte(file, shader.pad)
		
#######################################################################################
# Bump Maps
#######################################################################################
	
def WriteNormalMapHeader(file, header): 
    WriteLong(file, 82) #chunktype
    WriteLong(file, 37) #chunksize
	
    WriteSignedByte(file, header.number)
    WriteLongFixedString(file, header.typeName)
    WriteLong(file, header.reserved)

def WriteNormalMapEntryStruct(file, entryStruct): 
    WriteLong(file, 83) #chunktype
    WriteLong(file, 4 + 4 + len("DiffuseTexture") + 1 + 4 + len(entryStruct.diffuseTexName) + 1) #chunksize
    WriteLong(file, 1) #texture type
    WriteLong(file, len("DiffuseTexture") + 1) 
    WriteString(file, "DiffuseTexture")
    WriteLong(file, 1) #unknown value
    WriteString(file, entryStruct.diffuseTexName)
	
    WriteLong(file, 83) #chunktype
    WriteLong(file, 4 + 4 + len("NormalMap") + 1 + 4 + len(entryStruct.normalMap) + 1) #chunksize
    WriteLong(file, 1) #texture type
    WriteLong(file, len("NormalMap") + 1) 
    WriteString(file, "NormalMap")
    WriteLong(file, 1) #unknown value
    WriteString(file, entryStruct.normalMap)
	
    WriteLong(file, 83) #chunktype
    WriteLong(file, 4 + 4 + len("BumpScale") + 1 + 4) #chunksize
    WriteLong(file, 2) #bumpScale
    WriteLong(file, len("BumpScale") + 1) 
    WriteString(file, "BumpScale")
    WriteFloat(file, entryStruct.bumpScale)
	
    WriteLong(file, 83) #chunktype
    WriteLong(file, 4 + 4 + len("AmbientColor") + 1 + 16) #chunksize
    WriteLong(file, 5) #color
    WriteLong(file, len("AmbientColor") + 1) 
    WriteString(file, "AmbientColor")
    WriteFloat(file, entryStruct.ambientColor[0])
    WriteFloat(file, entryStruct.ambientColor[1])
    WriteFloat(file, entryStruct.ambientColor[2])
    WriteFloat(file, entryStruct.ambientColor[3])
	
    WriteLong(file, 83) #chunktype
    WriteLong(file, 4 + 4 + len("DiffuseColor") + 1 + 16) #chunksize
    WriteLong(file, 5) #color
    WriteLong(file, len("DiffuseColor") + 1) 
    WriteString(file, "DiffuseColor")
    WriteFloat(file, entryStruct.diffuseColor[0])
    WriteFloat(file, entryStruct.diffuseColor[1])
    WriteFloat(file, entryStruct.diffuseColor[2])
    WriteFloat(file, entryStruct.diffuseColor[3])
	
    WriteLong(file, 83) #chunktype
    WriteLong(file, 4 + 4 + len("SpecularColor") + 1 + 16) #chunksize
    WriteLong(file, 5) #color
    WriteLong(file, len("SpecularColor") + 1) 
    WriteString(file, "SpecularColor")
    WriteFloat(file, entryStruct.specularColor[0])
    WriteFloat(file, entryStruct.specularColor[1])
    WriteFloat(file, entryStruct.specularColor[2])
    WriteFloat(file, entryStruct.specularColor[3])
	
    WriteLong(file, 83) #chunktype
    WriteLong(file, 4 + 4 + len("SpecularExponent") + 1 + 4) #chunksize
    WriteLong(file, 2) #specularExponent
    WriteLong(file, len("SpecularExponent") + 1) 
    WriteString(file, "SpecularExponent")
    WriteFloat(file, entryStruct.specularExponent)
	
    WriteLong(file, 83) #chunktype
    WriteLong(file, 4 + 4 + len("AlphaTestEnable") + 1 + 1) #chunksize
    WriteLong(file, 7) #alphaTest
    WriteLong(file, len("AlphaTestEnable") + 1) 
    WriteString(file, "AlphaTestEnable")
    WriteUnsignedByte(file, entryStruct.alphaTestEnable)

def WriteNormalMap(file, normalMap):
    WriteLong(file, 81) #chunktype
    WriteLong(file, 45 + 301 + len(normalMap.entryStruct.diffuseTexName) + 1 + len(normalMap.entryStruct.normalMap) + 1) #chunksize

    WriteNormalMapHeader(file, normalMap.header)
    WriteNormalMapEntryStruct(file, normalMap.entryStruct)
	
def WriteMeshBumpMapArray(file, size, bumpMapArray):
    WriteLong(file, 80) #chunktype
    WriteLong(file, MakeChunkSize(size)) #chunksize

    WriteNormalMap(file, bumpMapArray.normalMap)
	
#######################################################################################
# AABTree (Axis-aligned-bounding-box)
#######################################################################################	

def WriteAABTreeHeader(file, size, header):
    WriteLong(file, 145) #chunktype
    WriteLong(file, size) #chunksize

    WriteLong(file, header.nodeCount)
    WriteLong(file, header.polyCount)

def WriteAABTreePolyIndices(file, size, polyIndices):
    WriteLong(file, 146) #chunktype
    WriteLong(file, size) #chunksize
	
    for poly in polyIndices:
        WriteLong(file, poly)

def WriteAABTreeNodes(file, size, nodes):
    WriteLong(file, 147) #chunktype
    WriteLong(file, size) #chunksize
	
    for node in nodes:
        WriteVector(file, node.min)
        WriteVector(file, node.max)
        WriteLong(file, node.frontOrPoly0)
        WriteLong(file, node.backOrPolyCount)

def WriteAABTree(file, size, aabtree):
    WriteLong(file, 144) #chunktype
    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    headerSize = 8
    WriteAABTreeHeader(file, headerSize, aabtree.header)
    
    polySize = len(aabtree.polyIndices) * 4
    if polySize > 0:
        WriteAABTreePolyIndices(file, polySize, aabtree.polyIndices)
	
    nodeSize = len(aabtree.nodes) * 32
    if nodeSize > 0:
        WriteAABTreeNodes(file, nodeSize, aabtree.nodes)
		
#######################################################################################
# Mesh
#######################################################################################	

def WriteMeshHeader(file, size, header): 
    WriteLong(file, 31) #chunktype
    WriteLong(file, size) #chunksize
	
    #print("## Name: " + header.meshName)
    WriteLong(file, MakeVersion(header.version)) 
    WriteLong(file, header.attrs) 
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
    #print("\n### NEW MESH: ###")
    WriteLong(file, 0) #chunktype
	
    headerSize = 116
    vertSize = len(mesh.verts) * 12
    vertCopySize = len(mesh.verts_copy) * 12
    normSize = len(mesh.normals) * 12
    normCopySize = len(mesh.normals_copy) * 12
    faceSize = len(mesh.faces) * 32
    shadeIndicesSize = len(mesh.verts) * 4
    userTextSize = 0
    if not mesh.userText ==  "":
        userTextSize = len(mesh.userText) + 1
    infSize = len(mesh.vertInfs) * 8
    matSetInfoSize = 16
    matArraySize = HEAD
    textureArraySize = HEAD

    for mat in mesh.vertMatls: 
        matArraySize += HEAD + len(mat.vmName) + 1 + HEAD + 32
        if len(mat.vmArgs0) > 0:
            matArraySize += HEAD + len(mat.vmArgs0) + 1
        if len(mat.vmArgs1) > 0:
            matArraySize += HEAD + len(mat.vmArgs1) + 1
			
        if not mat.vmName == "":
            for tex in mesh.textures:
               textureArraySize += HEAD + len(tex.name) + 1 #+ HEAD + 12
     
    shaderArraySize = len(mesh.shaders) * 16
	 
    materialPassSize = (HEAD + len(mesh.matlPass.vmIds) * 4 + HEAD + len(mesh.matlPass.shaderIds) * 4)
    if len(mesh.matlPass.dcg) > 0:
        materialPassSize += HEAD + len(mesh.matlPass.dcg) * 4
    if len(mesh.matlPass.txStage.txIds) > 0:		
        materialPassSize += HEAD + HEAD + len(mesh.matlPass.txStage.txIds) * 4 + HEAD + len(mesh.matlPass.txStage.txCoords) * 8
    bumpMapArraySize = (HEAD + 45 + 301 + len(mesh.bumpMaps.normalMap.entryStruct.diffuseTexName) + 1 + len(mesh.bumpMaps.normalMap.entryStruct.normalMap) + 1)
	
    aabtreeSize = HEAD + 8	
    if mesh.aabtree.header.polyCount > 0:
        aabtreeSize += HEAD + len(mesh.aabtree.polyIndices) * 4
    if mesh.aabtree.header.nodeCount > 0:
        aabtreeSize += HEAD + len(mesh.aabtree.nodes) * 32
	
	#size of the mesh chunk
    size = HEAD + headerSize 
    size += HEAD + vertSize 
    if vertCopySize > 0:
        size += HEAD + vertCopySize
    size += HEAD + normSize 
    if  normCopySize > 0:
        size += HEAD + normCopySize
    size += HEAD + faceSize 
    size += HEAD + shadeIndicesSize
    if not mesh.userText ==  "":
        size += HEAD + userTextSize
    if len(mesh.vertInfs) > 0:
        size += HEAD + infSize 
    size += HEAD + matSetInfoSize 
    if mesh.matInfo.vertMatlCount > 0:
        size += HEAD + matArraySize
    if mesh.matInfo.textureCount > 0:
        size += HEAD + textureArraySize 
    if mesh.matInfo.shaderCount > 0:
        size += HEAD + shaderArraySize
    if mesh.matInfo.passCount > 0:
        size += HEAD + materialPassSize
    if not mesh.bumpMaps.normalMap.entryStruct.diffuseTexName == "":
        size += HEAD + bumpMapArraySize
    if (mesh.aabtree.header.nodeCount > 0) or (mesh.aabtree.header.polyCount > 0):
        size += HEAD + aabtreeSize
    
    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    WriteMeshHeader(file, headerSize, mesh.header)
    #print("Header")
    WriteMeshVerticesArray(file, vertSize, mesh.verts)
    #print("Vertices")
    if vertCopySize > 0:
        WriteMeshVerticesCopyArray(file, vertCopySize, mesh.verts_copy)
        #print("Vertices Copy")
    WriteMeshNormalArray(file, normSize, mesh.normals)
    #print("Normals")
    if normCopySize > 0:
        WriteMeshNormalCopyArray(file, normCopySize, mesh.normals_copy)
        #print("Normals Copy")
    WriteMeshFaceArray(file, faceSize, mesh.faces)
    #print("Faces")
    if not mesh.userText ==  "":
        WriteLong(file, 12) #chunktype
        WriteLong(file, userTextSize) #chunksize
        WriteString(file, mesh.userText)
        #print("UserText")
    if len(mesh.vertInfs) > 0:
        WriteMeshVertexInfluences(file, infSize, mesh.vertInfs) 
        #print("Vertex Influences")
		
    WriteLong(file, 34) #chunktype
    WriteLong(file, shadeIndicesSize) #chunksize
    WriteLongArray(file, mesh.shadeIds)
    #print("VertexShadeIndices")
	
    WriteMeshMaterialSetInfo(file, matSetInfoSize, mesh.matInfo)
    #print("MaterialSetInfo")
    if mesh.matInfo.vertMatlCount > 0:
        WriteMeshMaterialArray(file, matArraySize, mesh.vertMatls)
        #print("Materials")
    if mesh.matInfo.shaderCount > 0:
        WriteMeshShaderArray(file, shaderArraySize, mesh.shaders)
        #print("Shader")
    if mesh.matInfo.textureCount > 0:
        WriteTextureArray(file, textureArraySize, mesh.textures)
        #print("Textures")
    if mesh.matInfo.passCount > 0:
        WriteMeshMaterialPass(file, materialPassSize, mesh.matlPass)
        #print("MaterialPass")
    if not mesh.bumpMaps.normalMap.entryStruct.normalMap == "":
        WriteMeshBumpMapArray(file, bumpMapArraySize, mesh.bumpMaps)
        #print("BumpMaps")
    if (mesh.aabtree.header.nodeCount > 0) or (mesh.aabtree.header.polyCount > 0):
        WriteAABTree(file, aabtreeSize, mesh.aabtree)
        #print("AABTree")
		
#######################################################################################
# Mesh Sphere
#######################################################################################	

def calculateMeshSphere(mesh, Header):
    # get the point with the biggest distance to x and store it in y
    x = mesh.vertices[0]
    y = mesh.vertices[1]
    dist = ((y.co[0] - x.co[0])**2 + (y.co[1] - x.co[1])**2 + (y.co[2] - x.co[2])**2)**(1/2)
    for v in mesh.vertices:
        curr_dist = ((v.co[0] - x.co[0])**2 + (v.co[1] - x.co[1])**2 + (v.co[2] - x.co[2])**2)**(1/2)
        if (curr_dist > dist):
            dist = curr_dist
            y = v
					
    #get the point with the biggest distance to y and store it in z
    z = mesh.vertices[2]
    dist = ((z.co[0] - y.co[0])**2 + (z.co[1] - y.co[1])**2 + (z.co[2] - y.co[2])**2)**(1/2)
    for v in mesh.vertices:
        curr_dist = ((v.co[0] - y.co[0])**2 + (v.co[1] - y.co[1])**2 + (v.co[2] - y.co[2])**2)**(1/2)
        if (curr_dist > dist):
            dist = curr_dist
            z = v   
             
    # the center of the sphere is between y and z
    vec_y = Vector(y.co.xyz)
    vec_z = Vector(z.co.xyz)
    y_z = ((vec_z - vec_y)/2)
    m = Vector(vec_y + y_z)
    radius = y_z.length

    #test if any of the vertices is outside the sphere (if so update the sphere)
    for v in mesh.vertices:
        curr_dist = ((v.co[0] - m[0])**2 + (v.co[1] - m[1])**2 + (v.co[2] - m[2])**2)**(1/2)
        if curr_dist > radius:
            delta = (curr_dist - radius)/2
            radius += delta
            m += (Vector(v.co.xyz - m)).normalized() * delta  	 	
    Header.sphCenter = m
    Header.sphRadius = radius
	
#######################################################################################
# compare the hierarchy with the existing skl file
#######################################################################################		

def compareHierarchy(sklPath, Hierarchy, self, context):
    skl = import_w3d.LoadSKL(self, sklPath)
    #test if all pivots from the scene are in the skl file 
    for pivot in Hierarchy.pivots:
        found = False
        for p in skl.pivots:
            if pivot.name == p.name:
                found = True
        if not found:
            context.report({'ERROR'}, "missing pivot " + pivot.name + " in .skl file!")
            print("Error: missing pivot " + pivot.name + " in .skl file!")   
            return False
    return True			

#######################################################################################
# Main Export
#######################################################################################	

def MainExport(givenfilepath, self, context, EXPORT_MODE = 'HM', USE_SKL_FILE = False, OBJECTS = ''):
    #print("Run Export")
    HLod = struct_w3d.HLod()
    HLod.lodArray.subObjects = []
    Hierarchy = struct_w3d.Hierarchy()
	
    roottransform = struct_w3d.HierarchyPivot()
    roottransform.name = "ROOTTRANSFORM"
    roottransform.parentID = -1
    Hierarchy.pivots.append(roottransform)
    
	#switch to object mode
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
	
    # Get all the armatures in the scene.
    rigList = [object for object in bpy.context.scene.objects if object.type == 'ARMATURE']
    for rig in rigList:
        for bone in rig.pose.bones:
             pivot = struct_w3d.HierarchyPivot()
             pivot.name = bone.name
             if not bone.parent == None:
                 ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == bone.parent.name] #return an array of indices (in this case only one value)
                 pivot.parentID = ids[0]
             else:
                 pivot.parentID = 0
             pivot.position = bone.location
             pivot.eulerAngles = bone.rotation_euler
             pivot.rotation = bone.rotation_quaternion
             Hierarchy.pivots.append(pivot)		
	
    objList = []
    if EXPORT_MODE == 'SM':
        objList.append(bpy.context.scene.objects[OBJECTS])
    else:
        # Get all the mesh objects in the scene.
        objList = [object for object in bpy.context.scene.objects if object.type == 'MESH']
	
    if not EXPORT_MODE == 'S':
         #make sure the skin file ends with _skn.w3d -> not needed
         #if not givenfilepath.endswith("_skn.w3d"):
         #    givenfilepath = givenfilepath.replace(".w3d", "_skn.w3d")
	
        sknFile = open(givenfilepath, "wb")
        containerName = (os.path.splitext(os.path.basename(sknFile.name))[0]).upper()
		
        for mesh_ob in objList: 
            if mesh_ob.name == "BOUNDINGBOX":
                Box = struct_w3d.Box()
                Box.name = containerName + "." + mesh_ob.name
                Box.center = mesh_ob.location
                box_mesh = mesh_ob.to_mesh(bpy.context.scene, False, 'PREVIEW', calc_tessface = True)
                Box.extend = Vector((box_mesh.vertices[0].co.x * 2, box_mesh.vertices[0].co.y * 2, box_mesh.vertices[0].co.z))
			
                WriteBox(sknFile, Box)
            else:
                Mesh = struct_w3d.Mesh()
                Header = struct_w3d.MeshHeader()
                Mesh.bumpMaps = struct_w3d.MeshBumpMapArray()
                Mesh.matInfo = struct_w3d.MeshMaterialSetInfo()		
                Mesh.aabtree = struct_w3d.MeshAABTree()
                Mesh.aabtree.header = struct_w3d.AABTreeHeader()			
		
                verts = []
                normals = [] 
                faces = []
                uvs = []
                vertInfs = []
                vertexShadeIndices = []

                Header.meshName = mesh_ob.name
                Header.containerName = containerName
                mesh = mesh_ob.to_mesh(bpy.context.scene, False, 'PREVIEW', calc_tessface = True)
		
                triangulate(mesh)
		
                Header.vertCount = len(mesh.vertices)
                Mesh.matlPass.txStage.txCoords = []
                Mesh.vertInfs = []
                group_lookup = {g.index: g.name for g in mesh_ob.vertex_groups}
                groups = {name: [] for name in group_lookup.values()}
                vertShadeIndex = 0
                for v in mesh.vertices:
                    vertexShadeIndices.append(vertShadeIndex)
                    vertShadeIndex += 1
                    verts.append(v.co.xyz)
                    normals.append(v.normal)
                    Mesh.matlPass.txStage.txCoords.append((0.0, 0.0)) #just to fill the array 
				
				    #vertex influences
                    vertInf = struct_w3d.MeshVertexInfluences()
                    if len(v.groups) > 0:
				        #has to be this complicated, otherwise the vertex groups would be corrupted
                        ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == mesh_ob.vertex_groups[v.groups[0].group].name] #return an array of indices (in this case only one value)
                        if len(ids) > 0:
                            vertInf.boneIdx = ids[0]
                        vertInf.boneInf = v.groups[0].weight
                        Mesh.vertInfs.append(vertInf)
                    elif len(v.groups) > 1:
                        #has to be this complicated, otherwise the vertex groups would be corrupted
                        ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == mesh_ob.vertex_groups[v.groups[0].group].name] #return an array of indices (in this case only one value)
                        if len(ids) > 0:
                            vertInf.boneIdx = ids[0]
                        vertInf.boneInf = v.groups[0].weight
                        #has to be this complicated, otherwise the vertex groups would be corrupted
                        ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == mesh_ob.vertex_groups[v.groups[1].group].name] #return an array of indices (in this case only one value)
                        if len(ids) > 0:
                            vertInf.boneIdx = ids[0]
                        vertInf.xtraInf = v.groups[1].weight
                        Mesh.vertInfs.append(vertInf)
                    elif len(v.groups) > 2: 
                        context.report({'ERROR'}, "max 2 bone influences per vertex supported!")
                        print("Error: max 2 bone influences per vertex supported!")
	
                calculateMeshSphere(mesh, Header)
			
                Mesh.verts = verts
                Mesh.normals = normals
                Mesh.shadeIds = vertexShadeIndices
                Header.minCorner = Vector((mesh_ob.bound_box[0][0], mesh_ob.bound_box[0][1], mesh_ob.bound_box[0][2]))
                Header.maxCorner =  Vector((mesh_ob.bound_box[6][0], mesh_ob.bound_box[6][1], mesh_ob.bound_box[6][2]))

                for face in mesh.polygons:
                    triangle = struct_w3d.MeshFace()
                    triangle.vertIds = [face.vertices[0], face.vertices[1], face.vertices[2]]
                    triangle.normal = face.normal
                    tri_x = (verts[face.vertices[0]].x + verts[face.vertices[1]].x + verts[face.vertices[2]].x)/3
                    tri_y = (verts[face.vertices[0]].y + verts[face.vertices[1]].y + verts[face.vertices[2]].y)/3
                    tri_z = (verts[face.vertices[0]].z + verts[face.vertices[1]].z + verts[face.vertices[2]].z)/3
                    tri_pos = Vector((tri_x, tri_y, tri_z))				
                    triangle.distance = (mesh_ob.location - tri_pos).length
                    faces.append(triangle)
                Mesh.faces = faces
			
                try:
                    Mesh.userText = mesh_ob['userText'] 
                except:
                    print("no userText")
			
                Header.faceCount = len(faces)
                #Mesh.aabtree.header.polyCount = len(faces)
			
		        #uv coords
                bm = bmesh.new()
                bm.from_mesh(mesh)

                uv_layer = bm.loops.layers.uv.verify()
                #bm.faces.layers.tex.verify()
			
                index = 0
                for f in bm.faces:
                    Mesh.matlPass.txStage.txCoords[Mesh.faces[index].vertIds[0]] = f.loops[0][uv_layer].uv
                    Mesh.matlPass.txStage.txCoords[Mesh.faces[index].vertIds[1]] = f.loops[1][uv_layer].uv
                    Mesh.matlPass.txStage.txCoords[Mesh.faces[index].vertIds[2]] = f.loops[2][uv_layer].uv
                    index+=1
						
                Mesh.matlPass.vmIds = []
                Mesh.matlPass.shaderIds = []
                Mesh.matlPass.txStage.txIds = []
                Mesh.matlPass.vmIds.append(0)
                Mesh.matlPass.shaderIds.append(0)
                Mesh.matlPass.txStage.txIds.append(0)      
					
                #shader
                shader = struct_w3d.MeshShader()
                Mesh.shaders = []
                Mesh.shaders.append(shader)
                Mesh.matInfo.shaderCount = 1
				
                Mesh.vertMatls = [] 
                Mesh.textures = [] 
                meshMaterial = struct_w3d.MeshMaterial()
                vertexMaterial = struct_w3d.VertexMaterial()
			
                for mat in mesh.materials:
                    matName = (os.path.splitext(os.path.basename(mat.name))[1])[1:]
                    if matName == "BumpMaterial":
                        Mesh.matInfo.shaderCount = 0
                        for tex in bpy.data.materials[mesh_ob.name + "." + matName].texture_slots:
                            if not (tex == None):
                                if '_NRM' in tex.name:
                                    Header.vertChannelCount = 99
                                    Mesh.bumpMaps.normalMap.entryStruct.normalMap = tex.name
                                else:
                                    Mesh.bumpMaps.normalMap.entryStruct.diffuseTexName = tex.name	
                    else:
                        Mesh.matInfo.vertMatlCount += 1
                        meshMaterial.vmName = matName
                        vertexMaterial.ambient = struct_w3d.RGBA(r = 255, g = 255, b = 255, a = 255)
                        vertexMaterial.diffuse = struct_w3d.RGBA(r = int(mat.diffuse_color.r), g = int(mat.diffuse_color.g), b = int(mat.diffuse_color.b), a = 255)
                        vertexMaterial.specular = struct_w3d.RGBA(r = int(mat.specular_color.r), g = int(mat.specular_color.g), b = int(mat.specular_color.b), a = 255)
                        vertexMaterial.shininess = 1.0#mat.specular_intensity
                        vertexMaterial.opacity = 1.0#mat.diffuse_intensity         
                        meshMaterial.vmInfo = vertexMaterial
                        Mesh.vertMatls.append(meshMaterial)
                        if not meshMaterial.vmName == "":
                            for tex in bpy.data.materials[mesh_ob.name + "." + meshMaterial.vmName].texture_slots:
                                if not (tex == None):
                                    Mesh.matInfo.textureCount += 1
                                    texture = struct_w3d.Texture()
                                    texture.name = tex.name
                                    Mesh.textures.append(texture)

                Header.matlCount = len(Mesh.vertMatls)
			
                if len(mesh_ob.vertex_groups) > 0:		 
                    Header.attrs = 131072 #type skin
                    Header.vertChannelCount = 19
                else:
                    Header.attrs = 0 #type normal mesh
				
                    pivot = struct_w3d.HierarchyPivot()
                    pivot.name = mesh_ob.name
                    pivot.parentID = 0
                    if not mesh_ob.parent_bone == "":
                        ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == mesh_ob.parent_bone] #return an array of indices (in this case only one value)
                        pivot.parentID = ids[0]
                    pivot.position = mesh_ob.location
                    pivot.eulerAngles = mesh_ob.rotation_euler
                    pivot.rotation = mesh_ob.rotation_quaternion
                    Hierarchy.pivots.append(pivot)	
			       
                Mesh.header = Header			
                WriteMesh(sknFile, Mesh)
			
            #HLod stuff
            subObject = struct_w3d.HLodSubObject()
            subObject.name = containerName + "." + mesh_ob.name
            subObject.boneIndex = 0
            ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == mesh_ob.name] #return an array of indices (in this case only one value)
            if len(ids) > 0:
	            subObject.boneIndex = ids[0]
            HLod.lodArray.subObjects.append(subObject)

    Hierarchy.header.pivotCount = len(Hierarchy.pivots)
		
    #test if we want to export a skeleton file or use an existing
    sklPath = ""
    if givenfilepath.endswith("skn.w3d"):
        sklPath = givenfilepath.replace("skn", "skl")
    else:
        sklPath = givenfilepath.replace(".w3d", "_skl.w3d")
    sklName = (os.path.splitext(os.path.basename(sklPath))[0]).upper()
	
    if EXPORT_MODE == 'HM' or EXPORT_MODE == 'HAM' or EXPORT_MODE == 'S':
        if len(rigList) == 1:
            if USE_SKL_FILE and not EXPORT_MODE == 'S':
                try:
                    if compareHierarchy(rigList[0]['sklFile'], Hierarchy, self, context):
                        sklName = (os.path.splitext(os.path.basename(rigList[0]['sklFile']))[0]).upper()	
                        HLod.header.HTreeName = sklName
                except:
                    context.report({'ERROR'}, "armature object has no property: sklFile!")
                    print("armature object has no property: sklFile!")	
					
                    #so save the skeleton to a new file
                    sklFile = open(sklPath,"wb")
                    Hierarchy.header.name = sklName
                    WriteHierarchy(sklFile, Hierarchy)
                    HLod.header.HTreeName = sklName
                    sklFile.close()
            else:
                sklFile = open(sklPath,"wb")
                Hierarchy.header.name = sklName
                WriteHierarchy(sklFile, Hierarchy)
                HLod.header.HTreeName = sklName
                sklFile.close()
				
        elif len(rigList) > 1:
            # if the rig list is > 1 then we always have to export a new skl file
            sklFile = open(sklPath,"wb")
            Hierarchy.header.name = sklName
            WriteHierarchy(sklFile, Hierarchy)
            HLod.header.HTreeName = sklNameskl
            File.close()
				
		#write the hierarchy to the skn file (has no armature data)
        elif not EXPORT_MODE == 'S':
            Hierarchy.header.name = containerName	  
            WriteHierarchy(sknFile, Hierarchy)
            HLod.header.HTreeName = containerName
			
        else:
            context.report({'ERROR'}, "no armature data available!!")
            print("no armature data available!!")	
	
    if not (EXPORT_MODE == 'SM' or EXPORT_MODE == 'S'):
        HLod.lodArray.header.modelCount = len(HLod.lodArray.subObjects)
        HLod.header.modelName = containerName
        WriteHLod(sknFile, HLod)

    try:
        sknFile.close()  
    except:
        print("")