#Struct
from mathutils import Vector, Quaternion

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

class HieraHeader(Struct):
    version = 0
    hierName = ""
    pivotCount = 0
    centerPos = Vector((0.0, 0.0 ,0.0))

class HieraPivot(Struct):
    name = ""
    parentID = 0
    position = Vector((0.0, 0.0 ,0.0))
    eulerAngles = Vector((0.0, 0.0 ,0.0))
    rotation = Quaternion((0.0, 0.0, 0.0, 0.0))
    isbone = 1 

class Hiera(Struct):
    header = HieraHeader()
    pivots = HieraPivot()
    pivot_fixups = []

class AABox(Struct): 
    version = 0
    attributes = 0
    name = ""
    color = RGBA()
    center = Vector((0.0, 0.0 ,0.0))
    extend = Vector((0.0, 0.0 ,0.0))
	
class HLodHeader(Struct):
    version = 0
    lodCount = 0
    modelName = ""
    HTreeName = ""
	
class HLodArrayHeader(Struct):
    modelCount = 0
    maxScreenSize = 0.0

class HLodSubObject(Struct):
    name = ""
    boneIndex = 0

class HLodArray(Struct):
    header = HLodArrayHeader()
    subObjects = []
    
class HLod(Struct):
    header = HLodHeader()
    lodArray = HLodArray()
    
class VtxMat(Struct):
    attributes = 0   #uint32
    ambient = RGBA() #alpha is only padding in this and below
    diffuse = RGBA()
    specular = RGBA()
    emissive = RGBA()
    shininess = 0.0      #how tight the specular highlight will be, 1 - 1000 (default = 1) -float
    opacity  = 0.0       #how opaque the material is, 0.0 = invisible, 1.0 = fully opaque (default = 1) -float
    translucency = 0.0   #how much light passes through the material. (default = 0) -float

class MshMatSetInfo(Struct):
    passCount = 0
    vertMatlCount = 0
    shaderCount = 0
    TextureCount = 0

class MshFace(Struct):
    vertIds = Vector((0.0, 0.0 ,0.0))
    attrs = 0
    normal = Vector((0.0, 0.0 ,0.0))
    distance = 0.0

class MshTexStage(Struct):
    txIds = []
    txCoords = []

class MshMatPass(Struct):
    vmIds = 0
    shaderIds = 0
    txStage = MshTexStage()

class MshMat(Struct):
    vmName = ""
    vmInfo = VtxMat()
    vmArgs0 = ""
    vmArgs1 = ""

class MshTex(Struct):
    txfilename = ""
    txinfo = ""
	
class AABTreeHeader(Struct):
    nodeCount = 0
    polyCount = 0
	
class AABTreeNode(Struct):
    min = Vector((0.0, 0.0 ,0.0))
    max = Vector((0.0, 0.0 ,0.0))
    FrontOrPoly0 = 0
    BackOrPolyCount = 0

class MshAABTree(Struct):
    header = AABTreeHeader()
    polyIndices = []
    nodes = []

class MshHeader(Struct):
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
    minCorner = Vector((0.0, 0.0 ,0.0))
    maxCorner = Vector((0.0, 0.0 ,0.0))
    sphCenter = Vector((0.0, 0.0 ,0.0))
    sphRadius = 0.0
    userText  = ""

class TexInfo(Struct):
    attributes = 0 #uint16
    animType = 0 #uint16
    frameCount = 0 #uint32
    frameRate = 0.0 #float32

class Tex(Struct):
    linkMap = 0
    name = ""
    textureInfo = TexInfo()

class Msh(Struct):
    header = MshHeader()
    verts = []
    normals = []
    vertInfs = []
    faces = []
    shadeIds = []
    matlheader = []
    shaders = []
    vertMatls = []
    textures = []
    matlPass = MshMatPass()
    aabtree = MshAABTree()