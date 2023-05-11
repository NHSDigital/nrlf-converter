#!/bin/bash

set -e

cd dist
python -m venv venv-test
source venv-test/bin/activate

mkdir -p integration/tests
mkdir -p nrl/tests/data

cp $(find ../nrlf_converter -name test_integration.py) integration/tests
cp ../nrlf_converter/nrl/tests/data/* nrl/tests/data/

pip install pytest requests *gz
python -m pytest -m 'integration'
