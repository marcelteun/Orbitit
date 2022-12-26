import orbitit
shape = orbitit.geom_3d.SymmetricShape(
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
        ([[0.542969, 0.0, 0.0]], []),
        ([[0.132812, 0.542969, 0.132812]], []),
        ([[0.0, 0.746094, 0.996094]], []),
        ([[0.0, 0.746094, 0.996094]], []),
        ([[0.996094, 0.839844, 0.0]], []),
        ([[0.542969, 0.0, 0.0]], []),
        ([[0.132812, 0.542969, 0.132812]], []),
        ([[0.996094, 0.839844, 0.0]], [])
    ],
    isometries=[
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([-0.5, 0.5, -0.5, -0.5]),
            orbitit.geomtypes.Quat([-0.5, -0.5, 0.5, 0.5]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([-0.7071067812, 0, -0.7071067812, 0]),
            orbitit.geomtypes.Quat([-0.7071067812, 0, 0.7071067812, 0]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0, 0, -0.7071067812, -0.7071067812]),
            orbitit.geomtypes.Quat([0, 0, 0.7071067812, 0.7071067812]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0.7071067812, -0.7071067812, 0, 0]),
            orbitit.geomtypes.Quat([0.7071067812, 0.7071067812, 0, 0]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0, -0.7071067812, 0.7071067812, 0]),
            orbitit.geomtypes.Quat([0, 0.7071067812, -0.7071067812, 0]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0.5, -0.5, -0.5, -0.5]),
            orbitit.geomtypes.Quat([0.5, 0.5, 0.5, 0.5]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([-0.5, -0.5, 0.5, -0.5]),
            orbitit.geomtypes.Quat([-0.5, 0.5, -0.5, 0.5]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0, 0.7071067812, 0, -0.7071067812]),
            orbitit.geomtypes.Quat([0, -0.7071067812, 0, 0.7071067812]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([-0.7071067812, -0.7071067812, 0, 0]),
            orbitit.geomtypes.Quat([-0.7071067812, 0.7071067812, 0, 0]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0, 0.7071067812, 0, 0.7071067812]),
            orbitit.geomtypes.Quat([0, -0.7071067812, 0, -0.7071067812]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0, 0, -0.7071067812, 0.7071067812]),
            orbitit.geomtypes.Quat([0, 0, 0.7071067812, -0.7071067812]),
        )),
        orbitit.geomtypes.Rot3((
            orbitit.geomtypes.Quat([0.7071067812, 0, -0.7071067812, 0]),
            orbitit.geomtypes.Quat([0.7071067812, 0, 0.7071067812, 0]),
        ))
    ],
    name='12cubes.py',
    orientation=orbitit.geomtypes.Rot3((
        orbitit.geomtypes.Quat([0.9530206139, 0.2141864953, 0, 0.2141864953]),
        orbitit.geomtypes.Quat([0.9530206139, -0.2141864953, 0, -0.2141864953]),
    ))
)
