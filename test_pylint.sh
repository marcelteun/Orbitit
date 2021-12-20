#!/bin/sh -e
chk_files="
	orbitit/__main__.py
	orbitit/geom_gui.py
	orbitit/geomtypes.py
	orbitit/isometry.py
	orbitit/main_dlg.py
	orbitit/main_win.py
"
pylint --extension-pkg-allow-list=wx $chk_files
