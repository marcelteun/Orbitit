## License

With this program you can interactively investigate some polyhedra. I use this
program myself and I am willing to share it with other who are interested. I use
Ubuntu, as a consequence some problems might exist with windows.

Copyright (C) 2021 Marcel Tunnissen
http://www.tunnissen.eu

License: GPLv2, see LICENCSE.txt

## wxPython

When wxPython is installed through pip it is compiled. This can take quite some
time (e.g. more than 15 minutes). This means that there should be c-compiler
available at least. For a Debian Linux you would need have installed (e.g.
through apt-get) the packages
 - build-essential
 - libgtk-3-dev and libwxgtk3.0-gtk3-dev (or whathever GTK version you are using)
 - python3-dev
 - libgl1-mesa-glx libglu1-mesa

The reason for me to choose wxPython over Tk was that I ran into quite some
preformance problems with Tk. The disadvantage is that it can be a pain to
install wxPython through pip.

## If You Install through PyPI (pip install)

Also here it is important to have the correct packages for building wxPython
installed. See section [wxPython](wxPython)" above.

### Install
`pip install orbitit`

### Run
`python -m orbitit`

## If You Downloaded from Github Directly

### Requirements

You will need:
1. python 3.x:  http://www.python.org
2. wxPython: http://www.wxpython.org
3. pyOpenGL: http://pyopengl.sourceforge.net/

### Install

E.g. for Ubuntu or other Debian based Linux dist:
`sudo apt-get install python3 python3-pip`

Then use pip to install other packages, e.g:
`pip3 install pyopengl wxpython`

See section [wxPython](#wxPython) for more about installing wxPython through pip.

### Run
Make sure the `PYTHONPATH` points out this directory, e.g. in Linux
`export PYTHONPATH=$PWD`

Also make sure to have set the `PYOPENGL_PLATFORM` environment variable.
On my system I do
```
source init_env
python orbitit
```

## Errors

### 1.
If you get problems with a context not being valid, e.g.
OpenGL.error.Error: Attempt to retrieve context when no valid context

Then this might be related to eht wrong `PYOPENGL_PLATFORM`
In my case this problem was solved by

`PYOPENGL_PLATFORM=egl python -m orbitit`

### 2.
If you get problems with NotImplementedError on GLCanvas you probably built
wxPython without the wxgtk support. See section [wxPython](#wxPython) above.
