from orbitit import geom_3d, geomtypes
shape = geom_3d.SymmetricShape(
  vs = [
    geomtypes.Vec3([1.0, 1.0, 1.0]),
    geomtypes.Vec3([-1.0, 1.0, 1.0]),
    geomtypes.Vec3([-1.0, -1.0, 1.0]),
    geomtypes.Vec3([1.0, -1.0, 1.0]),
    geomtypes.Vec3([1.0, 1.0, -1.0]),
    geomtypes.Vec3([-1.0, 1.0, -1.0]),
    geomtypes.Vec3([-1.0, -1.0, -1.0]),
    geomtypes.Vec3([1.0, -1.0, -1.0]),
  ],
  fs = [
    [0, 1, 2, 3],
    [0, 3, 7, 4],
    [1, 0, 4, 5],
    [2, 1, 5, 6],
    [3, 2, 6, 7],
    [7, 6, 5, 4],
  ],
  es = [0, 1, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 4, 4, 5, 1, 5, 5, 6, 2, 6, 6, 7],
  colors = [
    ([[0.99609400000000003, 0.83984400000000003, 0.0]], []),
    ([[0.13281200000000001, 0.54296900000000003, 0.13281200000000001]], []),
    ([[0.54296900000000003, 0.0, 0.0]], []),
    ([[0.0, 0.74609400000000003, 0.99609400000000003]], []),
    ([[0.54296900000000003, 0.52343799999999996, 0.30468800000000001]], []),
  ],
  isometries = [
    geomtypes.Rot3((geomtypes.Quat([-0.809016994375, -0.5, 0.309016994375, -3.08426926158e-14]), geomtypes.Quat([-0.809016994375, 0.5, -0.309016994375, 3.08426926158e-14]))),
    geomtypes.Rot3((geomtypes.Quat([0.809016994375, -0.309016994375, -4.98739097981e-14, -0.5]), geomtypes.Quat([0.809016994375, 0.309016994375, 4.98739097981e-14, 0.5]))),
    geomtypes.Rot3((geomtypes.Quat([0.5, 0.5, -0.5, -0.5]), geomtypes.Quat([0.5, -0.5, 0.5, 0.5]))),
    geomtypes.Rot3((geomtypes.Quat([0.5, -4.53526105559e-14, -0.309016994375, 0.809016994375]), geomtypes.Quat([0.5, 4.53526105559e-14, 0.309016994375, -0.809016994375]))),
    geomtypes.Rot3((geomtypes.Quat([4.582785177e-15, -0.5, 0.809016994375, 0.309016994375]), geomtypes.Quat([4.582785177e-15, 0.5, -0.809016994375, -0.309016994375]))),
  ],
  name = "5cubes.py",
  orientation = geomtypes.Rot3((geomtypes.Quat([1.0, 0.0, 0.0, 0.0]), geomtypes.Quat([1.0, -0.0, -0.0, -0.0])))
)
