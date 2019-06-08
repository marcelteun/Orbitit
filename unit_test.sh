#!/bin/sh -e
chk_files="isometry geomtypes geom3d"
for filename in $chk_files; do
	echo unit test $filename:
	PYTHONPATH=$PWD python  unittest/tst_$filename.py
done
