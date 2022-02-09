ARG PREFIX=kernelci/
FROM ${PREFIX}clang-base

RUN wget -q -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN echo 'deb http://apt.llvm.org/bullseye/ llvm-toolchain-bullseye-14 main' \
   >> /etc/apt/sources.list.d/clang.list

RUN apt-get update && apt-get install --no-install-recommends -y \
    clang-14 lld-14 llvm-14

ENV PATH=/usr/lib/llvm-14/bin:${PATH}
