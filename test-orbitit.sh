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

echo -n "$ccgray"

# test output to PS
./Orbitit.py -p tst/5cubes.off tst/tst.ps
echo -n "$ccdefault"
test="export 5cubes to PS"
diff tst/tst.ps tst/5cubes.ps > /dev/null && pass "$test" || fail "$test"

rm tst/tst.ps
