ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-8 \
    gcc-8-plugin-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-8 500

RUN pip3 install --system git+https://github.com/devicetree-org/dt-schema.git@master

RUN apt-get update && apt-get install -y --no-install-recommends \
    bison \
    device-tree-compiler \
    flex \
    libyaml-dev \
    pkg-config \
    python3-yaml
