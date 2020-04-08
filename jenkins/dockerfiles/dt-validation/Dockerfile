FROM kernelci/build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-8 \
    gcc-8-plugin-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-8 500

RUN pip3 install git+https://github.com/devicetree-org/dt-schema.git@master
