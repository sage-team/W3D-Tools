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
				
class Version(Struct):
    major = 0 
    minor = 0
				
class RGBA(Struct):
    r = 0
    g = 0
    b = 0
    a = 0

class HierarchyHeader(Struct):
    version = Version()
    name = ""
    pivotCount = 0
    centerPos = Vector((0.0, 0.0 ,0.0))

class HierarchyPivot(Struct):
    name = ""
    parentID = 0
    position = Vector((0.0, 0.0 ,0.0))
    eulerAngles = Vector((0.0, 0.0 ,0.0))
    rotation = Quaternion((0.0, 0.0, 0.0, 0.0))
    isBone = 1 

class Hierarchy(Struct):
    header = HierarchyHeader()
    pivots = HierarchyPivot()
    pivot_fixups = []

class Box(Struct): 
    version = Version()
    attributes = 0
    name = ""
    color = RGBA()
    center = Vector((0.0, 0.0 ,0.0))
    extend = Vector((0.0, 0.0 ,0.0))
	
class HLodHeader(Struct):
    version = Version()
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
	
class AnimationHeader(Struct):
    version = Version()
    name = ""
    hieraName = ""
    numFrames = 0
    frameRate = 0
	
class AnimationChannel(Struct):
    firstFrame = 0
    lastFrame = 0
    vectorLen = 0
    type = 0
    pivot = 0
    pad = 0 # padding?
    data = []
	
class Animation(Struct):
    header = AnimationHeader()
    channels = [] 
	
class CompressedAnimationHeader(Struct):
    version = Version()
    name = ""
    hieraName = ""
    numFrames = 0
    frameRate = 0
    flavor = 0
    
class VertexMaterial(Struct):
    attributes = 0   #uint32
    ambient = RGBA() #alpha is only padding in this and below
    diffuse = RGBA()
    specular = RGBA()
    emissive = RGBA()
    shininess = 0.0      #how tight the specular highlight will be, 1 - 1000 (default = 1) -float
    opacity  = 0.0       #how opaque the material is, 0.0 = invisible, 1.0 = fully opaque (default = 1) -float
    translucency = 0.0   #how much light passes through the material. (default = 0) -float

class MeshMaterialSetInfo(Struct):
    passCount = 0
    vertMatlCount = 0
    shaderCount = 0
    TextureCount = 0

class MeshFace(Struct):
    vertIds = Vector((0.0, 0.0 ,0.0))
    attrs = 0
    normal = Vector((0.0, 0.0 ,0.0))
    distance = 0.0

class MeshTextureStage(Struct):
    txIds = []
    txCoords = []

class MeshMaterialPass(Struct):
    vmIds = 0
    shaderIds = 0
    txStage = MeshTextureStage()

class MeshMaterial(Struct):
    vmName = ""
    vmInfo = VertexMaterial()
    vmArgs0 = ""
    vmArgs1 = ""

class MeshTexture(Struct):
    txfilename = ""
    txinfo = ""
	
class TextureInfo(Struct):
    attributes = 0 #uint16
    animType = 0 #uint16
    frameCount = 0 #uint32
    frameRate = 0.0 #float32
	
class MeshShader(Struct):
	depthCompare = 0 
	depthMask = 0 
	colorMask = 0 
	destBlend = 0 
	fogFunc = 0 
	priGradient = 0 
	secGradient = 0 
	srcBlend = 0
	texturing = 0
	detailColorFunc = 0
	detailAlphaFunc = 0
	shaderPreset = 0
	alphaTest = 0
	postDetailColorFunc = 0
	postDetailAlphaFunc = 0 
	pad = 0
	
#W3D_NORMALMAP_HEADER_TYPES
#    W3D_NORMTYPE_TEXTURE = 1,
#    W3D_NORMTYPE_BUMP = 2,
#    W3D_NORMTYPE_COLORS = 5,
#    W3D_NORMTYPE_ALPHA = 7	
class MeshNormalMapHeader(Struct):
    number = 0
    typeName = ""
    reserved = 0

class MeshNormalMapEntryStruct(Struct):
    typeFlag = 0
    typeSize = 0
    infoName = []
    itemSize = 0
    itemName = []
	
class MeshNormalMap(Struct):
    header = MeshNormalMapHeader()
    entryStructs = []
	
class AABTreeHeader(Struct):
    nodeCount = 0
    polyCount = 0
	
class AABTreeNode(Struct):
    min = Vector((0.0, 0.0 ,0.0))
    max = Vector((0.0, 0.0 ,0.0))
    FrontOrPoly0 = 0
    BackOrPolyCount = 0

class MeshAABTree(Struct):
    header = AABTreeHeader()
    polyIndices = []
    nodes = []

class MeshHeader(Struct):
    version = Version()
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

class Texture(Struct):
    linkMap = 0
    name = ""
    textureInfo = TextureInfo()

class Mesh(Struct):
    header = MeshHeader()
    verts = []
    normals = []
    vertInfs = []
    faces = []
    shadeIds = []
    matlheader = []
    shaders = []
    vertMatls = []
    textures = []
    matlPass = MeshMaterialPass()
    aabtree = MeshAABTree()