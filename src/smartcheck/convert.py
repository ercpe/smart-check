# -*- coding: utf-8 -*-

import yaml
import json
import sys
import re

s = open(sys.argv[1]).read() #[:2100]

s = re.sub(r':\s+("[\w\d\_]+")(,?) #\s*(.*)', r': [\1, "\3"]\2', s, flags=re.MULTILINE)
#s = re.sub('(?:,)([\r\n\s]*)', '\2', s, flags=re.MULTILINE)

s = re.sub(r'(\]),([\r\n\s]*})', r'\1\2', s, flags=re.MULTILINE)

#print(s)

d = json.loads(s)
#import pprint
#pprint.pprint(d)

for group_name, device in sorted(d['Devices'].items(), key=lambda x: x[1]['Device'][0]):
	print("")
	if len(device['Device']) > 1:
		print("- model:")
		print('\n'.join('  - "%s"' % x for x in device['Device']))
	else:
		print('- model: "%s"' % device['Device'][0])

	attribs = device['ID#']
	if attribs:
		thresholds = device['Threshs']

		print("  attributes:")
		for attribute_id, (field, description) in sorted(attribs.items(), key=lambda x: int(x[0])):
			attrib_thresholds = thresholds.get(str(attribute_id), None)
			if attrib_thresholds:
				thresh1, thresh2 = tuple(attrib_thresholds)
				if ':' in thresh1 and ':' in thresh2:

					def fix_threshold(s):
						if s.endswith(':'):
							return ":%s" % s[:-1]
						elif s.startswith(":"):
							return "%s:" % s[1:]
						else:
							return s

					print("    %s: # %s" % (int(attribute_id), description))
					if field != 'RAW_VALUE':
						print('      field: "%s"' % field)
					print('      warn_threshold: "%s"' % fix_threshold(thresh1))
					print('      crit_threshold: "%s"' % fix_threshold(thresh2))
				else:
					if 'WDC WD2000FYYZ-01UL1B0' in device['Device']:
						thresh1 = 0
					print('    %s: ["%s", %s, %s] # %s' % (int(attribute_id), field, thresh1, thresh2, description))
