#!/usr/bin/env python
"""Base class to create compounds of polyhedra."""

import math

V2 = math.sqrt(2)
V3 = math.sqrt(3)
V5 = math.sqrt(5)
V10 = math.sqrt(10)
# ~7.7612 degrees:
H_ACOS_1_3V5_8 = math.acos((1 + 3 * V5) / 8) / 2
# ~9.7356 degrees:
ATAN_3_2V2 = math.atan(3 - 2 * V2)
# ~13.2825256 degrees:
# == acos(np.sqrt(5 + 2 * V5) / V10)
ATAN_V5_2 = math.atan(V5 - 2)
# ~14.3592 degrees:
# == acos( ((V2+1)V5 + V2 - 1 ) / 6 )
ATAN_H_V2_1_V5__1 = math.atan((V2 - 1) * (V5 - 1) / 2)
# ~15.5225 degrees:
ACOS_1_3V5_8 = H_ACOS_1_3V5_8 * 2
# ~19.4712 degrees:
ATAN_V2_4 = math.atan(V2 / 4)
# 20.905
# == asin((V5 - 1) / (2 * V3))
ACOS_V5_1_2V3 = math.acos((V5 + 1) / (2 * V3))
# 22.238756
ACOS_V2_3_V5_8 = math.acos((V2 * (3 + V5)) / 8)
# ~23.4309
ACOS_7_3V5_3_2_2V5_8 = math.acos((-7 + 3 * V5 + 3 * math.sqrt(2 + 2 * V5)) / 8)
# ~24.094843
# == acos(V5 / V6)
ATAN_1_V5 = math.atan(1 / V5)
# ~26.57
TODO_26 = 26.57 * math.pi / 180
# ~31.0449 degrees:
acos_7_3V5_16 = math.acos((7 + 3 * V5) / 16)
# ~31.7175 degrees
# == asin(math.sqrt(5 - V5) / V10)
ACOS_V_5_V5_V10 = math.acos(math.sqrt(5 + V5) / V10)
# ~33.8305 degrees:
ATAN_H_V2_1_V5_1 = math.atan((V2 - 1) * (1 + V5) / 2)
# ~35.2644 degrees:
ASIN_1_V3 = math.asin(1 / V3)
# 37.761244:
ACOS_V10_4 = math.acos(V10 / 4)
# ~38.9424 degrees:
ATAN_4V2_7 = math.atan(4 * V2 / 7)
# ~41.81 degrees
TODO_41 = 41.81 * math.pi / 180
# ~44.4775 degrees
# == ACOS__1_3V5_8 = math.acos((-1 + 3 * V5) / 8)
D_ATAN_V3_2_V5 = -2 * math.atan(V3 * (2 - V5))
# ~54.7356 degrees:
ACOS_1_V3 = math.acos(1 / V3)
# ~56.1695
ACOS_V2_1_V5_V2_1__6 = math.acos(((V2 - 1) * V5 + V2 + 1) / 6)
# ~58.282526:
# == acos(math.sqrt(5 - V5) / V10)
ASIN_V_5_V5_V10 = math.asin(math.sqrt(5 + V5) / V10)
# ~69.0948 degrees
# == acos((V5 - 1) / (2 * V3))
ASIN_V5_1_2V3 = math.asin((V5 + 1) / (2 * V3))
# ~70.5288 degrees
ASIN_2V2_3 = math.asin(2 * V2 / 3)
