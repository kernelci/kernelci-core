#!/usr/env/bin python3

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET


def main(args):
    manifest_git_cmd = "git -C .repo/manifests log --oneline -1"
    tree = ET.parse('.repo/manifest.xml')
    root = tree.getroot()
    xml_file = root[0].get('name')
    manifest_fname = os.path.join(args[1], 'manifest.json')
    date = subprocess.check_output("date -u", shell=True).decode().strip()
    distro_version = os.readlink(f'src/build/images/{args[0]}/latest')
    manifest_git = subprocess.check_output(manifest_git_cmd,
                                           shell=True).decode().strip()

    build_info = {
        'date': date,
        'distro': 'ChromiumOS',
        'distro_version': distro_version,
        'manifest_git': manifest_git,
        'manifest_file': xml_file,
    }

    with open(manifest_fname, 'w') as manifest:
        json.dump(build_info, manifest, indent=4)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1:])
    else:
        print("Board name and destination directory required")
        sys.exit(1)
