# -*- coding: utf-8 -*-

import re

INFORMATION_SECTION_START = '=== START OF INFORMATION SECTION ==='
DATA_SECTION_START = '=== START OF READ SMART DATA SECTION ==='
TESTS_SECTION_START = 'SMART Self-test log structure revision number'

INFORMATION_RE = [
	("model_family", re.compile('Model Family: (.*)', re.UNICODE)),
	("device_model", re.compile("Device Model: (.*)", re.UNICODE)),
	("serial", re.compile("Serial Number: (.*)", re.UNICODE)),
	("firmware_version", re.compile("Firmware version: (.*)", re.UNICODE)),
	("ata_version", re.compile("ATA Version is: (.*)", re.UNICODE)),
	("sata_version", re.compile("SATA Version is: (.*)", re.UNICODE)),
]

DATA_RE = [
	('overall_health_status', re.compile('SMART overall-health self-assessment test result: (.*)', re.UNICODE)),
]
DATA_ATTRIBUTES_RE = re.compile(r"\s*(\d+)\s+([\w\d_\-]+)\s+([0-9a-fx]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\w\d_\-]+)\s+([\w\d]+)\s+([\w\d_\-]+)\s+(.*)", re.UNICODE)

TEST_RESULT_RE = re.compile(r"#\s*(\d+)\s+(.*?)\s{2,}(.*?)\s{2,}\s+([\d%]+)\s+(\d+)\s+(\d+|-)", re.UNICODE)

class SMARTCheck(object):

	def __init__(self, file_or_stream):
		self.raw = file_or_stream.read()
		self.parsed_sections = None

	@property
	def information(self):
		return self.parsed.get('information', {})

	@property
	def smart_data(self):
		return self.parsed.get('data', {})

	@property
	def self_tests(self):
		return self.parsed.get('self_tests', {})

	@property
	def parsed(self):
		if not self.parsed_sections:
			self.parsed_sections = self.parse()
		return self.parsed_sections

	def parse(self):
		return {
			'information': self.parse_information_section(self.raw),
			'data': self.parse_data_section(self.raw),
			'self_tests': self.parse_tests_section(self.raw),
		}

	def parse_information_section(self, s):
		start = s.index(INFORMATION_SECTION_START)
		end = s.index(DATA_SECTION_START)

		if end < 0:
			end = len(s)

		if start < 0:
			return {}

		information_text = s[start:end]

		d = {}
		for k, regex in INFORMATION_RE:
			m = regex.search(information_text)
			if m:
				d[k] = m.group(1).strip() if m.group(1) else ''
		return d

	def parse_data_section(self, s):
		start = s.index(DATA_SECTION_START)
		end = len(s) #s.index(DATA_SECTION_START)

		if end < 0:
			end = len(s)

		if start < 0:
			return {}

		data_text = s[start:end]
		#print(data_text)

		d = {}
		for k, regex in DATA_RE:
			m = regex.search(data_text)
			if m:
				d[k] = m.group(1).strip() if m.group(1) else ''

		d['attributes'] = DATA_ATTRIBUTES_RE.findall(s)

		return d

	def parse_tests_section(self, s):
		start = s.index(TESTS_SECTION_START)
		end = s.index('\n\n', start+1)

		if end < 0:
			end = len(s)

		if start < 0:
			return {}

		tests_text = s[start:end]

		return {
			'test_results': TEST_RESULT_RE.findall(tests_text)
		}


