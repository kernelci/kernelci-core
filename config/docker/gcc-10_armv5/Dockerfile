ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-10-arm-linux-gnueabi \
    gcc-10-plugin-dev-arm-linux-gnueabi

RUN update-alternatives \
    --install /usr/bin/arm-linux-gnueabi-gcc arm-linux-gnueabi-gcc /usr/bin/arm-linux-gnueabi-gcc-10 500 \
    --slave /usr/bin/arm-linux-gnueabi-gcc-ar arm-linux-gnueabi-gcc-ar /usr/bin/arm-linux-gnueabi-gcc-ar-10 \
    --slave /usr/bin/arm-linux-gnueabi-gcc-nm arm-linux-gnueabi-gcc-nm /usr/bin/arm-linux-gnueabi-gcc-nm-10 \
    --slave /usr/bin/arm-linux-gnueabi-gcc-ranlib arm-linux-gnueabi-gcc-ranlib /usr/bin/arm-linux-gnueabi-gcc-ranlib-10 \
    --slave /usr/bin/arm-linux-gnueabi-gcc-gcov arm-linux-gnueabi-gcov /usr/bin/arm-linux-gnueabi-gcov-10 \
    --slave /usr/bin/arm-linux-gnueabi-gcc-gcov-dump arm-linux-gnueabi-gcov-dump /usr/bin/arm-linux-gnueabi-gcov-dump-10 \
    --slave /usr/bin/arm-linux-gnueabi-gcc-gcov-tool arm-linux-gnueabi-gcov-tool /usr/bin/arm-linux-gnueabi-gcov-tool-10y

# kselftest
RUN dpkg --add-architecture armel
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev:armel \
   libcap-dev:armel \
   libcap-ng-dev:armel \
   libelf-dev:armel \
   libfuse-dev:armel \
   libhugetlbfs-dev:armel \
   libmnl-dev:armel \
   libnuma-dev:armel \
   libpopt-dev:armel \
   libasound2-dev:armel \
   libasound2-dev \
   pkg-config
