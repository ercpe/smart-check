# -*- coding: utf-8 -*-
import unittest
import os
from smartcheck.check import SMARTCheck, AttributeWarning, parse_range_specifier

samples_path = os.path.join(os.path.dirname(__file__), 'samples')
db_path = os.path.join(samples_path, '../../smartcheck/disks.yaml')

class CheckTest(unittest.TestCase):

    def test_check_broken1(self):
        with open(os.path.join(samples_path, 'seagate-barracuda-broken1.txt')) as f:
            check = SMARTCheck(f)
            self.assertFalse(check.check_tests())
            self.assertEqual(check.ata_error_count, 8)
            self.assertFalse(check.check())

    def test_check_broken2(self):
        with open(os.path.join(samples_path, 'seagate-barracuda-broken2.txt')) as f:
            check = SMARTCheck(f)
            self.assertFalse(check.check_tests())
            self.assertEqual(check.ata_error_count, 52)
            self.assertFalse(check.check())

    def test_check_broken3(self):
        with open(os.path.join(samples_path, 'WDC-WD1000FYPS-01ZKB0.txt')) as f:
            check = SMARTCheck(f)
            self.assertTrue(check.check_tests())  # no test ran
            self.assertEqual(check.ata_error_count, 32)
            self.assertFalse(check.check())

    def test_smart_attributes_not_found(self):
        with open(os.path.join(samples_path, 'ST2000NM0033-9ZM175.txt')) as f:
            check = SMARTCheck(f, db_path)
            self.assertTrue(check.check_tests())
            self.assertDictEqual(check.check_attributes(), {})  # Attributes not found in disks.json
            self.assertEqual(check.ata_error_count, 0)
            self.assertTrue(check.check())

    def test_smart_attributes_nothing_wrong(self):
        with open(os.path.join(samples_path, 'WDC-WD2000FYYZ-01UL1B1.txt')) as f:
            check = SMARTCheck(f, db_path)
            self.assertTrue(check.check_tests())
            self.assertDictEqual(check.check_attributes(), {})
            self.assertEqual(check.ata_error_count, 0)
            self.assertTrue(check.check())

    def test_smart_attributes_min_max(self):
        # from list
        with open(os.path.join(samples_path, 'ST2000NM0033-9ZM175.txt')) as f:
            check = SMARTCheck(f, os.path.join(samples_path, 'disks-min-max.yaml'))
            self.assertTrue(check.check_tests())
            self.assertDictEqual(check.check_attributes(), {
                (9, 'Power_On_Hours'): AttributeWarning(AttributeWarning.Critical, 'Power_On_Hours', 16998)
            })
            self.assertEqual(check.ata_error_count, 0)
            self.assertFalse(check.check())

        # from dict
        with open(os.path.join(samples_path, 'ST2000NM0033-9ZM175.txt')) as f:
            check = SMARTCheck(f, os.path.join(samples_path, 'disks-min-or-max.yaml'))
            self.assertTrue(check.check_tests())
            self.assertDictEqual(check.check_attributes(), {
                (9, 'Power_On_Hours'): AttributeWarning(AttributeWarning.Critical, 'Power_On_Hours', 16998),
                (194, 'Temperature_Celsius'): AttributeWarning(AttributeWarning.Critical, 'Temperature_Celsius', 30)
            })
            self.assertEqual(check.ata_error_count, 0)
            self.assertFalse(check.check())

    def test_smart_attributes_thresholds_min(self):
        for sample_file, expected_attributes in [
            # only warning
            ('disks-thresholds.yaml', {
                (9, 'Power_On_Hours'): AttributeWarning(AttributeWarning.Warning, 'Power_On_Hours', 15360)
            }),
            # warning and critical - critical wins
            ('disks-thresholds-warn-and-crit.yaml', {
                (9, 'Power_On_Hours'): AttributeWarning(AttributeWarning.Critical, 'Power_On_Hours', 15360)
            }),
            # warning threshold with range
            ('disks-thresholds-range.yaml', {
                (4, 'Start_Stop_Count'): AttributeWarning(AttributeWarning.Warning, 'Start_Stop_Count', 2)
            })
        ]:
            with open(os.path.join(samples_path, 'WDC-WD2000FYYZ-01UL1B1.txt')) as f:
                check = SMARTCheck(f, os.path.join(samples_path, sample_file))
                self.assertTrue(check.check_tests())
                self.assertDictEqual(check.check_attributes(), expected_attributes)
                self.assertFalse(check.check())

    def test_generic_attributes(self):
        base = """=== START OF INFORMATION SECTION ===
Model Family:     Seagate Barracuda 7200.14 (AF)
Device Model:     ST3000DM001-1CH167
Serial Number:    Z1F220RJ

=== START OF READ SMART DATA SECTION ===
SMART Attributes Data Structure revision number: 1
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
"""
        for attr_id, attr_name in [
            ('5', "Reallocated_Sector_Ct"),
            ('197', "current_pending_sector"),
            ('197', "current_pending_sector_count"),
            ('197', "total_pending_sectors"),
            ('0', 'spin_up_retry_count'),
            ('0', 'soft_read_error_rate'),
            ('0', 'Reallocation_Event_Count'),
            ('0', 'ssd_life_left'),
        ]:
            s = base + "%s %s 0x000f   001   000   000    Pre-fail  Always       -       1" % (
                attr_id.rjust(3), attr_name.ljust(23)
            )
            check = SMARTCheck(s, db_path)
            failed_attributes = check.check_generic_attributes()
            assert len(failed_attributes) == 1
            (failed_id, failed_name), warning = list(failed_attributes.items())[0]
            assert int(failed_id) == int(attr_id)
            assert warning.level == AttributeWarning.Notice
            assert warning.value == 1
            self.assertTrue(check.check_tests())
            self.assertFalse(check.check())

    def test_generic_temperature_attribute(self):
        base = """=== START OF INFORMATION SECTION ===
Model Family:     Seagate Barracuda 7200.14 (AF)
Device Model:     ST3000DM001-1CH167
Serial Number:    Z1F220RJ

=== START OF READ SMART DATA SECTION ===
SMART Attributes Data Structure revision number: 1
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
"""
        for attr_id, attr_name, attr_value, notice_expected in [
            ('0', 'temperature_celsius', 1, False), # too low
            ('0', 'temperature_celsius', 51, True), # within range
            ('0', 'temperature_celsius', 130, False), # out of range
            ('0', 'temperature_celsius_x10', 1, False), # too low
            ('0', 'temperature_celsius_x10', 501, True), # within range
        ]:
            s = base + "%s %s 0x000f   %s   000   000    Pre-fail  Always       -       %s" % (
                attr_id.rjust(3), attr_name.ljust(23), str(attr_value).zfill(3), attr_value
            )
            check = SMARTCheck(s, db_path)
            failed_attributes = check.check_generic_attributes()
            if notice_expected:
                assert len(failed_attributes) == 1
                (failed_id, failed_name), warning = list(failed_attributes.items())[0]
                assert int(failed_id) == int(attr_id)
                assert warning.level == AttributeWarning.Notice
                assert warning.value == attr_value
                self.assertFalse(check.check())
            else:
                assert len(failed_attributes) == 0
            self.assertTrue(check.check_tests())

    def test_ignore_attributes(self):
        with open(os.path.join(samples_path, 'seagate-barracuda-broken1.txt')) as f:
            check = SMARTCheck(f)

            for ignore_value in (198, '198', 'Offline_Uncorrectable'):
                failed_attributes = check.check_attributes(ignore_attributes=[ignore_value])
                assert len(failed_attributes) == 1
                (failed_id, failed_name), failed_attribute = list(failed_attributes.items())[0]
                assert failed_id == 197
                assert failed_name == "Current_Pending_Sector"
                assert int(failed_attribute.value) == 24

    def test_notice_warnings(self):
        with open(os.path.join(samples_path, 'hitachi-HDS723020BLA642.txt')) as f:
            check = SMARTCheck(f)
            
            self.assertFalse(check.check())
            
            failed = check.check_attributes()
            
            self.assertEqual(len(failed), 1)
            self.assertEqual(failed, {
                (5, 'Reallocated_Sector_Ct'): AttributeWarning(AttributeWarning.Notice, 'Reallocated_Sector_Ct', 84)
            })

    def test_parse_range_specifier(self):
        # greater than
        f = parse_range_specifier(1)
        assert f(1) is False
        assert f(2)

        # greater than
        f = parse_range_specifier('1')
        assert f(1) is False
        assert f(2)

        # greater than
        f = parse_range_specifier('1:')
        assert f(1) is False
        assert f(2)

        # less than
        f = parse_range_specifier(':2')
        assert f(-11)
        assert f(1)
        assert f(2) is False

        # range 'from:to' - including both ends as valid values
        f = parse_range_specifier('1:2')
        assert f(-1) is False
        assert f(0) is False
        assert f(1)
        assert f(2)
        assert f(3) is False

        # invalid
        f = parse_range_specifier('test')
        assert f(0) is False
        assert f(1) is False
        assert f(2) is False

