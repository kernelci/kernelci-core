#!/usr/env/bin python3

import json
import os
import subprocess
import sys

MANIFEST="/scratch/root/build_info.json"
TEST_SUITE_INFO="/scratch/root/test_suites.json"


def main(args):
    date = subprocess.check_output("date -u", shell=True).decode().strip()
    with open('/scratch/root/etc/debian_version') as f:
        distro_version = f.read().strip()

    build_info = {
        'date': date,
        'distro': 'debian',
        'distro_version': distro_version,
    }

    if os.path.exists(TEST_SUITE_INFO):
        with open(TEST_SUITE_INFO) as f:
            test_suite_info = json.load(f)
            build_info.update(test_suite_info)

    with open(MANIFEST, 'w') as manifest:
        json.dump(build_info, manifest, indent=4)


if __name__ == '__main__':
    main(sys.argv)
