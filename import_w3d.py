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

#Struct
class Struct:
    def __init__ (self, *argv, **argd):
        if len(argd):
            # Update by dictionary
            self.__dict__.update (argd)
        else:
            # Update by position
            attrs = filter (lambda x: x[0:2] != "__", dir(self))
            for n in range(len(argv)):
                setattr(self, attrs[n], argv[n])

class RGBA(Struct):
    r = 0
    g = 0
    b = 0
    a = 0

class Quat(Struct):
    val1 = 0.0
    val2 = 0.0
    val3 = 0.0
    val4 = 0.0

class HierarchyHeader(Struct):
    version = 0
    hierName = ""
    pivotCount = 0
    centerPos = 0

class HierarchyPivot(Struct):
    pivotName = ""
    parentID = 0
    pos = (0, 0 ,0)
    eulerAngles =(0, 0 ,0)
    rotation = Quat(val1 = 0.0,val2 = 0.0,val3 = 0.0,val4 = 0.0)

class Hierarchy(Struct):
    header = HierarchyHeader()
    pivots = HierarchyPivot()

class W3DVertexMaterial(Struct):
    attributes = 0   #uint32
    ambient = RGBA() #alpha is only padding in this and below
    diffuse = RGBA()
    specular = RGBA()
    emissive = RGBA()
    shininess = 0.0      #how tight the specular highlight will be, 1 - 1000 (default = 1) -float
    opacity  = 0.0       #how opaque the material is, 0.0 = invisible, 1.0 = fully opaque (default = 1) -float
    translucency = 0.0   #how much light passes through the material. (default = 0) -float

class W3DMeshMaterialSetInfo(Struct):
    passCount = 0
    vertMatlCount = 0
    shaderCount = 0
    TextureCount = 0

class W3DMeshFace(Struct):
    vertIds = (0, 0 ,0)
    attrs = 0
    normal = (0, 0 ,0)
    distance = 0.0

class W3DMeshTextureStage(Struct):
    txIds = []
    txCoords = []

class W3DMeshMaterialPass(Struct):
    vmIds = 0
    shaderIds = 0
    txStage = W3DMeshTextureStage()

class W3DMeshMaterial(Struct):
    vmName = ""
    vmInfo = W3DVertexMaterial()
    vmArgs0 = ""
    vmArgs1 = ""

class W3DMeshTexture(Struct):
    txfilename = ""
    txinfo = ""

class W3DMeshHeader(Struct):
    version = 0
    attrs = 0
    meshName = ""
    containerName = ""
    faceCount = 0
    vertCount = 0
    matlCount = 0
    damageStageCount = 0
    sortLevel = 0
    prelitVersion = 0
    futureCount = 0
    vertChannelCount = 0
    faceChannelCount = 0
    minCorner = (0, 0 ,0)
    maxCorner = (0, 0 ,0)
    sphCenter = (0, 0 ,0)
    sphRadius = 0.0
    userText  = ""

class W3DTextureInfo(Struct):
    attributes = 0 #uint16
    animType = 0 #uint16
    frameCount = 0 #uint32
    frameRate = 0.0 #float32

class W3DTexture(Struct):
    linkMap = 0
    name = ""
    textureInfo = W3DTextureInfo()

class W3DMesh(Struct):
    header = W3DMeshHeader()
    verts = []
    normals = []
    vertInfs = []
    faces = []
    shadeIds = []
    matlheader = []
    shaders = []
    vertMatls = []
    textures = []
    matlPass = W3DMeshMaterialPass()

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
    return RGBA(r=file.read(1),g=file.read(1),b=file.read(1),a=file.read(1))

def GetChunkSize(data):
    return (data & int(0x7FFFFFFF))

def ReadLong(file):
    #binary_format = "<l" long
    return (struct.unpack("<L",file.read(4))[0])

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

def ReadHierarchy(file,chunkEnd):
    while file.tell() < chunkEnd:
        file.read(4)

def ReadAABox(file,chunkEnd):
    while file.tell() < chunkEnd:
        file.read(4)

def ReadCompressed_Animation(file,chunkEnd):
    while file.tell() < chunkEnd:
        file.read(4)

def ReadHLod(file,chunkEnd):
    while file.tell() < chunkEnd:
        file.read(4)

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

    return W3DMeshTextureStage(txIds = TextureIds,txCoords = TextureCoords)

def ReadMeshMaterialPass(file, chunkEnd):
    VertexMaterialIds = []
    ShaderIds = []
    TextureStage = W3DMeshTextureStage()
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

    return W3DMeshMaterialPass(vmIds = VertexMaterialIds,shaderIds = ShaderIds,txStage = TextureStage)


def ReadW3DMaterial(file,chunkEnd):
    mat = W3DMeshMaterial()
    while file.tell() < chunkEnd:
        #file.read(4)
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell()+chunkSize

        if chunkType == 44:
            mat.vmName = ReadString(file)
        elif chunkType == 45:
            vmInf = W3DVertexMaterial()
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
    result = W3DMeshFace(vertIds = (ReadLong(file), ReadLong(file), ReadLong(file)),
    attrs = ReadLong(file),
    normal = (ReadFloat(file),ReadFloat(file), ReadFloat(file)),
    distance = ReadFloat(file))
    return result

def ReadMeshMaterialSetInfo (file):
    result = W3DMeshMaterialSetInfo(passCount = ReadLong(file), vertMatlCount = ReadLong(file), shaderCount = ReadLong(file), textureCount = ReadLong(file))
    return result

def ReadTexture(file,chunkEnd):
    tex = W3DTexture()
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize

        if Chunktype == 50:
            tex.name = ReadString(file)
        elif Chunktype == 51:
            tex.textureInfo = W3DTextureInfo(attributes=ReadShort(file),
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
    result = W3DMeshHeader(version = ReadLong(file), attrs =  ReadLong(file), meshName = ReadFixedString(file),
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
    MeshHeader = W3DMeshHeader()
    MeshInfo = W3DMeshMaterialSetInfo()
    MeshFaces = []
    MeshMaterialPass = W3DMeshMaterialPass()
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

    return W3DMesh(header = MeshHeader, verts = MeshVertices, normals = MeshNormals,vertInfs = [],faces = MeshFaces,userText = MeshUsertext,
                shadeIds = MeshShadeIds, matlheader = [],shaders = [],vertMatls = MeshVerticeMats , textures = MeshTextures, matlPass = MeshMaterialPass)


    #reads the file and get chunks and do all the other stuff
def MainImport(givenfilepath,self, context):
    file = open(givenfilepath,"rb")
    file.seek(0,2)
    filesize = file.tell()
    file.seek(0,0)
    Chunknumber = 1
    Meshes = []

    while file.tell() < filesize:
        data = ReadLong(file)
        Chunksize =  GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + Chunksize

        if data == 0:
            Meshes.append(ReadMesh(file, chunkEnd))
            CM = Meshes[len(Meshes)-1]
            file.seek(chunkEnd,0)

        elif data == 256:
            ReadHierarchy(file, chunkEnd)
            file.seek(chunkEnd,0)

        elif data == 512:
            ReadAnimation(file,chunkEnd)
            file.seek(chunkEnd,0)

        elif data == 680:
            ReadCompressed_Animation(file,chunkEnd)
            file.seek(chunkEnd,0)

        elif data == 1792:
            ReadHLod(file,chunkEnd)
            file.seek(chunkEnd,0)

        elif data == 1856:
            ReadAABox(file,chunkEnd)
            file.seek(chunkEnd,0)

        else:
            file.seek(Chunksize,1)

        Chunknumber += 1

    file.close()

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

        mesh_ob = bpy.data.objects.new(m.header.meshName,mesh)
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