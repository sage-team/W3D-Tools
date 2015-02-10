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