#Written by Stephan Vedder
#Last Modification 8.2.2015
#Loads the W3D Format used in games by Westwood & EA
import bpy
import operator
import struct
import os
import sys
import bmesh
from bpy.props import *
from mathutils import Vector, Matrix, Quaternion
from . import struct_w3d

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

def ReadRGBA(file):
    return struct_w3d.RGBA(r=file.read(1),g=file.read(1),b=file.read(1),a=file.read(1))

def GetChunkSize(data):
    return (data & int(0x7FFFFFFF))

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

def ReadHierarchyHeader(file):
    HieraHeader = struct_w3d.HieraHeader()
    HieraHeader.version = ReadLong(file)
    HieraHeader.hierName = ReadFixedString(file)
    HieraHeader.pivotCount = ReadLong(file)
    HieraHeader.centerPos = (ReadFloat(file), ReadFloat(file), ReadFloat(file))

    return HieraHeader

def ReadPivots(file, chunkEnd):
    pivots = []
    while file.tell() < chunkEnd:
        pivot = struct_w3d.HieraPivot()
        pivot.pivotName = ReadFixedString(file)
        pivot.parentID = ReadSignedLong(file)
        pivot.pos = (ReadFloat(file), ReadFloat(file) ,ReadFloat(file))
        pivot.eulerAngles = (ReadFloat(file), ReadFloat(file), ReadFloat(file))
        pivot.rotation = struct_w3d.Quat(val1 = ReadFloat(file), val2 = ReadFloat(file),val3 = ReadFloat(file),val4 = ReadFloat(file))

        pivots.append(pivot)
    return pivots

def ReadPivotFixups(file, chunkEnd):
    pivot_fixups = []
    while file.tell() < chunkEnd:
        pivot_fixup = (ReadFloat(file), ReadFloat(file), ReadFloat(file))
        pivot_fixups.append(pivot_fixup)
    return pivot_fixups

def ReadHierarchy(file,chunkEnd):
    HieraHeader = struct_w3d.HieraHeader()
    Pivots = []
    Pivot_fixups = []

    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize

        if chunkType == 257:
            HieraHeader = ReadHierarchyHeader(file)
        elif chunkType == 258:
            Pivots = ReadPivots(file, subChunkEnd)
        elif chunkType == 259:
            Pivot_fixups = ReadPivotFixups(file, subChunkEnd)
        else:
            file.seek(chunkSize, 1)

    return struct_w3d.Hiera(header = HieraHeader, pivots = Pivots, pivot_fixups = Pivot_fixups)

def ReadAABox(file,chunkEnd):
    while file.tell() < chunkEnd:
        file.read(4)

def ReadCompressed_Animation(file,chunkEnd):
    while file.tell() < chunkEnd:
        file.read(4)

def ReadHLodHeader(file):
    HLodHeader = struct_w3d.HLodHeader()
    HLodHeader.version = ReadLong(file)
    HLodHeader.lodCount = ReadLong(file)
    HLodHeader.modelName = ReadFixedString(file)
    HLodHeader.HTreeName = ReadFixedString(file)
    return HLodHeader

def ReadHLodArrayHeader(file):
    HLodArrayHeader = struct_w3d.HLodArrayHeader()
    HLodArrayHeader.modelCount = ReadLong(file)
    HLodArrayHeader.maxScreenSize = ReadFloat(file)
    return HLodArrayHeader

def ReadHLodSubObject(file):
    HLodSubObject = struct_w3d.HLodSubObject()
    HLodSubObject.name = ReadFixedString(file)
    HLodSubObject.boneIndex = ReadLong(file)
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
            HLodSubObjects.append(ReadHLodSubObject(file))
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

def ReadAnimation(file,chunkEnd):
    while file.tell() < chunkEnd:
        file.read(4)

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

    return struct_w3d.MshTexStage(txIds = TextureIds,txCoords = TextureCoords)

def ReadMeshMaterialPass(file, chunkEnd):
    VertexMaterialIds = []
    ShaderIds = []
    TextureStage = struct_w3d.MshTexStage()
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

    return struct_w3d.MshMatPass(vmIds = VertexMaterialIds,shaderIds = ShaderIds,txStage = TextureStage)


def ReadW3DMaterial(file,chunkEnd):
    mat = struct_w3d.MshMat()
    while file.tell() < chunkEnd:
        #file.read(4)
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell()+chunkSize

        if chunkType == 44:
            mat.vmName = ReadString(file)
        elif chunkType == 45:
            vmInf = struct_w3d.VtxMat()
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
        #file.read(4)
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell()+chunkSize
        if chunkType == 43:
            Mats.append(ReadW3DMaterial(file,subChunkEnd))
        else:
            file.seek(chunkSize,1)
    return Mats

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

def ReadMeshFaceArray(file, chunkEnd):
    faces = []
    while file.tell() < chunkEnd:
        faces.append(ReadMeshFace(file))
    return faces

def ReadMeshShaderArray(file, chunkEnd):
    while file.tell() < chunkEnd:
        file.read(4)

def ReadMeshFace(file):
    result = struct_w3d.MshFace(vertIds = (ReadLong(file), ReadLong(file), ReadLong(file)),
    attrs = ReadLong(file),
    normal = (ReadFloat(file),ReadFloat(file), ReadFloat(file)),
    distance = ReadFloat(file))
    return result

def ReadMeshMaterialSetInfo (file):
    result = struct_w3d.MshMatSetInfo(passCount = ReadLong(file), vertMatlCount = ReadLong(file), shaderCount = ReadLong(file), textureCount = ReadLong(file))
    return result

def ReadTexture(file,chunkEnd):
    tex = struct_w3d.Tex()
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize

        if Chunktype == 50:
            tex.name = ReadString(file)
        elif Chunktype == 51:
            tex.textureInfo = struct_w3d.W3DTextureInfo(attributes=ReadShort(file),
                animType=ReadShort(file),frameCount=ReadLong(file),frameRate=ReadFloat(file))
        else:
            file.seek(Chunksize,1)
    return tex

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

def ReadMeshHeader(file):
    result = struct_w3d.MshHeader(version = ReadLong(file), attrs =  ReadLong(file), meshName = ReadFixedString(file),
    containerName = ReadFixedString(file),faceCount = ReadLong(file),
    vertCount = ReadLong(file),matlCount = ReadLong(file),damageStageCount = ReadLong(file),sortLevel = ReadLong(file),
    prelitVersion = ReadLong(file) ,futureCount = ReadLong(file),
    vertChannelCount = ReadLong(file), faceChannelCount = ReadLong(file),
    #bounding volumes
    minCorner = (ReadFloat(file),ReadFloat(file),ReadFloat(file)),
    maxCorner = (ReadFloat(file),ReadFloat(file),ReadFloat(file)),
    sphCenter = (ReadFloat(file),ReadFloat(file),ReadFloat(file)),
    sphRadius =  ReadFloat(file))
    return result

    # do what it says
def ReadMesh(file,chunkEnd):
    MeshVerticesInfs = []
    MeshVertices = []
    MeshVerticeMats = []
    MeshNormals = []
    MeshHeader = struct_w3d.MshHeader()
    MeshInfo = struct_w3d.MshMatSetInfo()
    MeshFaces = []
    MeshMaterialPass = struct_w3d.MshMatPass()
    MeshTriangles = []
    MeshShadeIds = []
    MeshMats = []
    MeshTextures = []
    MeshUsertext = ""
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
                ReadMeshShaderArray(file,subChunkEnd)
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
        else:
            print("Invalid Chunktype: %s" %Chunktype)
            file.seek(Chunksize,1)

    return struct_w3d.Msh(header = MeshHeader, verts = MeshVertices, normals = MeshNormals,vertInfs = MeshVerticesInfs,faces = MeshFaces,userText = MeshUsertext,
                shadeIds = MeshShadeIds, matlheader = [],shaders = [],vertMatls = MeshVerticeMats , textures = MeshTextures, matlPass = MeshMaterialPass)

def LoadSKL(givenfilepath, filename):
    Hierarchy = struct_w3d.Hiera()
    sklpath = os.path.dirname(givenfilepath) + "/" + filename.lower() + ".w3d"
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

    #reads the file and get chunks and do all the other stuff
def MainImport(givenfilepath, self, context):
    file = open(givenfilepath,"rb")
    file.seek(0,2)
    filesize = file.tell()
    file.seek(0,0)
    Chunknumber = 1
    Meshes = []
    Hierarchy = struct_w3d.Hiera()
    HLod = struct_w3d.HLod()

    while file.tell() < filesize:
        data = ReadLong(file)
        Chunksize =  GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + Chunksize

        if data == 0:
            Meshes.append(ReadMesh(file, chunkEnd))
            CM = Meshes[len(Meshes)-1]
            file.seek(chunkEnd,0)

        elif data == 256:
            Hierarchy = ReadHierarchy(file, chunkEnd)
            file.seek(chunkEnd,0)

        elif data == 512:
            ReadAnimation(file,chunkEnd)
            file.seek(chunkEnd,0)

        elif data == 680:
            ReadCompressed_Animation(file,chunkEnd)
            file.seek(chunkEnd,0)

        elif data == 1792:
            HLod = ReadHLod(file,chunkEnd)
            file.seek(chunkEnd,0)

        elif data == 1856:
            ReadAABox(file,chunkEnd)
            file.seek(chunkEnd,0)

        else:
            file.seek(Chunksize,1)

        Chunknumber += 1

    file.close()

	
	##load skl file if needed -> print error message to user
    if HLod.header.modelName != HLod.header.HTreeName:
        Hierarchy = LoadSKL(givenfilepath, HLod.header.HTreeName)

    for m in Meshes:
        Vertices = m.verts
        Faces = []

        for f in m.faces:
            Faces.append(f.vertIds)

        #create the mash
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

        for vm in m.vertMatls:
            print(vm.vmName)
            mat = bpy.data.materials.new(vm.vmName)
            mat.use_shadeless = True
            mesh.materials.append(mat)

        for tex in m.textures:
            print(tex.name)
            basename = os.path.splitext(tex.name)[0]
            tgapath = os.path.dirname(givenfilepath)+"/"+basename+".tga"
            ddspath = os.path.dirname(givenfilepath)+"/"+basename+".dds"
            found_img = False
            try:
                img = bpy.data.images.load(tgapath)
                print(tgapath)
                found_img = True
            except:
                try:
                    img = bpy.data.images.load(ddspath)
                    print(ddspath)
                    found_img = True
                except:
                    print("Cannot load image %s" % os.path.dirname(givenfilepath)+"/"+basename)

            # Create material
            mTex = mesh.materials[0].texture_slots.add()

            # Create image texture from image
            if found_img == True:
                cTex = bpy.data.textures.new(tex.name, type = 'IMAGE')
                cTex.image = img
                mTex.texture = cTex

            mTex.texture_coords = 'UV'
            mTex.mapping = 'FLAT'

        mesh_ob = bpy.data.objects.new(m.header.meshName, mesh)
       
        #hierarchy stuff and skeleton
        if Hierarchy.header.pivotCount > 0:  
            # mesh header attributes		
            #        0      -> normal mesh
			#        8192   -> normal mesh - two sided
            #        32768  -> normal mesh - cast shadow		
            #        131072 -> skin			
			#        163840 -> skin - cast shadow
            type = m.header.attrs
            if type == 0 or type == 8192 or type == 32768:
                for pivot in Hierarchy.pivots:
                    if m.header.meshName == pivot.pivotName:
                        location = pivot.pos
                        rotation_euler = pivot.eulerAngles
                        rotation_quaternion = (pivot.rotation.val1, pivot.rotation.val2, pivot.rotation.val3, pivot.rotation.val4)
                        mesh_ob.rotation_mode = 'ZYX'
                        mesh_ob.location = location
                        mesh_ob.rotation_euler = rotation_euler
                        mesh_ob.rotation_quaternion = rotation_quaternion
			
			
            elif type == 131072 or type == 163840:
                amtName = HLod.header.HTreeName
                amt = bpy.data.armatures.new(Hierarchy.header.hierName)
                amt.show_names = True
                rig = bpy.data.objects.new(amtName, amt)
                rig.location = Hierarchy.header.centerPos
                rig.rotation_mode = 'ZYX'
                rig.show_x_ray = True
                bpy.context.scene.objects.link(rig) # Link the object to the active scene
                bpy.context.scene.objects.active = rig
                bpy.ops.object.mode_set(mode = 'EDIT')
                bpy.context.scene.update()	
			
                for pivot in Hierarchy.pivots:
                    pivot_pos = Vector((pivot.pos[0], pivot.pos[1], pivot.pos[2]))
                    pivot_rot = Quaternion((pivot.rotation.val3,pivot.rotation.val2, pivot.rotation.val1, pivot.rotation.val4))					
                    if pivot.parentID == -1:
                        #roottransform is the position of the armature
                        bpy.data.objects[amtName].location = pivot_pos
                    elif pivot.parentID == 0:		
                        bone = amt.edit_bones.new(pivot.pivotName)
                        bone.transform(rig.matrix_world)
                        bone.head = pivot_pos
                        bone.tail = bone.head + pivot_rot*Vector((-0.001, 0.0, 0.0))
                    else:	 
                        bone = amt.edit_bones.new(pivot.pivotName)
                        bone.transform(rig.matrix_world)	
                        if bone.vector.y >= 0:
                            bone.roll = -bone.roll	
                        parent_pivot =  Hierarchy.pivots[pivot.parentID]
                        parent_rot = Quaternion((parent_pivot.rotation.val4, parent_pivot.rotation.val1, parent_pivot.rotation.val2, parent_pivot.rotation.val3))
                        parent = amt.edit_bones[parent_pivot.pivotName]
                        bone.parent = parent
                        bone.head = pivot_pos
                        #bone.head = parent.tail
                        bone.use_connect = True
                        #bone.use_inherit_rotation = True
                        #bone.use_inherit_scale = True
                        bone.tail = bone.head + (pivot_rot)*pivot_pos
			    
				#create vertex group for each bone/ pivot
                for pivot in Hierarchy.pivots:
                    mesh_ob.vertex_groups.new(pivot.pivotName)
				 
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
						
                mod = mesh_ob.modifiers.new(amtName, 'ARMATURE')
                mod.object = rig
                mod.use_bone_envelopes = False
                mod.use_vertex_groups = True
            else:
                context.report({'ERROR'}, "unsupported meshtype attribute: %i" %type)
        bpy.context.scene.objects.link(mesh_ob) # Link the object to the active scene

class W3DImporter(bpy.types.Operator):
    '''Import from W3D File Format (.w3d)'''
    bl_idname = "import_mesh.westerwood_w3d"
    bl_label = 'Import W3D'

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    filepath = StringProperty(
                name="File Path",\
                description="Filepath used for importing the W3D file",\
                maxlen=1024,\
                default="")

    def execute(self, context):
        t = time.mktime(datetime.datetime.now().timetuple())
        with open(self.properties.filepath, 'rb') as file:
            print('Importing file', self.properties.filepath)
            read(file, context, self)

        t = time.mktime(datetime.datetime.now().timetuple()) - t
        print('Finished importing in', t, 'seconds')
        return {'FINISHED!'}

    def invoke(self, context, event):
        return {'RUNNING_MODAL'}
