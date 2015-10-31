TARGET?=tests

test: test-py2 test-py3

test-py2:
	PYTHONPATH=".:./src" python2 tests/

test-py3:
	PYTHONPATH=".:./src" python3 tests/

coverage:
	coverage erase
	PYTHONPATH=".:./src" coverage run --source='src' --omit='src/test.py' --branch tests/__main__.py
	coverage report -m
