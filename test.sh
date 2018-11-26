#!/usr/bin/env bash
python3 test/create_test_tables.py
python3 -m unittest discover -s test