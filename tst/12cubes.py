import orbitit
shape = orbitit.geom_3d.SymmetricShape(
  vs = [
    orbitit.geomtypes.Vec3([1.0, 1.0, 1.0]),
    orbitit.geomtypes.Vec3([-1.0, 1.0, 1.0]),
    orbitit.geomtypes.Vec3([-1.0, -1.0, 1.0]),
    orbitit.geomtypes.Vec3([1.0, -1.0, 1.0]),
    orbitit.geomtypes.Vec3([1.0, 1.0, -1.0]),
    orbitit.geomtypes.Vec3([-1.0, 1.0, -1.0]),
    orbitit.geomtypes.Vec3([-1.0, -1.0, -1.0]),
    orbitit.geomtypes.Vec3([1.0, -1.0, -1.0]),
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
    ([[0.54296900000000003, 0.0, 0.0]], []),
    ([[0.13281200000000001, 0.54296900000000003, 0.13281200000000001]], []),
    ([[0.0, 0.74609400000000003, 0.99609400000000003]], []),
    ([[0.0, 0.74609400000000003, 0.99609400000000003]], []),
    ([[0.99609400000000003, 0.83984400000000003, 0.0]], []),
    ([[0.54296900000000003, 0.0, 0.0]], []),
    ([[0.13281200000000001, 0.54296900000000003, 0.13281200000000001]], []),
    ([[0.99609400000000003, 0.83984400000000003, 0.0]], []),
  ],
  isometries = [
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([-0.5, 0.5, -0.5, -0.5]), orbitit.geomtypes.Quat([-0.5, -0.5, 0.5, 0.5]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([-0.707106781187, 1.04526690545e-16, -0.707106781187, 4.32963728536e-17]), orbitit.geomtypes.Quat([-0.707106781187, -1.04526690545e-16, 0.707106781187, -4.32963728536e-17]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([-1.22460635382e-16, 6.12303176911e-17, -0.707106781187, -0.707106781187]), orbitit.geomtypes.Quat([-1.22460635382e-16, -6.12303176911e-17, 0.707106781187, 0.707106781187]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([0.707106781187, -0.707106781187, -6.12303176911e-17, -6.12303176911e-17]), orbitit.geomtypes.Quat([0.707106781187, 0.707106781187, 6.12303176911e-17, 6.12303176911e-17]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([-3.33066907388e-16, -0.707106781187, 0.707106781187, 3.08170915002e-16]), orbitit.geomtypes.Quat([-3.33066907388e-16, 0.707106781187, -0.707106781187, -3.33066907388e-16]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([0.5, -0.5, -0.5, -0.5]), orbitit.geomtypes.Quat([0.5, 0.5, 0.5, 0.5]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([-0.5, -0.5, 0.5, -0.5]), orbitit.geomtypes.Quat([-0.5, 0.5, -0.5, 0.5]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([3.74915180456e-33, 0.707106781187, 6.12303176911e-17, -0.707106781187]), orbitit.geomtypes.Quat([3.74915180456e-33, -0.707106781187, -6.12303176911e-17, 0.707106781187]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([-0.707106781187, -0.707106781187, -6.12303176911e-17, 6.12303176911e-17]), orbitit.geomtypes.Quat([-0.707106781187, 0.707106781187, 6.12303176911e-17, -6.12303176911e-17]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([6.12303176911e-17, 0.707106781187, -2.46519032882e-32, 0.707106781187]), orbitit.geomtypes.Quat([6.12303176911e-17, -0.707106781187, 2.46519032882e-32, -0.707106781187]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([3.33066907388e-16, 1.11022302463e-16, -0.707106781187, 0.707106781187]), orbitit.geomtypes.Quat([3.33066907388e-16, -1.11022302463e-16, 0.707106781187, -0.707106781187]))),
    orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([0.707106781187, 4.32963728536e-17, -0.707106781187, -1.04526690545e-16]), orbitit.geomtypes.Quat([0.707106781187, -4.32963728536e-17, 0.707106781187, 1.04526690545e-16]))),
  ],
  name = "12cubes.py",
  orientation = orbitit.geomtypes.Rot3((orbitit.geomtypes.Quat([0.953020613871, 0.214186495298, 0.0, 0.214186495298]), orbitit.geomtypes.Quat([0.953020613871, -0.214186495298, -0.0, -0.214186495298])))
)
