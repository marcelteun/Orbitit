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

# test: output to PS
obj="5cubes"
tst="export $obj to PS"
./Orbitit.py -p tst/$obj.off tst/tst.ps
diff_test "tst/$obj.ps" "tst/tst.ps"

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

rm tst/tst.ps
