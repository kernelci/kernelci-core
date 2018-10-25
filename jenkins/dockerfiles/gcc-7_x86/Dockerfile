FROM kernelci/build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-7

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 500
