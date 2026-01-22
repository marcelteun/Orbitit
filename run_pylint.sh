#!/bin/sh -e
chk_files="
	orbitit/__main__.py
	orbitit/archimedean_solids.py
	orbitit/base.py
	orbitit/colors.py
	orbitit/geom_2d.py
	orbitit/geom_3d.py
	orbitit/geom_gui.py
	orbitit/geomtypes.py
	orbitit/heptagons.py
	orbitit/indent.py
	orbitit/isometry.py
	orbitit/main_dlg.py
	orbitit/main_win.py
	orbitit/orbit.py
	orbitit/platonic_solids.py
	orbitit/pre_pyopengl.py
	orbitit/rgb.py
	orbitit/scene_eql_hept_from_kite.py
	orbitit/scene_orbit.py
	orbitit/wx_colors.py
	orbitit/compounds/angle.py
	orbitit/compounds/S4A4.py
	orbitit/compounds/S4xI.py
	orbitit/compounds/generate.py
	unittest/test_geom_2d.py
	unittest/test_geom_3d.py
	unittest/test_geom_3d_long.py
	unittest/test_geomtypes.py
	unittest/test_indent.py
	unittest/test_isometry.py
	utils/generate_59_icosahedra.py
	utils/generate_compound_polyhedra.py
"
pylint --version
pylint $chk_files
