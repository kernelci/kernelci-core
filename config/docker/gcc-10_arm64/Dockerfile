ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-10-aarch64-linux-gnu \
    gcc-10-plugin-dev-aarch64-linux-gnu \
    gcc-10-arm-linux-gnueabihf \
    gcc-10-plugin-dev-arm-linux-gnueabihf

RUN update-alternatives \
    --install /usr/bin/aarch64-linux-gnu-gcc aarch64-linux-gnu-gcc /usr/bin/aarch64-linux-gnu-gcc-10 500 \
    --slave /usr/bin/aarch64-linux-gnu-gcc-ar aarch64-linux-gnu-ar /usr/bin/aarch64-linux-gnu-gcc-ar-10 \
    --slave /usr/bin/aarch64-linux-gnu-gcc-nm aarch64-linux-gnu-nm /usr/bin/aarch64-linux-gnu-gcc-nm-10 \
    --slave /usr/bin/aarch64-linux-gnu-gcc-ranlib aarch64-linux-gnu-ranlib /usr/bin/aarch64-linux-gnu-gcc-ranlib-10 \
    --slave /usr/bin/aarch64-linux-gnu-gcc-gcov aarch64-linux-gnu-gcov /usr/bin/aarch64-linux-gnu-gcov-10 \
    --slave /usr/bin/aarch64-linux-gnu-gcov-gcc-dump aarch64-linux-gnu-gcov-dump /usr/bin/aarch64-linux-gnu-gcov-dump-10 \
    --slave /usr/bin/aarch64-linux-gnu-gcov-gcc-tool aarch64-linux-gnu-gcov-tool /usr/bin/aarch64-linux-gnu-gcov-tool-10

RUN update-alternatives \
    --install /usr/bin/arm-linux-gnueabihf-gcc arm-linux-gnueabihf-gcc /usr/bin/arm-linux-gnueabihf-gcc-10 500 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-ar arm-linux-gnueabihf-gcc-ar /usr/bin/arm-linux-gnueabihf-gcc-ar-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-nm arm-linux-gnueabihf-gcc-nm /usr/bin/arm-linux-gnueabihf-gcc-nm-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-ranlib arm-linux-gnueabihf-gcc-ranlib /usr/bin/arm-linux-gnueabihf-gcc-ranlib-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-gcov arm-linux-gnueabihf-gcov /usr/bin/arm-linux-gnueabihf-gcov-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-gcov-dump arm-linux-gnueabihf-gcov-dump /usr/bin/arm-linux-gnueabihf-gcov-dump-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-gcov-tool arm-linux-gnueabihf-gcov-tool /usr/bin/arm-linux-gnueabihf-gcov-tool-10

# kselftest
RUN dpkg --add-architecture arm64
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev:arm64 \
   libcap-dev:arm64 \
   libcap-ng-dev:arm64 \
   libelf-dev:arm64 \
   libfuse-dev:arm64 \
   libhugetlbfs-dev:arm64 \
   libmnl-dev:arm64 \
   libnuma-dev:arm64 \
   libpopt-dev:arm64
