#!/bin/sh -e
chk_files="isometry geomtypes geom3d"
for filename in $chk_files; do
	echo unit test $filename:
	python3 unittest/tst_$filename.py
done
