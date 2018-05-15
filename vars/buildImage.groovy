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

    def stepsForParallel = [:]
    for (int i = 0; i < kernel_arch.size(); i++) {
        def arch = kernel_arch[i]
        def buildStep = "Build image for ${arch}"
        stepsForParallel[buildStep] = makeImageStep(pipeline_version,
                                                    arch,
                                                    debian_arch[arch],
                                                    debosFile,
                                                    extraPackages)
    }

    parallel stepsForParallel
}


def makeImageStep(String pipeline_version, String arch, String debian_arch, String debosFile, String extraPackages) {
    return {
        node {
            stage("Checkout") {
                checkout scm
            }

            docker.build("debian", "-f jenkins/debian/Dockerfile_debos --pull .").inside("--device=/dev/kvm ${getDockerArgs()}") {
                stage("Build base image for ${arch}") {
                    sh """
                        mkdir -p ${pipeline_version}/${arch}
                        debos -t architecture:${debian_arch} -t basename:${pipeline_version}/${arch} -t extra_packages:'${extraPackages}' ${debosFile}
                    """
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/initrd.cpio.gz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/rootfs.cpio.gz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/full.rootfs.tar.xz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/full.rootfs.cpio.gz", fingerprint: true
                archiveArtifacts artifacts: "${pipeline_version}/${arch}/rootfs.ext4.xz", fingerprint: true
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
    GROUP = sh(returnStdout: true, script: 'id -u').trim()
  }

  return "--group-add " + "${GROUP}"
}


