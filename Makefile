TARGET?=tests

test:
	PYTHONPATH=".:./src" python tests/

coverage:
	coverage erase
	PYTHONPATH=".:./src" coverage run --source='src' --omit='src/test.py' --branch tests/__main__.py
	coverage report -m
