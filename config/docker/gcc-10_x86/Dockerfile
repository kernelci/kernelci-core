ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-10 \
    gcc-10-plugin-dev

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 500

# kselftest
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev \
   libcap-dev \
   libcap-ng-dev \
   libelf-dev \
   libfuse-dev \
   libhugetlbfs-dev \
   libmnl-dev \
   libnuma-dev \
   libpopt-dev \
   libasound2-dev \
   patch \
   pkg-config

# 32-bit support for kselftest
RUN apt-get update && apt-get install --no-install-recommends -y \
   gcc-multilib \
   libc6-i386 \
   libc6-dev-i386

ADD gcc-header-fix.patch /
RUN cd / && patch -p1 </gcc-header-fix.patch
