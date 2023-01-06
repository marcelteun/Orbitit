#!/bin/sh -e
chk_files="geom_3d"
for filename in $chk_files; do
	echo unit test $filename:
	python3 unittest/test_${filename}_long.py
done
