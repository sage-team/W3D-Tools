#Written by Stephan Vedder and Michael Schnabel
#Last Modification 26.3.2015
#Loads the W3D Format used in games by Westwood & EA
import bpy
import operator
import struct
import os
import math
import sys
import bmesh
from bpy.props import *
from mathutils import Vector, Quaternion
from . import struct_w3d

#TODO 

#do not load files multiple times e.g. textures skeletons etc

#apply textures to meshes

#load and create animation data

#test normal map data

#create AABTree boxes

#possible to parent a vertex group to a bone?

#######################################################################################
# Basic Methods
#######################################################################################

def ReadString(file):
    bytes = []
    b = file.read(1)
    while ord(b)!=0:
        bytes.append(b)
        b = file.read(1)
    return (b"".join(bytes)).decode("utf-8")

def ReadFixedString(file):
    SplitString = ((str(file.read(16)))[2:16]).split("\\")
    return SplitString[0]

def ReadLongFixedString(file):
    SplitString = ((str(file.read(32)))[2:32]).split("\\")
    return SplitString[0]

def ReadRGBA(file):
    return struct_w3d.RGBA(r=file.read(1),g=file.read(1),b=file.read(1),a=file.read(1))

def GetChunkSize(data):
    return (data & int(0x7FFFFFFF))
<<<<<<< HEAD
	
def GetVersion(data):
    return struct_w3d.Version(major = (data)>>16, minor = (data) & 0xFFFF)
    
=======

def ReadByte(file):
    #binary_format = "<l" long
    return (struct.unpack("<L",file.read(4))[0])

>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2
def ReadLong(file):
    #binary_format = "<l" long
    return (struct.unpack("<L",file.read(4))[0])

def ReadSignedLong(file):
    #binary_format = "<l" signed long
    return (struct.unpack("<l",file.read(4))[0])

def ReadShort(file):
    #binary_format = "<h" short
    return (struct.unpack("<H",file.read(2))[0])

def ReadLongArray(file,chunkEnd):
    LongArray = []
    while file.tell() < chunkEnd:
        LongArray.append(ReadLong(file))
    return LongArray

def ReadFloat(file):
    #binary_format = "<f" float
    return (struct.unpack("f",file.read(4))[0])
	
def ReadUnsignedByte(file):
    return (struct.unpack("<B",file.read(1))[0])
	
def ReadQuaternion(file):
    quat = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))
    #change order from xyzw to wxyz
    return Quaternion((quat[3], quat[0], quat[1], quat[2]))
	
#######################################################################################
# Hierarchy
#######################################################################################

def ReadHierarchyHeader(file):
    HierarchyHeader = struct_w3d.HierarchyHeader()
    HierarchyHeader.version = GetVersion(ReadLong(file))
    HierarchyHeader.name = ReadFixedString(file)
    HierarchyHeader.pivotCount = ReadLong(file)
    HierarchyHeader.centerPos = Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
    return HierarchyHeader

def ReadPivots(file, chunkEnd):
    pivots = []
    while file.tell() < chunkEnd:
        pivot = struct_w3d.HierarchyPivot()
        pivot.name = ReadFixedString(file)
        pivot.parentID = ReadSignedLong(file)
        pivot.position = Vector((ReadFloat(file), ReadFloat(file) ,ReadFloat(file)))
        pivot.eulerAngles = Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
        pivot.rotation = ReadQuaternion(file)
        pivots.append(pivot)
    return pivots

def ReadPivotFixups(file, chunkEnd):
    pivot_fixups = []
    while file.tell() < chunkEnd:
        pivot_fixup = Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
        pivot_fixups.append(pivot_fixup)
    return pivot_fixups

def ReadHierarchy(file,chunkEnd):
    HierarchyHeader = struct_w3d.HierarchyHeader()
    Pivots = []
    Pivot_fixups = []
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        if chunkType == 257:
            HierarchyHeader = ReadHierarchyHeader(file)		
        elif chunkType == 258:
            Pivots = ReadPivots(file, subChunkEnd)
        elif chunkType == 259:
            Pivot_fixups = ReadPivotFixups(file, subChunkEnd)
        else:
<<<<<<< HEAD
            file.seek(chunkSize, 1)	
    return struct_w3d.Hierarchy(header = HierarchyHeader, pivots = Pivots, pivot_fixups = Pivot_fixups)
=======
            file.seek(chunkSize, 1)
    return struct_w3d.Hiera(header = HieraHeader, pivots = Pivots, pivot_fixups = Pivot_fixups)

def ReadAABox(file,chunkEnd):
    version = ReadLong(file)
    attributes = ReadLong(file)
    name = ReadFixedString32(file)
    color = ReadRGBA(file)
    center = Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
    extend = Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
    return struct_w3d.AABox(version = version, attributes = attributes, name = name, color = color, center = center, extend = extend)
>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2

#######################################################################################
# Animation
#######################################################################################
	
def ReadAnimationHeader(file, chunkEnd):
    return struct_w3d.AnimationHeader(version = GetVersion(ReadLong(file)), name = ReadFixedString(file), hieraName = ReadFixedString(file), numFrames = ReadLong(file), frameRate = ReadLong(file))

def ReadAnimationChannel(file, chunkEnd):
    FirstFrame = ReadShort(file)
    LastFrame = ReadShort(file)
    VectorLen = ReadShort(file)
    Type = ReadShort(file)
    Pivot = ReadShort(file)
    Pad = ReadShort(file) 
    Data = []
    if VectorLen == 1:
        while file.tell() < chunkEnd:
            Data.append(ReadFloat(file))
    elif VectorLen == 4:
        while file.tell() < chunkEnd:
            Data.append(ReadQuaternion(file))
    else:
        while file.tell() < chunkEnd:
            file.read(4)
    return struct_w3d.AnimationChannel(firstFrame = FirstFrame, lastFrame = LastFrame, vectorLen = VectorLen, type = Type, pivot = Pivot, pad = Pad, data = Data)
	
def ReadAnimationBitChannel(file, chunkEnd):
    while file.tell() < chunkEnd:
        print("###anim bit channel")
        print(ReadShort(file))
        print(ReadShort(file))
        print(ReadShort(file))
        print(ReadShort(file))
        print(file.read(8))

def ReadAnimation(file, chunkEnd):
    Header = struct_w3d.AnimationHeader()
    Channels = []
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        if chunkType == 513:
            Header = ReadAnimationHeader(file, subChunkEnd)
        elif chunkType == 514:
            Channels.append(ReadAnimationChannel(file, subChunkEnd))
        elif chunkType == 515:
            print("##### anim bit channels not supported yet!")
            #ReadAnimationBitChannel(file, subChunkEnd)
        else:
            file.seek(chunkSize,1)	
    return struct_w3d.Animation(header = Header, channels = Channels)
			
def ReadCompressedAnimationHeader(file, chunkEnd):
    return struct_w3d.CompressedAnimationHeader(version = GetVersion(ReadLong(file)), name = ReadFixedString(file), hieraName = ReadFixedString(file), numFrames = ReadLong(file), frameRate = ReadShort(file), flavor = ReadShort(file))
	
def ReadAnimationTimeCodedChannel(file, chunkEnd):
    TimeCodesCount = ReadLong(file)       
    Pivot = ReadShort(file)    
    VectorLen = ReadUnsignedByte(file)
    Flag = ReadUnsignedByte(file)  
    Pivot = ReadShort(file)
    Data = []
    print(VectorLen)
    print(Pivot)
    if VectorLen == 1:
        while file.tell() < chunkEnd:
            tCode = ReadLong(file)
            print(ReadFloat(file))
            #Data.append(ReadFloat(file))
    elif VectorLen == 4:
        while file.tell() < chunkEnd:
            tCode = ReadLong(file)
            print(ReadQuaternion(file))
            #Data.append(ReadQuaternion(file))
    else:
        while file.tell() < chunkEnd:
            file.read(4)
		
def ReadCompressedAnimation(file,chunkEnd):
    print("### compressed animation")
    Header = struct_w3d.CompressedAnimationHeader()
    Channels = []
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        if chunkType == 641:
            Header = ReadCompressedAnimationHeader(file, subChunkEnd)
            print(Header.hieraName)
            print(Header.flavor)
        elif chunkType == 642:
            print("##### anim bit channels for compressed animation are not supported yet!")
            #Channels.append(ReadAnimationChannel(file, subChunkEnd))
        elif chunkType == 643:
            print("##### anim bit channels not supported yet!")
            #ReadAnimationBitChannel(file, subChunkEnd)
        elif chunkType == 644:
            print("###anim bfme2 data") 
            print(chunkSize)
            ReadAnimationTimeCodedChannel(file, subChunkEnd)		
        else:
            file.seek(chunkSize,1)	

#######################################################################################
# HLod
#######################################################################################

def ReadHLodHeader(file):
    HLodHeader = struct_w3d.HLodHeader()
    HLodHeader.version = GetVersion(ReadLong(file))
    HLodHeader.lodCount = ReadLong(file)
    HLodHeader.modelName = ReadFixedString(file)
    HLodHeader.HTreeName = ReadFixedString(file)
    return HLodHeader

def ReadHLodArrayHeader(file):
    HLodArrayHeader = struct_w3d.HLodArrayHeader()
    HLodArrayHeader.modelCount = ReadLong(file)
    HLodArrayHeader.maxScreenSize = ReadFloat(file)
    return HLodArrayHeader

def ReadHLodSubObject(file, chunkEnd):
    HLodSubObject = struct_w3d.HLodSubObject()
    HLodSubObject.boneIndex = ReadLong(file)
    HLodSubObject.name = ReadLongFixedString(file)
    return HLodSubObject

def ReadHLodArray(file, chunkEnd):
    HLodArrayHeader = struct_w3d.HLodArrayHeader()
    HLodSubObjects = []
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        if chunkType == 1795:
            HLodArrayHeader = ReadHLodArrayHeader(file)
        elif chunkType == 1796:
            HLodSubObjects.append(ReadHLodSubObject(file, subChunkEnd))
        else:
            file.seek(chunkSize, 1)
    return struct_w3d.HLodArray(header = HLodArrayHeader, subObjects = HLodSubObjects)

def ReadHLod(file,chunkEnd):
    HLodHeader = struct_w3d.HLodHeader()
    HLodArray = struct_w3d.HLodArray()
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        if chunkType == 1793:
            HLodHeader = ReadHLodHeader(file)
        elif chunkType == 1794:
            HLodArray = ReadHLodArray(file, subChunkEnd)
        else:
            file.seek(chunkSize, 1)
    return struct_w3d.HLod(header = HLodHeader, lodArray = HLodArray)

#######################################################################################
# Box
#######################################################################################	
	
def ReadBox(file,chunkEnd):
    version = GetVersion(ReadLong(file))
    attributes = ReadLong(file)
    name = ReadLongFixedString(file)
    color = ReadRGBA(file)
    center = Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
    extend = Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
    return struct_w3d.Box(version = version, attributes = attributes, name = name, color = color, center = center, extend = extend)
	
	
#######################################################################################
# Texture
#######################################################################################			
			
def ReadMeshTextureCoordArray(file,chunkEnd):
    txCoords = []
    while file.tell() < chunkEnd:
        txCoords.append((ReadFloat(file),ReadFloat(file)))
    return txCoords

def ReadMeshTextureStage(file,chunkEnd):
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        TextureIds = []
        TextureCoords = []
        if chunkType == 73:
            TextureIds = ReadLongArray(file,subChunkEnd)
        elif chunkType == 74:
            TextureCoords = ReadMeshTextureCoordArray(file,subChunkEnd)
        else:
            file.seek(chunkSize,1)
    return struct_w3d.MeshTextureStage(txIds = TextureIds, txCoords = TextureCoords)
	
def ReadTexture(file,chunkEnd):
    tex = struct_w3d.Texture()
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize
        if Chunktype == 50:
            tex.name = ReadString(file)
        elif Chunktype == 51:
            tex.textureInfo = struct_w3d.W3DTextureInfo(attributes = ReadShort(file),
                animType = ReadShort(file), frameCount = ReadLong(file), frameRate = ReadFloat(file))
        else:
            file.seek(Chunksize,1)
    return tex

def ReadTextureArray(file, chunkEnd):
    textures = []
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize
        if Chunktype == 49:
            textures.append(ReadTexture(file,subChunkEnd))
        else:
            file.seek(Chunksize, 1)
    return textures

#######################################################################################
# Material
#######################################################################################	
	
def ReadMeshMaterialPass(file, chunkEnd):
    VertexMaterialIds = []
    ShaderIds = []
    TextureStage = struct_w3d.MeshTextureStage()
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        if chunkType == 57: #Vertex Material Ids
            VertexMaterialIds = ReadLongArray(file,subChunkEnd)
        elif chunkType == 58:#Shader Ids
            shaderIds = ReadLongArray(file,subChunkEnd)
        elif chunkType == 72: #Texture Stage
            TextureStage = ReadMeshTextureStage(file,subChunkEnd)
        elif chunkType == 74: #Texture Coords
            TextureStage.txCoords = ReadMeshTextureCoordArray(file,subChunkEnd)
        else:
            file.seek(chunkSize,1)
    return struct_w3d.MeshMaterialPass(vmIds = VertexMaterialIds, shaderIds = ShaderIds, txStage = TextureStage)

def ReadW3DMaterial(file,chunkEnd):
    mat = struct_w3d.MeshMaterial()
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        if chunkType == 44:
            mat.vmName = ReadString(file)
        elif chunkType == 45:
            vmInf = struct_w3d.VertexMaterial()
            vmInf.attributes = ReadLong(file)
            vmInf.ambient = ReadRGBA(file)
            vmInf.diffuse = ReadRGBA(file)
            vmInf.specular = ReadRGBA(file)
            vmInf.emissive = ReadRGBA(file)
            vmInf.shininess = ReadFloat(file)
            vmInf.opacity = ReadFloat(file)
            vmInf.translucency = ReadFloat(file)
            mat.vmInfo = vmInf
        elif chunkType == 46:
            mat.vmArgs0 = ReadString(file)
        elif chunkType == 47:
            mat.vmArgs1 = ReadString(file)
        else:
            file.seek(chunkSize,1)
    return mat

def ReadMeshMaterialArray(file,chunkEnd):
    Mats = []
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell()+chunkSize
        if chunkType == 43:
            Mats.append(ReadW3DMaterial(file,subChunkEnd))
        else:
            file.seek(chunkSize,1)
    return Mats

def ReadMeshMaterialSetInfo (file):
    result = struct_w3d.MeshMaterialSetInfo(passCount = ReadLong(file), vertMatlCount = ReadLong(file), shaderCount = ReadLong(file), textureCount = ReadLong(file))
    return result	
	
#######################################################################################
# Vertices
#######################################################################################
	
def ReadMeshVertInfs(file, chunkEnd):
    boneIds = []
    while file.tell()  < chunkEnd:
        boneIds.append(ReadShort(file))
        file.seek(6,1)
    return boneIds

def ReadMeshVertArray(file, chunkEnd):
    verts = []
    while file.tell() < chunkEnd:
        verts.append((ReadFloat(file), ReadFloat(file),ReadFloat(file)))
    return verts

#######################################################################################
# Faces
#######################################################################################	

def ReadMeshFace(file):
    result = struct_w3d.MeshFace(vertIds = (ReadLong(file), ReadLong(file), ReadLong(file)),
    attrs = ReadLong(file),
    normal = Vector((ReadFloat(file),ReadFloat(file), ReadFloat(file))),
    distance = ReadFloat(file))
    return result	
	
def ReadMeshFaceArray(file, chunkEnd):
    faces = []
    while file.tell() < chunkEnd:
        faces.append(ReadMeshFace(file))
    return faces

#######################################################################################
# Shader
#######################################################################################
	
def ReadMeshShaderArray(file, chunkEnd):
    shaders = []
    while file.tell() < chunkEnd:
        shader = struct_w3d.MeshShader()
        shader.depthCompare = ReadUnsignedByte(file)
        shader.depthMask = ReadUnsignedByte(file)
        shader.colorMask = ReadUnsignedByte(file)
        shader.destBlend = ReadUnsignedByte(file)
        shader.fogFunc = ReadUnsignedByte(file)
        shader.priGradient = ReadUnsignedByte(file) 
        shader.secGradient = ReadUnsignedByte(file)
        shader.srcBlend = ReadUnsignedByte(file)
        shader.texturing = ReadUnsignedByte(file)
        shader.detailColorFunc = ReadUnsignedByte(file)
        shader.detailAlphaFunc = ReadUnsignedByte(file)
        shader.shaderPreset = ReadUnsignedByte(file)
        shader.alphaTest = ReadUnsignedByte(file)
        shader.postDetailColorFunc = ReadUnsignedByte(file)
        shader.postDetailAlphaFunc = ReadUnsignedByte(file) 
        shader.pad = ReadUnsignedByte(file)
        shaders.append(shader)
    return shaders
	
#######################################################################################
# Normal Map
#######################################################################################
	
def ReadNormalMapHeader(file, chunkEnd): 
    number = file.read(1)
    typeName = ReadLongFixedString(file)
    reserved = ReadLong(file)
    return struct_w3d.MeshNormalMapHeader(number = number, typeName = typeName, reserved = reserved)

def ReadNormalMapEntryStruct(file, chunkEnd):
    typeFlag = ReadLong(file)
    typeSize = ReadLong(file)
    infoName = ReadFixedString(file)
    itemSize = ReadLong(file)
    itemName = ReadLongFixedString(file)

def ReadNormalMap(file, chunkEnd):
    print("#####normal map#####")
    header = struct_w3d.MeshNormalMapHeader()
    entryStructs = []
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize
        print(Chunksize)
        if Chunktype == 81:
            print("#### flag")
            #nothing to read?
        elif Chunktype == 82:
            print("#### header")
            header = ReadNormalMapHeader(file, subChunkEnd)
        elif Chunktype == 83:
            print("#### entryStruct")
            entryStructs.append(ReadNormalMapEntryStruct(file, subChunkEnd))
        else:
            file.seek(Chunksize, 1)

<<<<<<< HEAD
#######################################################################################
# AABTree (Axis-aligned-bounding-box)
#######################################################################################	
	
=======
def ReadTextureArray(file,chunkEnd):
    textures = []
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize
        if Chunktype == 49:
            textures.append(ReadTexture(file,subChunkEnd))
        else:
            file.seek(Chunksize,1)
    return textures

>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2
def ReadAABTreeHeader(file, chunkEnd):
    nodeCount = ReadLong(file)
    polyCount = ReadLong(file)
    #padding of the header
    while file.tell() < chunkEnd:
        file.read(4)
    return struct_w3d.AABTreeHeader(nodeCount = nodeCount, polyCount = polyCount)

def ReadAABTreePolyIndices(file, chunkEnd):
    polyIndices = []
    while file.tell() < chunkEnd:
        polyIndices.append(ReadLong(file))
    return polyIndices

def ReadAABTreeNodes(file, chunkEnd):
    nodes = []
    while file.tell() < chunkEnd:
        min = Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
        max = Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))
        FrontOrPoly0 = ReadLong(file)
        BackOrPolyCount = ReadLong(file)
        nodes.append(struct_w3d.AABTreeNode(min = min, max = max, FrontOrPoly0 = FrontOrPoly0, BackOrPolyCount = BackOrPolyCount))
    return nodes
<<<<<<< HEAD
	
=======

#Axis-Aligned-Bounding-Box tree
>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2
def ReadAABTree(file, chunkEnd):
    aabtree = struct_w3d.MeshAABTree()
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize
        if Chunktype == 145:
            aabtree.header = ReadAABTreeHeader(file, subChunkEnd)
        elif Chunktype == 146:
            aabtree.polyIndices = ReadAABTreePolyIndices(file, subChunkEnd)
        elif Chunktype == 147:
            aabtree.nodes = ReadAABTreeNodes(file, subChunkEnd)
        else:
            file.seek(Chunksize, 1)
    return aabtree

#######################################################################################
# Mesh
#######################################################################################	
	
def ReadMeshHeader(file):
    result = struct_w3d.MeshHeader(version = GetVersion(ReadLong(file)), attrs =  ReadLong(file), meshName = ReadFixedString(file),
    containerName = ReadFixedString(file),faceCount = ReadLong(file),
    vertCount = ReadLong(file),matlCount = ReadLong(file),damageStageCount = ReadLong(file),sortLevel = ReadLong(file),
    prelitVersion = ReadLong(file) ,futureCount = ReadLong(file),
    vertChannelCount = ReadLong(file), faceChannelCount = ReadLong(file),
    #bounding volumes
    minCorner = Vector((ReadFloat(file),ReadFloat(file),ReadFloat(file))),
    maxCorner = Vector((ReadFloat(file),ReadFloat(file),ReadFloat(file))),
    sphCenter = Vector((ReadFloat(file),ReadFloat(file),ReadFloat(file))),
    sphRadius =  ReadFloat(file))
    return result

def ReadMesh(file,chunkEnd, context):
    MeshVerticesInfs = []
    MeshVertices = []
    MeshVerticeMats = []
    MeshNormals = []
    MeshHeader = struct_w3d.MeshHeader()
    MeshInfo = struct_w3d.MeshMaterialSetInfo()
    MeshFaces = []
    MeshMaterialPass = struct_w3d.MeshMaterialPass()
    MeshTriangles = []
    MeshShadeIds = []
    MeshMats = []
    MeshShaders = []
    MeshTextures = []
    MeshUsertext = ""
<<<<<<< HEAD
    MeshNormalMap = ""
    MeshAABTree = struct_w3d.MeshAABTree()
	
=======
    MeshAABTree = struct_w3d.MshAABTree()

>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2
    print("NEW MESH:")
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize

        if Chunktype == 2:
            try:
                MeshVertices = ReadMeshVertArray(file,subChunkEnd)
                print("Vertices")
            except:
                print("Mistake while reading Vertices (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
            temp = 0
        elif Chunktype == 3072:
            try:
                ReadMeshVertArray(file,subChunkEnd)
                print("Vertices-Copy")
            except:
                print("Mistake while reading Vertices-Copy (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 3:
            try:
                MeshNormals = ReadMeshVertArray(file,subChunkEnd)
                print("Normals")
            except:
                print("Mistake while reading Normals (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 3073:
            try:
                ReadMeshVertArray(file,subChunkEnd)
                print("Normals-Copy")
            except:
                print("Mistake while reading Normals-Copy (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 12:
            try:
                MeshUsertext = ReadString(file)
                print("Usertext")
                print(MeshUsertext)
            except:
                print("Mistake while reading Usertext (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 14:
            try:
                MeshVerticesInfs = ReadMeshVertInfs(file,subChunkEnd)
                print("VertInfs")
            except:
                print("Mistake while reading Vertice Influences (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 31:
            try:
                MeshHeader = ReadMeshHeader(file)
                print("Header")
            except:
                print("Mistake while reading Mesh Header (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 32:
            try:
                MeshFaces = ReadMeshFaceArray(file, subChunkEnd)
                print("Faces")
            except:
                print("Mistake while reading Faces (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 34:
            try:
                MeshShadeIds = ReadLongArray(file,subChunkEnd)
                print("Shade IDs")
            except:
                print("Mistake while reading MeshShadeIds (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 40:
            try:
                MeshInfo = ReadMeshMaterialSetInfo(file)
                print("Info")
            except:
                print("Mistake while reading MeshInfo (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 41:
            try:
                MeshShaders = ReadMeshShaderArray(file,subChunkEnd)
                print("MeshShader")
            except:
                print("Mistake while reading MeshShaders (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 42:
            try:
                MeshVerticeMats = ReadMeshMaterialArray(file,subChunkEnd)
                print("VertMats")
            except:
                print("Mistake while reading VerticeMaterials (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 48:
            try:
                MeshTextures = ReadTextureArray(file,subChunkEnd)
                print("Textures")
            except:
                print("Mistake while reading MeshTextures (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 56:
            try:
                MeshMaterialPass = ReadMeshMaterialPass(file,subChunkEnd)
                print("MatPass")
            except:
                print("Mistake while reading MeshMaterialPass (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 80:
            try:
                MeshNormalMap = ReadNormalMap(file, subChunkEnd)
                print("NormalMap")
            except:
                print("Mistake while reading NormalMap (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 96:
            try:
                ReadMeshVertArray(file,subChunkEnd)
                print("unknown Chunk 96")
            except:
                print("Mistake while reading unknown Chunk 96 (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 97:
            try:
                ReadMeshVertArray(file,subChunkEnd)
                print("unknown Chunk 97")
            except:
                print("Mistake while reading unknown Chunk 97 (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 144:
            try:
                MeshAABTree = ReadAABTree(file,subChunkEnd)
                print("AABTree")
            except:
                print("Mistake while reading AABTree (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        else:
            print("Invalid chunktype: %s" %Chunktype)
            context.report({'ERROR'}, "Invalid chunktype: %s" %Chunktype)
            file.seek(Chunksize,1)
    return struct_w3d.Mesh(header = MeshHeader, verts = MeshVertices, normals = MeshNormals,vertInfs = MeshVerticesInfs,faces = MeshFaces,userText = MeshUsertext,
                shadeIds = MeshShadeIds, matlheader = [],shaders = MeshShaders, vertMatls = MeshVerticeMats, textures = MeshTextures, matlPass = MeshMaterialPass, aabtree = MeshAABTree)

#######################################################################################
# create Box
#######################################################################################		
		
def createBox(Box):	
    name = (os.path.splitext(Box.name)[1]).replace(".", "")
    x = Box.extend[0]/2
    y = Box.extend[1]/2
    z = Box.extend[2]

    verts = [(x, y, z), (-x, y, z), (-x, -y, z), (x, -y, z), (x, y, 0), (-x, y, 0), (-x, -y, 0), (x, -y, 0)]
    faces = [(0,1,2,3), (4,5,6,7), (0,4,5,1), (1,5,6,2), (2,6,7,3), (3,7,4,0)]

    cube = bpy.data.meshes.new(name)
    box = bpy.data.objects.new(name, cube)
    box.location = Box.center
    bpy.context.scene.objects.link(box)
    cube.from_pydata(verts, [], faces)
    cube.update(calc_edges = True)
				
#######################################################################################
# Skeleton / Armature 
#######################################################################################					
				
def LoadSKL(givenfilepath, filename):
    Hierarchy = struct_w3d.Hierarchy()
    sklpath = os.path.dirname(givenfilepath) + "/" + filename.lower() + ".w3d"
    print("LOAD SKELETON:")
    print(sklpath)
    file = open(sklpath,"rb")
    file.seek(0,2)
    filesize = file.tell()
    file.seek(0,0)
    Chunknumber = 1

    while file.tell() < filesize:
        chunkType = ReadLong(file)
        Chunksize =  GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + Chunksize
        if chunkType == 256:
            Hierarchy = ReadHierarchy(file, chunkEnd)
            file.seek(chunkEnd,0)
        else:
            file.seek(Chunksize,1)

        Chunknumber += 1
    file.close()
    return Hierarchy

def createArmature(Hierarchy, amtName):
    amt = bpy.data.armatures.new(Hierarchy.header.name)
    amt.show_names = True
    rig = bpy.data.objects.new(amtName, amt)
    rig.location = Hierarchy.header.centerPos
    rig.rotation_mode = 'QUATERNION'
    rig.show_x_ray = True
    bpy.context.scene.objects.link(rig) # Link the object to the active scene
    bpy.context.scene.objects.active = rig
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.context.scene.update()

	#create the bones from the pivots
    root = Vector((0.0, 0.0, 0.0))
<<<<<<< HEAD
    for pivot in Hierarchy.pivots:			
        if not pivot.isBone:
=======
    for pivot in Hierarchy.pivots:
        if not pivot.isbone:
>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2
            continue
        bone = amt.edit_bones.new(pivot.name)
        if pivot.parentID > 0:
            parent_pivot =  Hierarchy.pivots[pivot.parentID]
            parent = amt.edit_bones[parent_pivot.name]
            #if parent.length < 0.02:
            #    parent.tail = root + Vector((0, 0.2, 0))
            bone.parent = parent
        bone.head = root
        bone.tail = root + Vector((0.0, 0.02, 0.0))

    #pose the bones
    bpy.ops.object.mode_set(mode = 'POSE')
<<<<<<< HEAD
    for pivot in Hierarchy.pivots:	
        if not pivot.isBone:
=======
    for pivot in Hierarchy.pivots:
        if not pivot.isbone:
>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2
            continue
        bone = rig.pose.bones[pivot.name]
        bone.location = pivot.position
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_euler = pivot.eulerAngles
        bone.rotation_quaternion = pivot.rotation
        #rot90 = Quaternion((0.707, 0, 0, 0.707))

    bpy.ops.object.mode_set(mode = 'OBJECT')
    return rig
	
#######################################################################################
# Main Import
#######################################################################################	

    #reads the file and get chunks and do all the other stuff
def MainImport(givenfilepath, self, context):
    file = open(givenfilepath,"rb")
    file.seek(0,2)
    filesize = file.tell()
    file.seek(0,0)
    Chunknumber = 1
    Meshes = []
    Box = struct_w3d.Box()
    Textures = []
    Hierarchy = struct_w3d.Hierarchy()
    Animation = struct_w3d.Animation()
    HLod = struct_w3d.HLod()
    amtName = ""

    while file.tell() < filesize:
        Chunktype = ReadLong(file)
        Chunksize =  GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + Chunksize
        if Chunktype == 0:
            Meshes.append(ReadMesh(file, chunkEnd, context))
            CM = Meshes[len(Meshes)-1]
            file.seek(chunkEnd,0)

        elif Chunktype == 256:
            Hierarchy = ReadHierarchy(file, chunkEnd)
            file.seek(chunkEnd,0)

        elif Chunktype == 512:
            Animation = ReadAnimation(file,chunkEnd)
            file.seek(chunkEnd,0)

        elif Chunktype == 640:
            ReadCompressedAnimation(file,chunkEnd)
            file.seek(chunkEnd,0)

        elif Chunktype == 1792:
            HLod = ReadHLod(file,chunkEnd)
            file.seek(chunkEnd,0)

        elif Chunktype == 1856:
            Box = ReadBox(file,chunkEnd)
            file.seek(chunkEnd,0)

        else:
            file.seek(Chunksize,1)

        Chunknumber += 1

    file.close()
<<<<<<< HEAD
	
    ##create box 
    if not Box.name == "":
        createBox(Box)
	
	##load skeleton (_skl.w3d) file if needed 
=======

	##load skeleton (_skl.w3d) file if needed
>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2
    if HLod.header.modelName != HLod.header.HTreeName:
        try:
            Hierarchy = LoadSKL(givenfilepath, HLod.header.HTreeName)
        except:
<<<<<<< HEAD
            context.report({'ERROR'}, "skeleton file not found: " + HLod.header.HTreeName) 
			
    elif (not Animation.header.name == "") and Hierarchy.header.name == "":			
        try:
            Hierarchy = LoadSKL(givenfilepath, Animation.header.hieraName)
        except:
            context.report({'ERROR'}, "skeleton file not found: " + Animation.header.hieraName) 

    #test for non_bone_pivots
    for obj in HLod.lodArray.subObjects: 
        if Hierarchy.header.pivotCount > 0:
            Hierarchy.pivots[obj.boneIndex].isBone = 0
=======
            context.report({'ERROR'}, "skeleton file not found: " + HLod.header.HTreeName)

    #test for non_bone_pivots
    for obj in HLod.lodArray.subObjects:
        Hierarchy.pivots[obj.boneIndex].isbone = 0
>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2

    #create skeleton if needed
    if Hierarchy.header.name.endswith('_SKL'):
        amtName = Hierarchy.header.name
        found = False
        for obj in bpy.data.objects:
            if obj.name == amtName:
                rig = obj
                found = True
        if not found:
            rig = createArmature(Hierarchy, amtName)

    for m in Meshes:
        	
        Vertices = m.verts
        Faces = []

        for f in m.faces:
            Faces.append(f.vertIds)

        #create the mesh
        mesh = bpy.data.meshes.new(m.header.containerName)
        mesh.from_pydata(Vertices,[],Faces)
        mesh.uv_textures.new("UVW")

        bm = bmesh.new()
        bm.from_mesh(mesh)

        #create the uv map
        uv_layer = bm.loops.layers.uv.verify()
        bm.faces.layers.tex.verify()

        index = 0
        if len(m.matlPass.txStage.txCoords)>0:
            for f in bm.faces:
                f.loops[0][uv_layer].uv = m.matlPass.txStage.txCoords[Faces[index][0]]
                f.loops[1][uv_layer].uv = m.matlPass.txStage.txCoords[Faces[index][1]]
                f.loops[2][uv_layer].uv = m.matlPass.txStage.txCoords[Faces[index][2]]
                index+=1

        bm.to_mesh(mesh)

        mesh_ob = bpy.data.objects.new(m.header.meshName, mesh)
		
        for vm in m.vertMatls:
            print(vm.vmName)
            created = False
            for material in bpy.data.materials:
                if vm.vmName == material.name:
                    mesh.materials.append(material)
                    created = True
            if not created:
                mat = bpy.data.materials.new(vm.vmName)
                mat.use_shadeless = True
            mesh.materials.append(mat)

        for tex in m.textures:
            print(tex.name)
            found_img = False

            basename = os.path.splitext(tex.name)[0]
			
			#test if image file has already been loaded
            for image in bpy.data.images:	
                if basename == os.path.splitext(image.name)[0]:
                    img = image
                    found_img = True

            if found_img == False:
                tgapath = os.path.dirname(givenfilepath)+"/"+basename+".tga"
                ddspath = os.path.dirname(givenfilepath)+"/"+basename+".dds"
                try:
                    img = bpy.data.images.load(tgapath)
                    print(tgapath)
                    found_img = True
                except:
<<<<<<< HEAD
                    try:
                        img = bpy.data.images.load(ddspath)
                        print(ddspath)
                        found_img = True
                    except:
                        context.report({'ERROR'}, "texture file not found: " + basename) 
                        print("Cannot load image %s" % os.path.dirname(givenfilepath)+"/"+basename)
				
=======
                    context.report({'ERROR'}, "texture file not found: " + basename)
                    print("Cannot load image %s" % os.path.dirname(givenfilepath)+"/"+basename)

>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2
            # Create material
            mTex = mesh.materials[0].texture_slots.add()

            # Create image texture from image
            if found_img == True:
                cTex = bpy.data.textures.new(tex.name, type = 'IMAGE')
                cTex.image = img
                mTex.texture = cTex

            mTex.texture_coords = 'UV'
            mTex.mapping = 'FLAT'
		
        #hierarchy stuff
        if Hierarchy.header.pivotCount > 0:
            # mesh header attributes
            #        0      -> normal mesh
			#        8192   -> normal mesh - two sided
            #        32768  -> normal mesh - cast shadow
            #        131072 -> skin
            #        139264 -> skin - two sided
			#        163840 -> skin - cast shadow
            #        172032 -> skin - two sided - cast shadow
            type = m.header.attrs
            if type == 0 or type == 8192 or type == 32768:
                for pivot in Hierarchy.pivots:
                    if m.header.meshName == pivot.name:
                        mesh_ob.rotation_mode = 'QUATERNION'
                        mesh_ob.location =  pivot.position
                        mesh_ob.rotation_euler = pivot.eulerAngles
                        mesh_ob.rotation_quaternion = pivot.rotation
<<<<<<< HEAD
						
                        #test if the pivot has a parent pivot and parent the corresponding bone to the mesh if it has
                        if pivot.parentID > 0:
                            parent_pivot = Hierarchy.pivots[pivot.parentID]
                            mesh_ob.parent = bpy.data.objects[amtName]
                            mesh_ob.parent_bone = parent_pivot.name
                            mesh_ob.parent_type = 'BONE'

            elif type == 131072 or type == 139264 or type == 163840 or type == 172032:
=======

                        #test if the pivot has a parent pivot and parent them if it has
                        if pivot.parentID > 0:
                            parent_pivot = Hierarchy.pivots[pivot.parentID]
                            parent = bpy.data.armatures[amtName].bones[parent_pivot.name]

                            #bpy.ops.object.select_all(action='DESELECT') #deselect all object

                            #parent.select = True
                            #mesh_ob.select = True

                            #bpy.context.scene.objects.active = parent
                            #bpy.ops.object.parent_set(type = 'BONE')

            elif type == 131072 or type == 163840:
>>>>>>> 7fa3e7808beff224d438cfc27c8c2bfa02e1b7b2
				#create vertex group for each pivot
                for pivot in Hierarchy.pivots:
                    mesh_ob.vertex_groups.new(pivot.name)

                vertIDs = []
                weight = 1.0 #in range 0.0 to 1.0
                boneID = m.vertInfs[0]
                for i in range(len(m.vertInfs)):
                    if m.vertInfs[i] == boneID:
                        vertIDs.append(i)
                    else:
                        mesh_ob.vertex_groups[boneID].add(vertIDs, weight, 'REPLACE')
                        boneID = m.vertInfs[i]
                        vertIDs = []
                        vertIDs.append(i)
                mesh_ob.vertex_groups[boneID].add(vertIDs, weight, 'REPLACE')

                mod = mesh_ob.modifiers.new(amtName, 'ARMATURE')
                mod.object = rig
                mod.use_bone_envelopes = False
                mod.use_vertex_groups = True
            else:
                context.report({'ERROR'}, "unsupported meshtype attribute: %i" %type)
        bpy.context.scene.objects.link(mesh_ob) # Link the object to the active scene

    #animation stuff
    if not Animation.header.name == "":	
        for channel in Animation.channels:
            pivot = Hierarchy.pivots[channel.pivot]
            if pivot.isBone:
                obj = rig.pose.bones[pivot.name]
            else:
                obj = bpy.data.objects[pivot.name]
            rest_location = obj.location
            rest_rotation = obj.rotation_quaternion
            # ANIM_CHANNEL_X
            if channel.type == 0:   
                #print("x")
                for frame in range(channel.firstFrame, channel.lastFrame):
                    bpy.context.scene.frame_set(frame)
                    obj.location = Vector((channel.data[frame - channel.firstFrame], 0, 0)) 
                    #obj.position += Vector((0, 0, channel.data[frame - channel.firstFrame]))
                    obj.keyframe_insert(data_path='location', frame = frame * 10) 
            # ANIM_CHANNEL_Y
            elif channel.type == 1:   
                #print("y")
                for frame in range(channel.firstFrame, channel.lastFrame):
                    bpy.context.scene.frame_set(frame)
                    obj.location = Vector((0, channel.data[frame - channel.firstFrame], 0)) 
                    #obj.position += Vector((0, 0, channel.data[frame - channel.firstFrame]))
                    obj.keyframe_insert(data_path='location', frame = frame * 10) 
            # ANIM_CHANNEL_Z
            elif channel.type == 2:  
                #print("z")
				#curKey.value += [0, 0, step] * (inverse datumRot)
                #pack this into a method
                for frame in range(channel.firstFrame, channel.lastFrame):
                    bpy.context.scene.frame_set(frame)
                    obj.location = Vector((0, 0, channel.data[frame - channel.firstFrame])) 
                    #obj.position += Vector((0, 0, channel.data[frame - channel.firstFrame]))
                    obj.keyframe_insert(data_path='location', frame = frame * 10) 
					
			# ANIM_CHANNEL_Q		
            elif channel.type == 6:  
                #print("quaternion")
                for frame in range(channel.firstFrame, channel.lastFrame):
                    bpy.context.scene.frame_set(frame)
                    obj.rotation_mode = 'QUATERNION'
                    obj.rotation_quaternion = channel.data[frame - channel.firstFrame] 
                    obj.keyframe_insert(data_path='rotation_quaternion', frame = frame * 10)   
            else:
                context.report({'ERROR'}, "unsupported channel type: %s" %channel.type)
                
    bpy.context.scene.game_settings.material_mode = 'GLSL'
    #set render mode to textured or solid
    for scrn in bpy.data.screens:
        if scrn.name == 'Default':
            bpy.context.window.screen = scrn
            for area in scrn.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            if len(bpy.data.textures) > 1:
                                space.viewport_shade = 'TEXTURED'
                            else:
                                space.viewport_shade = 'SOLID'
