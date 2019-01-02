#!/usr/bin/env bash
echo "Creating tables, if needed..."
python3 test/create_test_tables.py
echo "Done."
echo "Running tests..."
python3 -m unittest discover -s test
echo "Removing test tables..."
python3 test/remove_test_tables.py
echo "Done."