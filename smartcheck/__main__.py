#!/usr/bin/env python
# -*- coding: utf-8 -*-
from argparse import ArgumentParser
import shlex
import sys
import logging
import subprocess

from smartcheck import VERSION
from smartcheck.check import SMARTCheck, AttributeWarning, DEFAULT_DISKS_FILE


def execute_smartctl(drive, interface=None, sudo=None, smartctl_path=None, smartctl_args=''):
    command_line = "%s %s %s %s -a %s" % (
        "sudo" if sudo else '',
        smartctl_path,
        '-d %s' % interface if interface else '',
        smartctl_args,
        drive
    )
    logging.debug("Executing smartctl command: %s" % command_line)

    cmd = shlex.split(command_line)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={'LC_ALL': 'C'})
    output = process.communicate()[0]
    # TODO: See if we can get hints from the smartctl exit codes:
    # https://www.freebsd.org/cgi/man.cgi?query=smartctl&manpath=FreeBSD+9.0-RELEASE+and+Ports&format=html#RETURN_VALUES
    # at least we should not handle if the drive is in low-power mode (spindown)
#    if process.returncode:
#        raise Exception("smartctl failed with status code %s" % process.returncode)
    return output

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument('--disks-file', default=DEFAULT_DISKS_FILE)

    parser.add_argument('-s', '--sudo', help="Use sudo to execute smartctl", action='store_true', default=False)

    parser.add_argument('--smartctl-path', default="/usr/sbin/smartctl", help='Path to smartctl (default: %(default)s)')
    parser.add_argument('-a', '--smartctl-args', default='-n standby', help="Other arguments passed to smartctl (default: %(default)s)")

    parser.add_argument('-i', '--interface', help="The smartctl interface specification (passed to smartctl's -d parameter")
    parser.add_argument('drive', type=str, nargs='?', help="The device as passed to smartctl's positional argument")
    parser.add_argument('-f', '--file', help="Use S.M.A.R.T. report from file instead of calling smartctl (Use - to read from stdin)")

    parser.add_argument('-x', '--exclude-notices', help='Do not report NOTICE warnings (default: %(default)s)', action='store_true', default=False)
    parser.add_argument('--ignore-attributes', help='Ignore this S.M.A.R.T. attributes (id or name)', nargs='*')
    parser.add_argument('-v', '--verbose', help='Verbose messages', action='store_true', default=False)
    parser.add_argument('--debug', help="Print debug messages", action="store_true", default=False)
    parser.add_argument('--version', action='store_true', dest='version', help='show version and exit')

    args = parser.parse_args()

    if args.version:
        print("smart-check %s" % VERSION)
        sys.exit(0)

    if args.file and any([args.interface, args.drive]):
        parser.error('-f/--file cannot be used with a device and/or -i/--interface')

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

    exit_code = 0
    msg = ""
    try:
        stream = None
        if args.file:
            if args.file == '-':
                stream = sys.stdin
            else:
                stream = open(args.file, 'r')
        else:
            stream = execute_smartctl(args.drive, args.interface, args.sudo, args.smartctl_path, args.smartctl_args)

        check = SMARTCheck(stream, args.disks_file)

        if check.data_parsed:
            attribute_errors = check.check_attributes()

            if args.exclude_notices:
                for k in [x for x, y in attribute_errors.items() if y.level == AttributeWarning.Notice]:
                    del attribute_errors[k]

            if attribute_errors:
                msg = ', '.join([ae.long_message if args.verbose else ae.short_message for ae in attribute_errors.values()])

                if any((ae.level == AttributeWarning.Warning for ae in attribute_errors.values())):
                    exit_code = 1
                if any((ae.level == AttributeWarning.Critical for ae in attribute_errors.values())):
                    exit_code = 2

            if not check.check_tests():
                msg = (msg.strip() + '; S.M.A.R.T. self test reported an error').lstrip(';').strip()
                exit_code = 2

            if check.ata_error_count:
                msg = (msg.strip() + '; %s ATA errors found' % check.ata_error_count).lstrip(';').strip()
                exit_code = 2

            if not exit_code:
                msg = "S.M.A.R.T. data OK"

            msg = "%s: %s" % (check.device_model, msg)
        else:
            msg = "Could not read S.M.A.R.T. data (executed as root?)"
            exit_code = 3
    except Exception as ex:
        msg = "Plugin failed: %s" % ex
        if args.debug:
            logging.exception("Plugin failed")
        exit_code = 3

    print(msg)
    sys.exit(exit_code)
