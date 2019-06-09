import geomtypes
import Geom3D
import isometry
shape = Geom3D.IsometricShape(
    Vs=[
        geomtypes.Vec3([1.0, 1.0, 1.0]),
        geomtypes.Vec3([-1.0, 1.0, 1.0]),
        geomtypes.Vec3([-1.0, -1.0, 1.0]),
        geomtypes.Vec3([1.0, -1.0, 1.0]),
        geomtypes.Vec3([1.0, 1.0, -1.0]),
        geomtypes.Vec3([-1.0, 1.0, -1.0]),
        geomtypes.Vec3([-1.0, -1.0, -1.0]),
        geomtypes.Vec3([1.0, -1.0, -1.0])
    ],
    Fs=[
        [0, 1, 2, 3],
        [0, 3, 7, 4],
        [1, 0, 4, 5],
        [2, 1, 5, 6],
        [3, 2, 6, 7],
        [7, 6, 5, 4]
    ],
    Es=[0, 1, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 4, 4, 5, 1, 5, 5, 6, 2, 6, 6, 7],
    colors=[
        ([[0.996094, 0.839844, 0.0]], []),
        ([[0.132812, 0.542969, 0.132812]], []),
        ([[0.542969, 0.0, 0.0]], []),
        ([[0.0, 0.746094, 0.996094]], []),
        ([[0.542969, 0.523438, 0.304688]], [])
    ],
    directIsometries=[
        geomtypes.Rot3((
            geomtypes.Quat([-0.809016994375, -0.5, 0.309016994375, -3.08426926158e-14]),
            geomtypes.Quat([-0.809016994375, 0.5, -0.309016994375, 3.08426926158e-14]),
        )),
        geomtypes.Rot3((
            geomtypes.Quat([0.809016994375, -0.309016994375, -4.98739097981e-14, -0.5]),
            geomtypes.Quat([0.809016994375, 0.309016994375, 4.98739097981e-14, 0.5]),
        )),
        geomtypes.Rot3((
            geomtypes.Quat([0.5, 0.5, -0.5, -0.5]),
            geomtypes.Quat([0.5, -0.5, 0.5, 0.5]),
        )),
        geomtypes.Rot3((
            geomtypes.Quat([0.5, -4.53526105559e-14, -0.309016994375, 0.809016994375]),
            geomtypes.Quat([0.5, 4.53526105559e-14, 0.309016994375, -0.809016994375]),
        )),
        geomtypes.Rot3((
            geomtypes.Quat([4.582785177e-15, -0.5, 0.809016994375, 0.309016994375]),
            geomtypes.Quat([4.582785177e-15, 0.5, -0.809016994375, -0.309016994375]),
        ))
    ],
    unfoldOrbit=False,
    name='5cubes.py',
    orientation=geomtypes.Rot3((
        geomtypes.Quat([1.0, 0.0, 0.0, 0.0]),
        geomtypes.Quat([1.0, -0.0, -0.0, -0.0]),
    ))
)
