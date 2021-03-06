import geomtypes
import Geom3D
import isometry
shape = Geom3D.SimpleShape(
    Vs=[
        geomtypes.Vec3([1.0, 1.0, 1.0]),
        geomtypes.Vec3([-1.0, 1.0, 1.0]),
        geomtypes.Vec3([-1.0, -1.0, 1.0]),
        geomtypes.Vec3([1.0, -1.0, 1.0]),
        geomtypes.Vec3([1.0, 1.0, -1.0]),
        geomtypes.Vec3([-1.0, 1.0, -1.0]),
        geomtypes.Vec3([-1.0, -1.0, -1.0]),
        geomtypes.Vec3([1.0, -1.0, -1.0]),
        geomtypes.Vec3([1.0, 1.0, -2.0]),
        geomtypes.Vec3([0.5, 1.0, 1.0])
    ],
    Fs=[
        [0, 4, 8],
        [0, 9, 1, 2, 3],
        [0, 3, 7, 4],
        [1, 0, 4, 5],
        [2, 1, 5, 6],
        [3, 2, 6, 7],
        [7, 6, 5, 4]
    ],
    Es=[0, 4, 4, 8, 0, 8, 0, 9, 1, 9, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 1, 4, 5, 1, 5, 5, 6, 2, 6, 6, 7],
    colors=([[0.945312, 0.945312, 0.945312]], [0, 0, 0, 0, 0, 0, 0]),
    name="SimpleShape"
)
