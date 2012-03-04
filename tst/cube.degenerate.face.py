import Geom3D
import GeomTypes
import math

Vs = [
	GeomTypes.Vec3([ 1,  1,  1]),
	GeomTypes.Vec3([-1,  1,  1]),
	GeomTypes.Vec3([-1, -1,  1]),
	GeomTypes.Vec3([ 1, -1,  1]),
	GeomTypes.Vec3([ 1,  1, -1]),
	GeomTypes.Vec3([-1,  1, -1]),
	GeomTypes.Vec3([-1, -1, -1]),
	GeomTypes.Vec3([ 1, -1, -1]),
	GeomTypes.Vec3([ 1,  1, -2]),
	GeomTypes.Vec3([.5,  1,  1]),
]

Fs = [
	[0, 4, 8],      # just a line
        [0, 9, 1, 2, 3],# first part on line, cannot be used to calc face normal
	[0, 3, 7, 4],
	[1, 0, 4, 5],
	[2, 1, 5, 6],
	[3, 2, 6, 7],
	[7, 6, 5, 4]
]

shape = Geom3D.SimpleShape(Vs = Vs, Fs = Fs)
