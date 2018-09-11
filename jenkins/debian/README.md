# Creation of Debian-based base ramdisks

Jenkinsfile defines a Jenkins Pipeline creating a stripped-down
Debian image for x86, x86_64, armhf, armel and arm64.

These images are created using [debos](https://github.com/go-debos/debos)
that's installed with all its dependencies in the docker image used by
the pipeline.

The pipeline has been tested in a Jenkins installation setup using docker
as agents.
At least the following Jenkins plugins must be installed:

- [pipeline](https://wiki.jenkins-ci.org/display/JENKINS/Pipeline+Plugin)
- [docker pipeline](http://wiki.jenkins-ci.org/display/JENKINS/Docker+Pipeline+Plugin)
- [version number](https://wiki.jenkins-ci.org/display/JENKINS/Version+Number+Plugin)

debos also needs the kvm module loaded by the build host.

