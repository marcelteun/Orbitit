#!/bin/sh -e
chk_files="isometry.py geomtypes.py scene_orbit"
pylint $chk_files
