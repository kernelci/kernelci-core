# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2020-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Python package setup"""

import fnmatch
import os
import setuptools
import kernelci


def _list_files(path, match):
    all_files = []
    for root, _, files in os.walk(path):
        dir_files = []
        for fname in fnmatch.filter(files, match):
            dir_files.append(os.path.join(root, fname))
        all_files.append((root, dir_files))
    return all_files


def _load_readme():
    with open('README.md', 'rb') as readme:
        return readme.read().decode('utf8')


setuptools.setup(
    name='kernelci',
    version=kernelci.__version__,
    description="KernelCI core functions",
    author="kernelci.org",
    author_email="kernelci@groups.io",
    url="https://github.com/kernelci/kernelci-core",
    packages=[
        "kernelci",
        "kernelci.api",
        "kernelci.cli",
        "kernelci.config",
        "kernelci.db",
        "kernelci.legacy",
        "kernelci.legacy.cli",
        "kernelci.legacy.config",
        "kernelci.legacy.lava",
        "kernelci.runtime",
        "kernelci.runtime.legacy",
        "kernelci.storage",
    ],
    scripts=[
        'kci',
        'kci_build',
        'kci_test',
        'kci_rootfs',
        'kci_data',
        'kci_bisect',
        'scripts/kci-bisect-lava-v2-callback',
        'scripts/kci-bisect-push-results',
    ],
    long_description=_load_readme(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',  # noqa pylint: disable=line-too-long
        'Operating System :: OS Independent',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: C',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Testing',
    ],
    python_requires='>=3.8',
    install_requires=[
        "cloudevents",
        "jinja2",
        "kubernetes",
        "paramiko",
        "pyelftools",
        "pytest",
        "pyyaml",
        "requests",
        "scp",
    ],
    extras_require={
        'dev': [
            'pycodestyle',
            'pylint',
        ]
    }
)
