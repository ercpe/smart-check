TARGET?=tests

VERSION := $(shell grep -Po '"(.*)"' smartcheck/__init__.py | sed -e 's/"//g')

test_default_python:
	python tests/ -v

test_py2:
	@echo Executing test with python2
	python2 tests/ -v

test_py3:
	@echo Executing test with python3
	python3 tests/ -v

test: test_py2 test_py3

compile:
	@echo Compiling python code
	python -m compileall smartcheck/

compile_optimized:
	@echo Compiling python code optimized
	python -O -m compileall smartcheck/

coverage:
	coverage erase
	coverage run --source='.' --omit 'tests/*,setup.py' --branch tests/__main__.py
	coverage report -m

sonar:
	/usr/local/bin/sonar-scanner/bin/sonar-scanner -Dsonar.projectVersion=$(VERSION)

clean:
	find -name "*.py?" -delete
	rm -f coverage.xml testresults.xml
	rm -fr htmlcov dist build smart_check.egg-info

travis: compile compile_optimized test_default_python coverage

jenkins: travis sonar
