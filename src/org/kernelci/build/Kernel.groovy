/*
  Copyright (C) 2018 Collabora Limited
  Author: Guillaume Tucker <guillaume.tucker@collabora.com>

  This module is free software; you can redistribute it and/or modify it under
  the terms of the GNU Lesser General Public License as published by the Free
  Software Foundation; either version 2.1 of the License, or (at your option)
  any later version.

  This library is distributed in the hope that it will be useful, but WITHOUT
  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
  FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
  details.

  You should have received a copy of the GNU Lesser General Public License
  along with this library; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
*/


package org.kernelci.build;

def cloneKCIBuild(path, url, branch) {
    sh(script: "rm -rf ${path}")
    dir("${path}") {
        git(url: url,
            branch: branch,
            poll: false)
    }
}

def downloadTarball(kdir, url, filename="linux-src.tar.gz") {
    sh(script: "rm -rf ${kdir}")
    dir(kdir) {
        sh(script: "\
wget \
--no-hsts \
--progress=dot:giga \
--retry-connrefused \
--waitretry=5 \
--read-timeout=20 \
--timeout=15 \
--tries 20 \
--continue \
${url}")
        sh(script: "tar xzf ${filename}")
    }
}
