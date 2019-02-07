FROM kernelci/build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    software-properties-common \
    gnupg2
RUN wget -q -O - https://apt.llvm.org/llvm-snapshot.gpg.key| apt-key add -
RUN apt-add-repository 'deb http://apt.llvm.org/unstable/ llvm-toolchain main'
RUN apt-get update && apt-get install --no-install-recommends -y \
    binutils-aarch64-linux-gnu \
    clang-9

RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-9 500

RUN apt-get autoremove -y gcc
