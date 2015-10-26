# -*- coding: utf-8 -*-
from argparse import ArgumentParser
import os
import sys
from smartcheck.check import SMARTCheck, AttributeWarning

DEFAULT_DATA_FILE=os.path.join(os.path.dirname(__file__), 'disks.yaml')

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('--data-file', default=DEFAULT_DATA_FILE)
	parser.add_argument('-f', '--file', help="Use S.M.A.R.T. report from file instead of calling smartctl (Use - to read from stdin)")
	parser.add_argument('-x', '--exclude-notices', help='Report NOTICE warnings (default: %(default)s)', action='store_true', default=False)
	parser.add_argument('-v', '--verbose', help='Verbose messages', action='store_true', default=False)

	args = parser.parse_args()

	stream = None
	if args.file:
		if args.file == '-':
			stream = sys.stdin
		else:
			stream = open(args.file, 'r')

	check = SMARTCheck(stream, args.data_file)

	exit_code = 0
	msg = ""

	attribute_errors = check.check_attributes()

	if args.exclude_notices:
		for k in [x for x, y in attribute_errors.items() if y.level == AttributeWarning.Notice]:
			del attribute_errors[k]

	if any((ae.level == AttributeWarning.Warning for ae in attribute_errors.values())):
		msg = ', '.join([ae.long_message if args.verbose else ae.short_message for ae in attribute_errors.values()])
		exit_code = 1
	if any((ae.level == AttributeWarning.Critical for ae in attribute_errors.values())):
		msg = ', '.join([ae.long_message if args.verbose else ae.short_message for ae in attribute_errors.values()])
		exit_code = 2
	if not check.check_tests():
		msg = (msg + '; S.M.A.R.T. self test reported an error').lstrip(';').strip()
		exit_code = 2

	if not exit_code:
		msg = "S.M.A.R.T. data OK"

	print(msg)
	sys.exit(exit_code)
