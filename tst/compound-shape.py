import Geom3D
import geomtypes

Vs = [
	geomtypes.Vec3([ 1,  1,  1]),
	geomtypes.Vec3([-1,  1,  1]),
	geomtypes.Vec3([-1, -1,  1]),
	geomtypes.Vec3([ 1, -1,  1]),
	geomtypes.Vec3([ 1,  1, -1]),
	geomtypes.Vec3([-1,  1, -1]),
	geomtypes.Vec3([-1, -1, -1]),
	geomtypes.Vec3([ 1, -1, -1]),
	geomtypes.Vec3([ 1,  1, -2]),
	geomtypes.Vec3([.5,  1,  1]),
]

Fs = [
	[0, 1, 2, 3],
	[0, 3, 7, 4],
	[1, 0, 4, 5],
	[2, 1, 5, 6],
	[3, 2, 6, 7],
	[7, 6, 5, 4]
]

shape0 = Geom3D.SimpleShape(Vs = Vs, Fs = Fs)

Vs = [
	geomtypes.Vec3([ 0,  0,  2]),
	geomtypes.Vec3([ 2,  0,  0]),
	geomtypes.Vec3([ 0,  2,  0]),
	geomtypes.Vec3([-2,  0,  0]),
	geomtypes.Vec3([ 0, -2,  0]),
	geomtypes.Vec3([ 0,  0,  2]),
]

Fs = [
        [0, 1, 2],
        [0, 2, 3],
        [0, 3, 4],
        [0, 4, 1],
        [5, 2, 1],
        [5, 3, 2],
        [5, 4, 3],
        [5, 1, 4],
]

shape1 = Geom3D.SimpleShape(Vs = Vs, Fs = Fs)

shape = Geom3D.CompoundShape([shape0, shape1])
