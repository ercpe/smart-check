# -*- coding: utf-8 -*-
import logging

import sys
import yaml
import re
import os

logger = logging.getLogger(__name__)

DEFAULT_DISKS_FILE=os.path.join(os.path.dirname(__file__), 'disks.yaml')
GENERIC_ATTRS_FILE=os.path.join(os.path.dirname(__file__), 'generic.yaml')

INFORMATION_SECTION_START = '=== START OF INFORMATION SECTION ==='
DATA_SECTION_START = '=== START OF READ SMART DATA SECTION ==='
TESTS_SECTION_START = 'SMART Self-test log structure revision number'
ATA_ERROR_COUNT = re.compile('^ATA Error Count: (\d+).*', re.MULTILINE | re.IGNORECASE)

INFORMATION_RE = [
    ("model_family", re.compile('Model Family: (.*)', re.UNICODE)),
    ("device_model", re.compile("(?:Device Model|Product): (.*)", re.UNICODE)),
    ("serial", re.compile("Serial Number: (.*)", re.UNICODE | re.IGNORECASE)),
    ("firmware_version", re.compile("Firmware version: (.*)", re.UNICODE)),
    ("ata_version", re.compile("ATA Version is: (.*)", re.UNICODE)),
    ("sata_version", re.compile("SATA Version is: (.*)", re.UNICODE)),
]

DATA_RE = [
    ('overall_health_status', re.compile('SMART overall-health self-assessment test result: (.*)', re.UNICODE)),
]
DATA_ATTRIBUTES_RE = re.compile(r"\s*(\d+)\s+([\w\d_\-]+)\s+([0-9a-fx]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\w\d_\-]+)\s+([\w\d]+)\s+([\w\d_\-]+)\s+([^\r\n]*)", re.UNICODE)

TEST_RESULT_RE = re.compile(r"#\s*(\d+)\s+(.*?)\s{2,}(.*?)\s{2,}\s+([\d%]+)\s+(\d+)\s+(\d+|-)", re.UNICODE)


def toint(s, default=0):
    try:
        return int(s)
    except ValueError:
        return default


def parse_range_specifier(s):
    # should be functional equivalent to the next one
    if isinstance(s, int):
        return lambda x: x > s

    # either '10' or '10:'
    if re.match("^[0-9]+$", s) or re.match("^[0-9]+:$", s):
        return lambda x: x > int(s.rstrip(':'))
    
    # ':10'
    if re.match("^:[0-9]+$", s):
        return lambda x: x < int(s.lstrip(':'))

    from_to = re.match("^([0-9]+):([0-9]+)$", s, re.IGNORECASE)
    if from_to:
        return lambda x: int(from_to.group(1)) <= x <= int(from_to.group(2))
    
    logger.error("Couldn't parse '%s' - it will be ignored")
    return lambda x: False


class AttributeWarning(object):
    Notice = 'NOTICE'
    Warning = 'WARNING'
    Critical = 'CRITICAL'

    def __init__(self, level=None, attribute_name=None, value=None, description=None):
        self.level = level
        self.field = attribute_name
        self.value = value
        self.description = (description or '').strip()

    @property
    def short_message(self):
        return "%s: %s=%s" % (self.level or '?', self.field, self.value)

    @property
    def long_message(self):
        s = self.short_message

        if self.description:
            s += ": %s" % self.description

        return s

    def __str__(self):
        return self.short_message

    def __repr__(self):
        return self.short_message

    def __eq__(self, other):
        return isinstance(other, AttributeWarning) and \
                    self.level is not None and self.level == other.level and \
                    self.field is not None and self.field == other.field and \
                    self.value is not None and self.value == other.value


class SMARTCheck(object):

    def __init__(self, file_or_string, db_path=None):
        if hasattr(file_or_string, 'read'):
            self.raw = file_or_string.read()
        elif isinstance(file_or_string, str) or (sys.version_info[0] == 2 and isinstance(file_or_string, unicode)):
            self.raw = file_or_string
        elif isinstance(file_or_string, bytes):
            self.raw = file_or_string.decode('UTF-8')
        else:
            raise Exception("Unknown type: %s" % type(file_or_string))

        self.parsed_sections = None
        self.db_path = db_path
        self._database = None
        self._generic = None

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

    @property
    def database(self):
        if self._database is None:
            if self.db_path:
                with open(self.db_path) as f:
                    self._database = yaml.load(f) or {}
            else:
                self._database = []
        return self._database

    @property
    def generic_attributes_checks(self):
        if self._generic is None:
            try:
                with open(GENERIC_ATTRS_FILE) as f:
                    self._generic = yaml.load(f) or []
            except:
                logger.exception("Could not read %s", GENERIC_ATTRS_FILE)
        return self._generic

    @property
    def device_model(self):
        return self.information['device_model']

    @property
    def ata_error_count(self):
        return self.parsed['ata_error_count']

    def exists_in_database(self):
        return self.get_attributes_from_database(self.device_model) is not None

    def get_attributes_from_database(self, device_model):
        for dev in self.database:
            device_regexprs = dev['model'] if isinstance(dev['model'], list) else [dev['model']]
            if any(re.match(r, device_model, re.IGNORECASE) for r in device_regexprs):
                logger.debug("Device exists in database (one of %s matches %s)", device_regexprs, self.device_model)
                return dev['attributes']
        logger.debug("Device does not exist in database")
        return None

    def parse(self):
        return {
            'information': self.parse_information_section(self.raw),
            'data': self.parse_data_section(self.raw),
            'self_tests': self.parse_tests_section(self.raw),
            'ata_error_count': self.parse_ata_error_count(self.raw),
        }

    @property
    def data_parsed(self):
        return 'attributes' in self.smart_data

    def parse_information_section(self, s):
        if INFORMATION_SECTION_START not in s:
            return {}

        start = s.index(INFORMATION_SECTION_START)

        if DATA_SECTION_START not in s:
            end = len(s)
        else:
            end = s.index(DATA_SECTION_START)

        information_text = s[start:end]

        d = {}
        for k, regex in INFORMATION_RE:
            m = regex.search(information_text)
            if m:
                d[k] = m.group(1).strip() if m.group(1) else ''
        return d

    def parse_data_section(self, s):
        if DATA_SECTION_START not in s:
            logger.info("No data section found")
            return {}

        start = s.index(DATA_SECTION_START)
        data_text = s[start:]

        d = {}
        for k, regex in DATA_RE:
            m = regex.search(data_text)
            if m:
                d[k] = m.group(1).strip() if m.group(1) else ''

        d['attributes'] = sorted(DATA_ATTRIBUTES_RE.findall(s), key=lambda t: int(t[0]))

        return d

    def parse_tests_section(self, s):
        if TESTS_SECTION_START not in s:
            return {
                'test_results': []
            }

        start = s.index(TESTS_SECTION_START)
        end = re.search(r'(\r\n\r\n|\n\n|\r\r)', s[start+1:], re.MULTILINE)
        end = start + end.end(0) if end else len(s)

        tests_text = s[start:end]

        return {
            'test_results': TEST_RESULT_RE.findall(tests_text)
        }

    def parse_ata_error_count(self, s):
        m = ATA_ERROR_COUNT.search(s)
        if m:
            return int(m.group(1))
        return 0

    def check(self, ignore_attributes=None):
        return len(self.check_attributes(ignore_attributes or [])) == 0 and self.check_tests() and self.ata_error_count == 0

    def check_tests(self, latest_only=False):
        ok_test_results = [
            'Completed without error',
            'Interrupted (host reset)', # reboot during self test
            'Aborted by host'
        ]
        if latest_only and self.self_tests['test_results']:
            return not self.self_tests['test_results'][2] in ok_test_results

        return not any([x[2] not in ok_test_results for x in self.self_tests['test_results']])

    def check_attributes(self, ignore_attributes=None):
        failed_attributes = self.check_generic_attributes()

        if self.exists_in_database():
            failed_attributes.update(self.check_device_attributes())

        # remove every AttributeWarning from failed_attributes based on ignore_attributes
        for attr_id_or_name in ignore_attributes or []:
            del_keys = []
            if isinstance(attr_id_or_name, int) or attr_id_or_name.isdigit():
                del_keys = [k for k in failed_attributes.keys() if k[0] == int(attr_id_or_name)]
            else:
                del_keys = [k for k in failed_attributes.keys() if k[1] == attr_id_or_name]

            for x in del_keys:
                del failed_attributes[x]

        return failed_attributes

    def check_generic_attributes(self):
        failed_attributes = {}

        for attrid, name, flag, value, worst, thresh, attr_type, updated, when_failed, raw_value in self.smart_data['attributes']:
            logger.debug("Attribute %s (%s): value=%s, raw value=%s, worst=%s, thresh=%s", attrid, name, value, raw_value, worst, thresh)

            attrid = int(attrid)
            attr_name = (name or '').lower()
            int_value = toint(value)
            int_raw_value = toint(raw_value)
            int_thresh = toint(thresh)

            for rule in self.generic_attributes_checks:
                if attr_name not in rule.get('attributes', []):
                    continue

                if 'value' in rule:
                    check_value = int_value
                    func = parse_range_specifier(rule['value'])
                elif 'raw_value' in rule:
                    check_value = int_raw_value
                    func = parse_range_specifier(rule['raw_value'])

                if func(check_value):
                    failed_attributes[(attrid, name)] = AttributeWarning(AttributeWarning.Notice, name, check_value, rule['message'])
                    break
            
            if (attrid, name) in failed_attributes:
                # don't check against threshold if one of the generic rules already matched
                continue

            # execute a generic check for value < threshold
            if int_value and int_thresh:
                if int_value < int_thresh:
                    failed_attributes[(attrid, name)] = AttributeWarning(
                                                                AttributeWarning.Warning if attr_type == 'Pre-fail' else AttributeWarning.Notice,
                                                                name,
                                                                raw_value,
                                                                "Attribute value dropped below threshold of %s" % int_thresh)

        logger.debug("Failed generic attributes: %s" % failed_attributes)
        return failed_attributes

    def check_device_attributes(self):
        device_model = self.device_model
        device_db_attributes = self.get_attributes_from_database(device_model)

        threshold_from = re.compile('^(\d+):$')
        threshold_to = re.compile('^:(\d+)$')
        threshold_from_to = re.compile('^(\d+):(\d+)$')

        failed_attributes = {}

        for attrid, name, flag, value, worst, tresh, type, updated, when_failed, raw_value in self.smart_data['attributes']:
            attrid = int(attrid)
            if attrid in device_db_attributes:
                db_attrs = device_db_attributes[attrid]

                if isinstance(db_attrs, list):
                    value_field, min_value, max_value = tuple(device_db_attributes[int(attrid)])

                    check_value = value if value_field == "VALUE" else raw_value
                    check_value = int(check_value or -1)

                    logger.debug("Attribute %s, field: %s, min: %s, max: %s, value: %s, raw_value: %s",
                        attrid, value, min_value, max_value, value, raw_value
                    )

                    if not (int(min_value) <= check_value <= int(max_value)):
                        logger.info("Attribute %s (%s) failed: not %s <= %s <= %s", attrid, name, min_value, check_value, max_value)
                        failed_attributes[(attrid, name)] = AttributeWarning(AttributeWarning.Critical, name, check_value)

                elif isinstance(db_attrs, dict):
                    value_field = db_attrs.get('field', 'RAW_VALUE')
                    check_value = value if value_field == "VALUE" else raw_value
                    check_value = int(check_value or -1)

                    min_value = db_attrs.get('min', None)
                    max_value = db_attrs.get('max', None)

                    if min_value is None and max_value is None:
                        for failure_type, threshold_key in [('WARNING', 'warn_threshold'), ('CRITICAL', 'crit_threshold')]:
                            if threshold_key not in db_attrs:
                                continue
                            v = db_attrs.get(threshold_key)

                            from_m = threshold_from.match(v)
                            to_m = threshold_to.match(v)
                            from_to_m = threshold_from_to.match(v)

                            if (from_m and check_value >= int(from_m.group(1))) or \
                                (to_m and check_value <= int(to_m.group(1))) or \
                                (from_to_m and (int(from_to_m.group(1)) <= check_value <= int(from_to_m.group(2)))):

                                logger.info("Attribute %s (%s) failed with %s: not within treshold %s", attrid, name, failure_type, v)
                                failed_attributes[(attrid, name)] = AttributeWarning(failure_type, name, check_value)
                    else:
                        if (min_value is not None and check_value >= int(min_value)) or \
                            (max_value is not None and check_value <= int(max_value)):
                            logger.info("Attribute %s (%s) failed: not %s >= %s <= %s", attrid, name, min_value, check_value, max_value)
                            failed_attributes[(attrid, name)] = AttributeWarning(AttributeWarning.Critical, name, check_value)

                else:
                    raise ValueError("Unknown attribute specification: %s" % db_attrs)

        return failed_attributes
