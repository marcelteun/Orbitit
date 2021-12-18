#!/bin/sh -e
chk_files="
	orbitit/isometry.py
	orbitit/geomtypes.py
	orbitit/scene_orbit.py
	orbitit/geom_gui.py
"
pylint --extension-pkg-allow-list=wx $chk_files
