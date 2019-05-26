#!/bin/sh -e
chk_files="isometry.py geomtypes.py scene_orbit.py geom_gui.py"
pylint $chk_files
