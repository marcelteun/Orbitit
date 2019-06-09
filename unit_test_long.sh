#!/bin/sh -e
chk_files="geom3d"
for filename in $chk_files; do
	echo unit test $filename:
	PYTHONPATH=$PWD python  unittest/tst_${filename}_slow.py
done
