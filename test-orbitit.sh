#!/bin/bash

ccbred=$(echo -e "\033[01;31m")
ccbgreen=$(echo -e "\033[01;32m")
ccgray=$(echo -e "\033[1;30m")
ccwhite=$(echo -e "\033[01;37m")
ccdefault=$(echo -e "\033[0m")

function fail()
{
	echo test $1 "$ccbred" failed"$ccgray"
}

function pass()
{
	echo "test $1 $ccbgreen"passed"$ccgray"
}

function diff_test()
{
	echo -n "$ccdefault"
	diff $1 $2 > /dev/null && pass "$tst" || fail "$tst"
}

echo -n "$ccgray"

# test: output to Python
if [ -z $SKIP_PY_TST ]; then {
	# test isometric shape with default orientation of base shape
	obj="5cubes"
	tst="export $obj to Python"
	./Orbitit.py -y tst/$obj.py tst/tst.py
	diff_test "tst/$obj.py" "tst/tst.py"

	# test isometric shape with a non-default orientation of base shape
	obj="12cubes"
	tst="export $obj to Python"
	./Orbitit.py -y tst/$obj.py tst/tst.py
	diff_test "tst/$obj.py" "tst/tst.py"

	rm tst/tst.py
} fi

# test: output to PS
if [ -z $SKIP_PS_TST ]; then {
	# a simple example, .off input: classic compound of five cubes
	obj="5cubes"
	tst="export $obj to PS"
	./Orbitit.py -p tst/$obj.off tst/tst.ps
	diff_test "tst/$obj.ps" "tst/tst.ps"

	# python: isometric shape with non-default orientation of base shape
	obj="12cubes"
	tst="export $obj to PS"
	./Orbitit.py -p tst/$obj.py tst/tst.ps
	diff_test "tst/$obj.ps" "tst/tst.ps"

	# a cube with a degenerate face
	# and a face for which the 1st 3 vertices cannot be used to calculate
	# the face normal
	obj="cube.degenerate.face"
	tst="export $obj to PS"
	./Orbitit.py -p tst/$obj.py tst/tst.ps
	diff_test "tst/$obj.ps" "tst/tst.ps"

	# some complex uniform star polyhedra examples
	obj="MW115"
	tst="export $obj to PS"
	./Orbitit.py -m 9 -p tst/$obj.off tst/tst.ps
	diff_test "tst/$obj.ps" "tst/tst.ps"

	obj="MW117"
	tst="export $obj to PS"
	./Orbitit.py -m 9 -p tst/$obj.off tst/tst.ps
	diff_test "tst/$obj.ps" "tst/tst.ps"

	obj="MW119"
	tst="export $obj to PS"
	./Orbitit.py -m 9 -p tst/$obj.off tst/tst.ps
	diff_test "tst/$obj.ps" "tst/tst.ps"

	# clean up
	rm tst/tst.ps
} fi
