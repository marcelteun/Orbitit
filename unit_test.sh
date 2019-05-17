#!/bin/sh -e
chk_files="isometry.py geomtypes.py"
for filename in $chk_files; do
	echo unit test $filename:
	PYTHONPATH=$PWD python  unittest/tst_$filename
done
