import GeomTypes
import Geom3D
import isometry
shape = Geom3D.SimpleShape(
    Vs = [
        GeomTypes.Vec3([1.0, 1.0, 1.0]),
        GeomTypes.Vec3([-1.0, 1.0, 1.0]),
        GeomTypes.Vec3([-1.0, -1.0, 1.0]),
        GeomTypes.Vec3([1.0, -1.0, 1.0]),
        GeomTypes.Vec3([1.0, 1.0, -1.0]),
        GeomTypes.Vec3([-1.0, 1.0, -1.0]),
        GeomTypes.Vec3([-1.0, -1.0, -1.0]),
        GeomTypes.Vec3([1.0, -1.0, -1.0]),
        GeomTypes.Vec3([1.0, 1.0, -2.0]),
        GeomTypes.Vec3([0.5, 1.0, 1.0])
    ],
    Fs = [
        [0, 4, 8],
        [0, 9, 1, 2, 3],
        [0, 3, 7, 4],
        [1, 0, 4, 5],
        [2, 1, 5, 6],
        [3, 2, 6, 7],
        [7, 6, 5, 4]
    ],
    Es = [],
    colors = ([[0.99609400000000003, 0.0, 0.0]], [0, 0, 0, 0, 0, 0, 0]),
    name = "SimpleShape"
)
