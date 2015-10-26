# -*- coding: utf-8 -*-
from argparse import ArgumentParser
import os
import sys
from smartcheck.check import SMARTCheck

DEFAULT_DATA_FILE=os.path.join(os.path.dirname(__file__), 'disks.yaml')

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('--data-file', default=DEFAULT_DATA_FILE)
	parser.add_argument('-f', '--file', help="Use S.M.A.R.T. report from file instead of calling smartctl (Use - to read from stdin)")

	args = parser.parse_args()

	stream = None
	if args.file:
		if args.file == '-':
			stream = sys.stdin
		else:
			stream = open(args.file, 'r')

	check = SMARTCheck(stream, args.data_file)

	import pprint
	print(check.information)
	#print(check.device_model, check.exists_in_database())
	#print(check.check())
	print(check.check_tests())

	#pprint.pprint(check.smart_data)
	#pprint.pprint(check.self_tests)

	#if not check.check_attributes():
	#	import sys
	#	sys.exit(1)