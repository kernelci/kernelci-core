FROM kernelci/build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-8 \
    gcc-8-plugin-dev

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-8 500
