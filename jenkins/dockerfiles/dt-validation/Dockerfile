FROM kernelci/build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-8 \
    gcc-8-plugin-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-8 500

RUN sudo apt install flex bison
RUN sudo apt install pkg-config python-yaml device-tree-compiler
RUN sudo apt install libyaml-dev
RUN make defconfig

RUN pip3 install git+https://github.com/devicetree-org/dt-schema.git@master 
RUN export PATH=$HOME/.local/bin/:$PATH
