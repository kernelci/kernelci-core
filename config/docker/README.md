## Prerequisites

The `kci_docker` tool only requires Python 3 and the `docker` and `jinja2`
packages.  To install all this on a Debian-based distribution:

```
sudo apt update
sudo apt install -y python3 python3-pip
pip3 install -r requirements.txt
```

## Docker images and tag names

The base name for each Docker image follows the main application contained in
the image.  For example: `clang-14`, `gcc-10`, `k8s`, `kernelci`.  Then the tag
is composed of an optional kernel CPU architecture name when applicable
(currently only with GCC images) followed by optional additional fragments.  A
prefix can be used to specify the Docker Hub account where the image should be
pushed, or for local name spaces.  The overall pattern looks like this:

    {{ prefix }}{{ image }}:{{ arch }}{{ -fragment2 }}{{ -fragment2 }}{{ ... }}

The fragment names are additional features to be added to the image.  These are
typically useful when running jobs in a local shell all in the same container.
For Kubernetes deployment in produciton, each step should be run in a separate
container which would only include one application.

Here are a few image names examples:

* `kernelci/gcc-10:x86`
* `kernelci/gcc-10:x86-kunit`
* `my-image/gcc-10:x86-kunit-kernelci`
* `kernelci/gcc-10:arm64-kselftest`
* `kernelci/clang-14`
* `kernelci/clang-14:kselftest`
* `kernelci`
* `kernelci/k8s`
* `pipeline-dev/k8s-kernelci`

## Command line syntax

See `kci_docker --help` for the full details about how to use the tool.  It
generates a `Dockerfile` on the fly based on Jinja2 templates then builds it
and tags it with the Python SDK directly.  It's possible to dump it in a
`Dockerfile` and do a manual build.  Here are a few examples to get started:

Get the full name of a Docker image without building it:

    $ ./kci_docker name gcc-10 --arch=x86 --fragment=kernelci
    kernelci/gcc-10:x86-kernelci

Build an image with GCC only and a local prefix:

    $ ./kci_docker build gcc-10 --arch=x86 --prefix=my-stuff/ --verbose
    Building my-stuff/gcc-10:x86
    $ docker images | grep my-stuff
    my-stuff/gcc-10                  x86                  8deb3fdc7ad9   17 seconds ago   584MB

Build an image with just the KernelCI core tools:

    $ ./kci_docker build kernelci --prefix=my-stuff/
    Building my-stuff/kernelci

The plain images with just the compiler toolchains can be used to build Linux
kernels and related things such as KUnit and kselftest etc.  However they don't
contain the KernelCI core tools such as `kci_build`.  With the new pipeline,
when running tests in a local shell, typically the job will directly send the
result to the API from the same container.  That's where having mixed images
with both the compiler and KernelCI core tools.

For example, to build an image with Clang 14 and extra kselftest tools
installed, as well as the KernelCI core tools:

    $ ./kci_docker build clang-14 --prefix=my-stuff/ --fragment=kselftest --fragment=kernelci
    Building my-stuff/clang-14:kselftest-kernelci

Build the `kernelci` image with a particular revision using `--build-arg`:

    ./kci_docker build kernelci --build-arg core_rev=staging-20220728.1
