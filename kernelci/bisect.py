#!/usr/bin/env python3
#
# Copyright (C) 2021 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import re
import subprocess

from kernelci import shell_cmd

RE_ADDR = r'.*@.*\.[a-z]+'
RE_TRAILER = re.compile(r'^(?P<tag>[A-Z][a-z-]*)\: (?P<value>.*)$')
RE_EMAIL = re.compile(r'^(?P<name>.*)(?P<email><{}>)'.format(RE_ADDR))
RE_MAILING_LIST = re.compile(r'^(?P<email>{}) \('.format(RE_ADDR))


def _git_show_fmt(kdir, revision, fmt):
    show = shell_cmd("""
set -e
cd {kdir}
git show {revision} -s --pretty=format:'{fmt}'
""".format(kdir=kdir, revision=revision, fmt=fmt))
    show.strip()
    return show


def _name_address(data):
    name, address = (data.get(k, '').strip() for k in ['name', 'email'])
    if name:
        address = ' '.join([name, address])
    return address


def _git_maintainers(kdir, revision):
    maintainers = set()
    p = subprocess.Popen(
        "cd {}; git show {} --pretty=format:%b".format(kdir, revision),
        shell=True, stdout=subprocess.PIPE)
    body = p.communicate()[0]
    p = subprocess.Popen(
        "cd {}; ./scripts/get_maintainer.pl --nogit".format(kdir),
        shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    raw = p.communicate(input=body)[0].decode()
    for ln in raw.split('\n'):
        m = RE_EMAIL.match(ln) or RE_MAILING_LIST.match(ln)
        if m:
            maintainers.add(_name_address(m.groupdict()))
    return list(maintainers)


def _git_people(kdir, revision):
    people = {
        'maintainers': _git_maintainers(kdir, revision),
        'author': [_git_show_fmt(kdir, revision, '%an <%ae>')],
        'committer': [_git_show_fmt(kdir, revision, '%cn <%ce>')],
        'Acked-by': [],
        'Reported-by': [],
        'Reviewed-by': [],
        'Signed-off-by': [],
        'Tested-by': [],
    }
    body = _git_show_fmt(kdir, revision, '%b')

    for ln in body.split('\n'):
        m = RE_TRAILER.match(ln)
        if m:
            md = m.groupdict()
            tag, value = (md[k] for k in ['tag', 'value'])
            if tag in people:
                e = RE_EMAIL.match(value)
                if e:
                    people[tag].append(_name_address(e.groupdict()))

    return people


def get_recipients(kdir, commit, to=set(), cc=set()):
    """Create list of recipients for a bisection report

    Automatically gather all the recipients for a bisection email report using
    the get_maintainers.pl script as well as trailers and meta-data from the
    commit found.

    *kdir* is the path to a kernel source directory
    *commit* is the Git commit checksum from the bisection result
    *to* is a set with extra recipients to be added as To:
    *cc* is a set with extra recipients to be added as Cc:
    """
    recipients_map = {
        'author': to,
        'committer': cc,
        'maintainers': cc,
        'Acked-by': to,
        'Reported-by': to,
        'Reviewed-by': to,
        'Signed-off-by': to,
        'Tested-by': to,
    }
    people = _git_people(kdir, commit)

    for category, entries in people.items():
        recip = recipients_map[category]
        for e in entries:
            recip.add(e)

    cc = cc.difference(to)

    return {'to': list(to), 'cc': list(cc)}
