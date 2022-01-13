#!/bin/sh
set -e
python3 setup.py check
python3 setup.py sdist bdist_wheel

# TEST PKG    : twine check dist/*
# PUBLISH TEST: twine upload --repository testpypi dist/*
# PUBLISH PROD: twine upload dist/*