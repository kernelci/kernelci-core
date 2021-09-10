ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-8 \
    gcc-8-plugin-dev

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-8 500

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
   libpopt-dev
