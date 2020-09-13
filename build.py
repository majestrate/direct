#!/usr/bin/env python3.8
import os
import subprocess
import platform

join = os.path.join

def libname(modname):
    maj,min,patch = platform.python_version_tuple()
    return "{}.{}-{}-{}-linux-gnu.so".format(modname, platform.python_implementation().lower(), '{}{}'.format(maj,min) ,platform.machine())

def lokimq():

    yield "git submodule update --init --recursive"
    yield "mkdir -p build"
    yield "cmake -B build {}".format(join("external", "pylokimq"))
    yield "make -C build"
    yield "mkdir -p lib"
    yield "cp {} {}".format(join("build", "pylokimq",libname("pylokimq")), "lib")

for cmd in lokimq():
    print(" --- {}".format(cmd))
    subprocess.run(cmd.split(' '))