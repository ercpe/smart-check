# -*- coding: utf-8 -*-
from argparse import ArgumentParser
import os
from smartcheck.check import SMARTCheck

DEFAULT_DATA_FILE=os.path.join(os.path.dirname(__file__), 'disks.yaml')

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('--data-file', default=DEFAULT_DATA_FILE)
	parser.add_argument('-f', '--file', help="Use S.M.A.R.T. report from file instead of calling smartctl")

	args = parser.parse_args()

	check = SMARTCheck(open(args.file, 'r'), args.data_file)

	import pprint
	print(check.check_attributes())
	#if not check.check_attributes():
	#	import sys
	#	sys.exit(1)
	#pprint.pprint(check.smart_data)
	#pprint.pprint(check.self_tests)