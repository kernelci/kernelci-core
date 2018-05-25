/*
  Copyright (C) 2018 Collabora Limited
  Author: Ana Guerrero Lopez <ana.guerrero@collabora.com>

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



/* TODO:
- Harcoded paths at jenkins/debian/... for Dockerfile and debos file
*/

def call(Closure context) {

    def config = [:]
    context.resolveStrategy = Closure.DELEGATE_FIRST
    context.delegate = config
    context()

    def name = config.name
    def kernel_arch = config.archList
    def debian_arch =  ["armhf": "armhf",
                        "armel": "armel",
                        "arm64": "arm64",
                        "x86": "i386",
                        "x86_64": "amd64"]

    def debosFile = "jenkins/debian/debos/stretch.yaml"
    // Returns the pipeline version with the format YYYYMMMAA.X where X is the number of the build of the day
    def pipeline_version = VersionNumber(versionNumberString: '${BUILD_DATE_FORMATTED,"yyyyMMdd"}.${BUILDS_TODAY_Z}')

    // debos will always run the extra packages step, so let's make sure it has something to install
    def extraPackages = "bash"
    if (config.extra_packages != null) {
        extraPackages = config.extra_packages
    }

    // defaults to empty script scripts/nothing.sh
    def script = "scripts/nothing.sh"
    if (config.script != null) {
        script = config.script
    }

    def stepsForParallel = [:]
    for (int i = 0; i < kernel_arch.size(); i++) {
        def arch = kernel_arch[i]
        def buildStep = "Build image for ${arch}"
        stepsForParallel[buildStep] = makeImageStep(pipeline_version,
                                                    arch,
                                                    debian_arch[arch],
                                                    debosFile,
                                                    extraPackages,
                                                    name,
                                                    script)
    }

    parallel stepsForParallel
}


def makeImageStep(String pipeline_version, String arch, String debian_arch, String debosFile, String extraPackages, String name, String script) {
    return {
        node('builder' && 'docker') {
            stage("Checkout") {
                checkout scm
            }

            docker.build("debian", "-f jenkins/debian/Dockerfile_debos --pull .").inside("--device=/dev/kvm ${getDockerArgs()}") {
                stage("Build base image for ${arch}") {
                    sh """
                        mkdir -p ${pipeline_version}/${arch}
                        debos -t architecture:${debian_arch} -t basename:${pipeline_version}/${arch} -t extra_packages:'${extraPackages}' -t script:${script} ${debosFile}
                    """
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/initrd.cpio.gz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/rootfs.cpio.gz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/full.rootfs.tar.xz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/full.rootfs.cpio.gz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/rootfs.ext4.xz", fingerprint: true
                }

                stage("Upload images for ${arch}") {
                    withCredentials([string(credentialsId: 'Staging KernelCI API Token', variable: 'API_TOKEN')]) {
                        sh """
                            python push-source.py --token ${API_TOKEN} --api https://staging-api.kernelci.org \
                                --publish_path images/rootfs/debian/${name}/ \
                                --file ${pipeline_version}/${arch}/*.*
                        """
                    }
                }
            }
        }
    }
}


// make sure the kvm group gid is passed to docker with option --group-add
def getDockerArgs() {

  def GROUP = sh(returnStdout: true, script: 'getent group kvm | cut -d : -f 3').trim()

  if (GROUP == "") {
    // defaults to user group gid
    GROUP = sh(returnStdout: true, script: 'id -g').trim()
  }

  return "--group-add " + "${GROUP}"
}


