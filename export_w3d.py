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


def MainExport(givenfilepath, self, context):
	print("Run Export")