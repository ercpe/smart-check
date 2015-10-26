# -*- coding: utf-8 -*-
from StringIO import StringIO

import unittest
import os
from smartcheck.check import SMARTCheck, AttributeWarning

samples_path = os.path.join(os.path.dirname(__file__), 'samples')
db_path = os.path.join(samples_path, '../../src/smartcheck/disks.yaml')

class CheckTest(unittest.TestCase):

	def test_check_broken1(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'seagate-barracuda-broken1.txt')))
		self.assertFalse(check.check_tests())
		self.assertFalse(check.check())

	def test_check_broken2(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'seagate-barracuda-broken2.txt')))
		self.assertFalse(check.check_tests())
		self.assertFalse(check.check())

	def test_smart_attributes_not_found(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'ST2000NM0033-9ZM175.txt')), db_path)
		self.assertTrue(check.check_tests())
		self.assertDictEqual(check.check_attributes(), {})  # Attributes not found in disks.json
		self.assertTrue(check.check())

	def test_smart_attributes_nothing_wrong(self):
		check = SMARTCheck(open(os.path.join(samples_path, 'WDC-WD2000FYYZ-01UL1B1.txt')), db_path)
		self.assertTrue(check.check_tests())
		self.assertDictEqual(check.check_attributes(), {})
		self.assertTrue(check.check())

	def test_smart_attributes_min_max(self):
		# from list
		check = SMARTCheck(open(os.path.join(samples_path, 'ST2000NM0033-9ZM175.txt')),
						   os.path.join(samples_path, 'disks-min-max.yaml'))
		self.assertTrue(check.check_tests())
		self.assertDictEqual(check.check_attributes(), {
			(9, 'Power_On_Hours'): AttributeWarning(AttributeWarning.Critical, 'RAW_VALUE', 16998)
		})
		self.assertFalse(check.check())

		# from dict
		check = SMARTCheck(open(os.path.join(samples_path, 'ST2000NM0033-9ZM175.txt')),
						   os.path.join(samples_path, 'disks-min-or-max.yaml'))
		self.assertTrue(check.check_tests())
		self.assertDictEqual(check.check_attributes(), {
			(9, 'Power_On_Hours'): AttributeWarning(AttributeWarning.Critical, 'RAW_VALUE', 16998),
			(194, 'Temperature_Celsius'): AttributeWarning(AttributeWarning.Critical, 'VALUE', 30)
		})
		self.assertFalse(check.check())

	def test_smart_attributes_thresholds_min(self):
		for sample_file, expected_attributes in [
			# only warning
			('disks-thresholds.yaml', {
				(9, 'Power_On_Hours'): AttributeWarning(AttributeWarning.Warning, 'RAW_VALUE', 15360)
			}),
			# warning and critical - critical wins
			('disks-thresholds-warn-and-crit.yaml', {
				(9, 'Power_On_Hours'): AttributeWarning(AttributeWarning.Critical, 'RAW_VALUE', 15360)
			}),
			# warning threshold with range
			('disks-thresholds-range.yaml', {
				(4, 'Start_Stop_Count'): AttributeWarning(AttributeWarning.Warning, 'RAW_VALUE', 2)
			})
		]:
			check = SMARTCheck(open(os.path.join(samples_path, 'WDC-WD2000FYYZ-01UL1B1.txt')), os.path.join(samples_path, sample_file))
			self.assertTrue(check.check_tests())
			self.assertDictEqual(check.check_attributes(), expected_attributes)
			self.assertFalse(check.check())
