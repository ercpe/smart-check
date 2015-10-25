# -*- coding: utf-8 -*-

import unittest
import os
from smartcheck.check import SMARTCheck

samples_path = os.path.join(os.path.dirname(__file__), 'samples')
db_path = os.path.join(samples_path, '../../src/smartcheck/disks.json')

class CheckTest(unittest.TestCase):

	def test_check_broken1(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'seagate-barracuda-broken1.txt')))
		self.assertFalse(check.check())
		self.assertFalse(check.check_tests())

	def test_check_broken2(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'seagate-barracuda-broken2.txt')))
		self.assertFalse(check.check())
		self.assertFalse(check.check_tests())

	def test_smart_attributes_not_found(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'seagate-barracuda-broken1.txt')), db_path)
		self.assertFalse(check.check())
		self.assertFalse(check.check_tests())
		self.assertDictEqual(check.check_attributes(), {})  # Attributes not found in disks.json

	def test_smart_attributes_nothing_wrong(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'WDC-WD2000FYYZ-01UL1B1.txt')), db_path)
		self.assertTrue(check.check())
		self.assertTrue(check.check_tests())
		self.assertDictEqual(check.check_attributes(), {})

	def test_smart_attributes_min_max(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'WDC-WD2000FYYZ-01UL1B1.txt')),
						   os.path.join(samples_path, 'disks-min-max.json'))
		self.assertFalse(check.check())
		self.assertTrue(check.check_tests())
		self.assertDictEqual(check.check_attributes(), {
			('9', 'Power_On_Hours'): ('RAW_VALUE', 15360)
		})

	def test_smart_attributes_thresholds(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'WDC-WD2000FYYZ-01UL1B1.txt')),
						   os.path.join(samples_path, 'disks-thresholds.json'))
		self.assertFalse(check.check())
		self.assertTrue(check.check_tests())
		self.assertDictEqual(check.check_attributes(), {
			('9', 'Power_On_Hours'): ('RAW_VALUE', 15360)
		})
