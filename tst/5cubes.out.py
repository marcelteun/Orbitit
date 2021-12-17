import orbitit
shape = orbitit.Geom3D.IsometricShape(
    Vs=[
        orbitit.geomtypes.Vec3([1, 1, 1]),
        orbitit.geomtypes.Vec3([-1, 1, 1]),
        orbitit.geomtypes.Vec3([-1, -1, 1]),
        orbitit.geomtypes.Vec3([1, -1, 1]),
        orbitit.geomtypes.Vec3([1, 1, -1]),
        orbitit.geomtypes.Vec3([-1, 1, -1]),
        orbitit.geomtypes.Vec3([-1, -1, -1]),
        orbitit.geomtypes.Vec3([1, -1, -1])
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
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([-0.8090169944, -0.5, 0.3090169944, 0]),
            orbitit.geomtypes.Quat([-0.8090169944, 0.5, -0.3090169944, 0]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0.8090169944, -0.3090169944, 0, -0.5]),
            orbitit.geomtypes.Quat([0.8090169944, 0.3090169944, 0, 0.5]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0.5, 0.5, -0.5, -0.5]),
            orbitit.geomtypes.Quat([0.5, -0.5, 0.5, 0.5]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0.5, 0, -0.3090169944, 0.8090169944]),
            orbitit.geomtypes.Quat([0.5, 0, 0.3090169944, -0.8090169944]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0, -0.5, 0.8090169944, 0.3090169944]),
            orbitit.geomtypes.Quat([0, 0.5, -0.8090169944, -0.3090169944]),
        ))
    ],
    unfoldOrbit=False,
    name='5cubes.py',
    orientation=orbitit.geomtypes.Rot3((
        orbitit.geomtypes.Quat([1, 0, 0, 0]),
        orbitit.geomtypes.Quat([1, 0, 0, 0]),
    ))
)
