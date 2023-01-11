#!/bin/sh -e
chk_files="isometry geomtypes geom_3d geom_2d indent"
for filename in $chk_files; do
	echo unit test $filename:
	python3 unittest/test_$filename.py
done
