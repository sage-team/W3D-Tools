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


def WriteString(string, file):
	#TODO: check if it does write nullterminated strings
   	file.write(string)
    return

def WriteFixedString(string,file):
	#truncate the string to 16
	nullbytes = 16-len(string)
	if(nullbytes<0)
		print("Warning: Fixed string is too long")

	file.write(string)
	for i in xrange(nullbytes)
		file.write(struct.pack("c",'\0'))

def WriteByte(num,file):
    file.write(struct.pack("<B",num))

def WriteByteSigned(num,file):
    file.write(struct.pack("<´b",num))

def WriteShort(num,file):
    file.write(struct.pack("<H",num))

def WriteShortSigned(num,file):
    file.write(struct.pack("<h",num))

def WriteLong(num,file):
    file.write(struct.pack("<L",num))

def WriteLongSigned(num,file):
    file.write(struct.pack("<l",num))

def WriteFloat(num,file):
    file.write(struct.pack("<f",num))


def MainExport(givenfilepath, self, context):
	print("Run Export")