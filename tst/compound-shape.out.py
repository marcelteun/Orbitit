import geomtypes
import geom_3d
import isometry
shape = geom_3d.CompoundShape(
    shapes = [
        geom_3d.SimpleShape(
            vs = [
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
            fs = [
                [0, 1, 2, 3],
                [0, 3, 7, 4],
                [1, 0, 4, 5],
                [2, 1, 5, 6],
                [3, 2, 6, 7],
                [7, 6, 5, 4]
            ],
            es = [],
            colors = ([[0.99609400000000003, 0.0, 0.0]], [0, 0, 0, 0, 0, 0]),
            name = "SimpleShape"
        ),
        geom_3d.SimpleShape(
            vs = [
                geomtypes.Vec3([0.0, 0.0, 2.0]),
                geomtypes.Vec3([2.0, 0.0, 0.0]),
                geomtypes.Vec3([0.0, 2.0, 0.0]),
                geomtypes.Vec3([-2.0, 0.0, 0.0]),
                geomtypes.Vec3([0.0, -2.0, 0.0]),
                geomtypes.Vec3([0.0, 0.0, 2.0])
            ],
            fs = [
                [0, 1, 2],
                [0, 2, 3],
                [0, 3, 4],
                [0, 4, 1],
                [5, 2, 1],
                [5, 3, 2],
                [5, 4, 3],
                [5, 1, 4]
            ],
            es = [],
            colors = ([[0.99609400000000003, 0.0, 0.0]], [0, 0, 0, 0, 0, 0, 0, 0]),
            name = "SimpleShape"
        )
    ],
    name = "CompoundShape"
)
