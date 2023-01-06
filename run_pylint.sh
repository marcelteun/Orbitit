#!/bin/sh -e
chk_files="
	orbitit/__main__.py
	orbitit/archimedean_solids.py
	orbitit/geom_2d.py
	orbitit/geom_gui.py
	orbitit/geomtypes.py
	orbitit/gen_59_icosahedra.py
	orbitit/heptagons.py
	orbitit/isometry.py
	orbitit/main_dlg.py
	orbitit/main_win.py
	orbitit/orbit.py
	orbitit/platonic_solids.py
	orbitit/rgb.py
	orbitit/scene_orbit.py
	unittest/test_geom_2d.py
"
pylint --extension-pkg-whitelist=wx $chk_files
