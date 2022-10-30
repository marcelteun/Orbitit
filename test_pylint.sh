#!/bin/sh -e
chk_files="
	orbitit/__main__.py
	orbitit/geom_gui.py
	orbitit/geomtypes.py
	orbitit/gen_59_icosahedra.py
	orbitit/isometry.py
	orbitit/main_dlg.py
	orbitit/main_win.py
	orbitit/orbit.py
	orbitit/rgb.py
	orbitit/scene_orbit.py
"
pylint --extension-pkg-whitelist=wx $chk_files
