# -*- coding: utf-8 -*-
import os
import unittest
from smartcheck.check import SMARTCheck


class InformationBlockParsingTest(unittest.TestCase):

	def test_parsing(self):
		samples_path = os.path.dirname(__file__)
		for filename, expected_data in [
			('samples/seagate-barracuda-broken1.txt', {
				'ata_version': 'ATA8-ACS T13/1699-D revision 4',
				'device_model': 'ST3000DM001-1CH166',
				'model_family': 'Seagate Barracuda 7200.14 (AF)',
				'sata_version': 'SATA 3.0, 6.0 Gb/s (current: 6.0 Gb/s)',
				'serial': 'Z1F220RJ'
				}),
			('samples/seagate-barracuda-broken2.txt', {
				'ata_version': 'ATA8-ACS T13/1699-D revision 4',
				'device_model': 'ST3000DM001-1CH166',
				'model_family': 'Seagate Barracuda 7200.14 (AF)',
				'sata_version': 'SATA 3.0, 6.0 Gb/s (current: 6.0 Gb/s)',
				'serial': 'Z1F23HW0'
				}),
			]:

			check = SMARTCheck(open(os.path.join(samples_path, filename)))
			self.assertDictEqual(check.information, expected_data)


class SMARTDataParsingTest(unittest.TestCase):
	def test_parsing(self):
		samples_path = os.path.dirname(__file__)
		for filename, overall_health, attributes in [
			('samples/seagate-barracuda-broken1.txt', 'PASSED', [
				('1', 'Raw_Read_Error_Rate', '0x000f', '103', '099', '006', 'Pre-fail', 'Always', '-', '5845168'),
				('3', 'Spin_Up_Time', '0x0003', '095', '095', '000', 'Pre-fail', 'Always', '-', '0'),
				('4', 'Start_Stop_Count', '0x0032', '100', '100', '020', 'Old_age', 'Always', '-', '7'),
				('5', 'Reallocated_Sector_Ct', '0x0033', '100', '100', '010', 'Pre-fail', 'Always', '-', '0'),
				('7', 'Seek_Error_Rate', '0x000f', '087', '055', '030', 'Pre-fail', 'Always', '-', '643382224'),
				('9', 'Power_On_Hours', '0x0032', '074', '074', '000', 'Old_age', 'Always', '-', '23115'),
				('10', 'Spin_Retry_Count', '0x0013', '100', '100', '097', 'Pre-fail', 'Always', '-', '0'),
				('12', 'Power_Cycle_Count', '0x0032', '100', '100', '020', 'Old_age', 'Always', '-', '7'),
				('183', 'Runtime_Bad_Block', '0x0032', '100', '100', '000', 'Old_age', 'Always', '-', '0'),
				('184', 'End-to-End_Error', '0x0032', '100', '100', '099', 'Old_age', 'Always', '-', '0'),
				('187', 'Reported_Uncorrect', '0x0032', '092', '092', '000', 'Old_age', 'Always', '-', '8'),
				('188', 'Command_Timeout', '0x0032', '100', '100', '000', 'Old_age', 'Always', '-', '0 0 0'),
				('189', 'High_Fly_Writes', '0x003a', '100', '100', '000', 'Old_age', 'Always', '-', '0'),
				('190', 'Airflow_Temperature_Cel', '0x0022', '071', '064', '045', 'Old_age', 'Always', '-', '29 (Min/Max 24/32)'),
				('191', 'G-Sense_Error_Rate', '0x0032', '100', '100', '000', 'Old_age', 'Always', '-', '0'),
				('192', 'Power-Off_Retract_Count', '0x0032', '100', '100', '000', 'Old_age', 'Always', '-', '5'),
				('193', 'Load_Cycle_Count', '0x0032', '100', '100', '000', 'Old_age', 'Always', '-', '1574'),
				('194', 'Temperature_Celsius', '0x0022', '029', '040', '000', 'Old_age', 'Always', '-', '29 (0 22 0 0 0)'),
				('197', 'Current_Pending_Sector', '0x0012', '100', '100', '000', 'Old_age', 'Always', '-', '24'),
				('198', 'Offline_Uncorrectable', '0x0010', '100', '100', '000', 'Old_age', 'Offline', '-', '24'),
				('199', 'UDMA_CRC_Error_Count', '0x003e', '200', '200', '000', 'Old_age', 'Always', '-', '0'),
				('240', 'Head_Flying_Hours', '0x0000', '100', '253', '000', 'Old_age', 'Offline', '-', '23044h+44m+28.078s'),
				('241', 'Total_LBAs_Written', '0x0000', '100', '253', '000', 'Old_age', 'Offline', '-', '161370349869'),
				('242', 'Total_LBAs_Read', '0x0000', '100', '253', '000', 'Old_age', 'Offline', '-', '78560290534'),
			])
		]:
			check = SMARTCheck(open(os.path.join(samples_path, filename)))
			self.assertEqual(check.smart_data['overall_health_status'], overall_health)
			self.assertEqual(check.smart_data['attributes'], attributes)


class SelfTestParsingTest(unittest.TestCase):

	def test_parsing(self):
		samples_path = os.path.dirname(__file__)
		for filename, tests in [
			('samples/seagate-barracuda-broken1.txt', [
				('1', 'Extended offline', 'Completed: read failure', '80%', '23113', '1737376544'),
				('2', 'Extended offline', 'Completed: read failure', '80%', '23000', '1737376544'),
				('3', 'Extended offline', 'Interrupted (host reset)', '80%', '22998', '-'),
				('4', 'Extended offline', 'Completed without error', '00%', '5', '-'),
			])
		]:
			check = SMARTCheck(open(os.path.join(samples_path, filename)))
			self.assertEqual(check.self_tests['test_results'], tests)
