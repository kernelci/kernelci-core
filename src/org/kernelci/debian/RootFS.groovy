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

/* ----------------------------------------------------------------------------
 * Jenkins parameters

KCI_API_URL (https://api.kernelci.org)
  URL of the KernelCI backend API
KCI_TOKEN_ID
  Identifier of the KernelCI backend API token stored in Jenkins

*/

package org.kernelci.debian
import org.kernelci.util.Job


def buildImage(config) {
    def name = config.name
    def archList = config.arch_list
    def debianRelease = config.debian_release

    def debosFile = "jenkins/debian/debos/rootfs.yaml"
    /* Returns the pipeline version with the format YYYYMMMAA.X where X is the
     * number of the build of the day */
    def pipeline_version = VersionNumber(
        versionNumberString: '${BUILD_DATE_FORMATTED,"yyyyMMdd"}.${BUILDS_TODAY_Z}')

    def vmMemory = config.vm_memory ?: "2G"

    /* debos will always run the extra packages step, so let's make sure it has
     * something to install */
    def extraPackages = "bash"
    if (config.extra_packages != null) {
        extraPackages = config.extra_packages
    }

    def extraPackagesRemove = config.extra_packages_remove ?: ""
    def extraFilesRemove = config.extra_files_remove ?: ""

    // defaults to empty script scripts/nothing.sh
    def script = "scripts/nothing.sh"
    if (config.script != null) {
        script = config.script
    }

    def test_overlay = config.test_overlay ?: ""

    def docker_image = config.docker_image ?: "kernelci/debos"

    def stepsForParallel = [:]
    for (int i = 0; i < archList.size(); i++) {
        def arch = archList[i]
        def buildStep = "Build image for ${arch}"
        stepsForParallel[buildStep] = makeImageStep(pipeline_version,
                                                    vmMemory,
                                                    arch,
                                                    debianRelease,
                                                    debosFile,
                                                    extraPackages,
                                                    extraPackagesRemove,
                                                    extraFilesRemove,
                                                    name,
                                                    script,
                                                    test_overlay,
                                                    docker_image)
    }

    parallel stepsForParallel
}


def makeImageStep(String pipeline_version,
                  String vmMemory,
                  String arch,
                  String debianRelease,
                  String debosFile,
                  String extraPackages,
                  String extraPackagesRemove,
                  String extraFilesRemove,
                  String name,
                  String script,
                  String test_overlay,
                  String docker_image) {
    return {
        node("docker && debos") {
            stage("Checkout") {
                checkout scm
            }

            j = new Job()
            j.dockerPullWithRetry(docker_image).inside(getDockerArgs()) {
                stage("Build base image for ${arch}") {
                    sh """
                        mkdir -p ${pipeline_version}/${arch}
                        debos \
                            -m ${vmMemory} \
                            -t architecture:${arch} \
                            -t suite:${debianRelease} \
                            -t basename:${pipeline_version}/${arch} \
                            -t extra_packages:'${extraPackages}' \
                            -t extra_packages_remove:'${extraPackagesRemove}' \
                            -t extra_files_remove:'${extraFilesRemove}' \
                            -t script:${script} \
                            -t test_overlay:'${test_overlay}' \
                            ${debosFile}
                    """
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/initrd.cpio.gz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/rootfs.cpio.gz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/full.rootfs.tar.xz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/full.rootfs.cpio.gz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/rootfs.ext4.xz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/build_info.json", fingerprint: true
                }

                stage("Upload images for ${arch}") {
                    withCredentials([string(credentialsId: params.KCI_TOKEN_ID, variable: 'API_TOKEN')]) {
                        sh """
                            python push-source.py --token ${API_TOKEN} --api ${params.KCI_API_URL} \
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
    def group = sh(returnStdout: true,
                   script: "getent group kvm | cut -d : -f 3").trim()

    if (group == "") {
        // defaults to user group gid
        group = sh(returnStdout: true, script: "id -g").trim()
    }

    return "--device=/dev/kvm --group-add ${group}"
}
