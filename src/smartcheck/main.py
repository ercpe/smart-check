# -*- coding: utf-8 -*-
from argparse import ArgumentParser
import os
from smartcheck.check import SMARTCheck

DEFAULT_DATA_FILE=os.path.join(os.path.dirname(__file__), 'disks.json')

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('--data-file', default=DEFAULT_DATA_FILE)
	parser.add_argument('-f', '--file', help="Use S.M.A.R.T. report from file instead of calling smartctl")

	args = parser.parse_args()

	check = SMARTCheck(open(args.file, 'r'))

	import pprint
	#pprint.pprint(check.information)
	pprint.pprint(check.smart_data)
	#pprint.pprint(check.self_tests)