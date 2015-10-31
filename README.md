# What is smart-check?

After several undetected silent hard drive failures i looked (once again) for a working Nagios/Icinga plugin. There are many, many plugins which claim to be able to detect early signs of failing hard drives. Most of them just don't.

The few which actually do more than just checking for the temperature or some bogus attributes fall short on some other aspects, so i decided to add just another plugin to world which tries to solve this problem.


# Basic usage

    usage: smart-check [-h] [--disks-file DISKS_FILE] [-s]
                       [--smartctl-path SMARTCTL_PATH] [-a SMARTCTL_ARGS]
                       [-i INTERFACE] [-f FILE] [-x]
                       [--ignore-attributes [IGNORE_ATTRIBUTES [IGNORE_ATTRIBUTES ...]]]
                       [-v] [--debug]
                       [drive]
    
    positional arguments:
      drive                 The device as passed to smartctl's positional argument
    
    optional arguments:
      -h, --help            show this help message and exit
      --disks-file DISKS_FILE
      -s, --sudo            Use sudo to execute smartctl
      --smartctl-path SMARTCTL_PATH
                            Path to smartctl (default: /usr/sbin/smartctl)
      -a SMARTCTL_ARGS, --smartctl-args SMARTCTL_ARGS
                            Other arguments passed to smartctl (default: -n
                            standby)
      -i INTERFACE, --interface INTERFACE
                            The smartctl interface specification (passed to
                            smartctl's -d parameter
      -f FILE, --file FILE  Use S.M.A.R.T. report from file instead of calling
                            smartctl (Use - to read from stdin)
      -x, --exclude-notices
                            Do not report NOTICE warnings (default: False)
      --ignore-attributes [IGNORE_ATTRIBUTES [IGNORE_ATTRIBUTES ...]]
                            Ignore this S.M.A.R.T. attributes (id or name)
      -v, --verbose         Verbose messages
      --debug               Print debug messages



The basic usage is 

    smart-check <device>

e.g.

    root@host# smart-check /dev/sda

If your devices are behind a raid controller, pass `smartctl`'s `--device` argument via the `-i/--interface` parameter:

    root@host# smart-check -i areca,1 /dev/sg13



# Attributes and thresholds

`smart-check` checks for several well-known S.M.A.R.T. attributes to predict signs a hardware failure. Note: This code is taken from [gsmartcontrol](http://gsmartcontrol.sourceforge.net/).
It checks that the following attributes have a non-zero value for  `VALUE`/`RAW_VALUE` and emits a NOTICE.

* `reallocated_sector_count` / `reallocated_sector_ct`
* `spin_up_retry_count`
* `soft_read_error_rate`
* `temperature_celsius` / `temperature_celsius_x10`
* `reallocation_event_count`
* `current_pending_sector` / `current_pending_sector_count` / `total_pending_sectors`
* `offline_uncorrectable` / `total_offline_uncorrectable`
* `ssd_life_left`

`smart-check` also contains a disk database (taken from [check_smart_attributes](https://github.com/thomas-krenn/check_smart_attributes)) which can be used to specify more fine-grained thresholds for specific hard drive device models.


If you want to ignore certain attributes (e.g. because your hard drive reports bogus values) pass the `--ignore-attributes` parameter to `smart-check`, e.g.:

    smart-check --ignore-attributes Temperature_Celcius /dev/sda
    
