#!/usr/bin/env bash

lib_files=/tmp/profpy_files.txt
python3 setup.py install --record ${lib_files}
cat ${lib_files} | xargs rm -rf
rm ${lib_files}