ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    dwarves \
    gcc-10-arm-linux-gnueabihf \
    gcc-10-plugin-dev-arm-linux-gnueabihf

RUN update-alternatives \
    --install /usr/bin/arm-linux-gnueabihf-gcc arm-linux-gnueabihf-gcc /usr/bin/arm-linux-gnueabihf-gcc-10 500 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-ar arm-linux-gnueabihf-gcc-ar /usr/bin/arm-linux-gnueabihf-gcc-ar-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-nm arm-linux-gnueabihf-gcc-nm /usr/bin/arm-linux-gnueabihf-gcc-nm-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-ranlib arm-linux-gnueabihf-gcc-ranlib /usr/bin/arm-linux-gnueabihf-gcc-ranlib-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-gcov arm-linux-gnueabihf-gcov /usr/bin/arm-linux-gnueabihf-gcov-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-gcov-dump arm-linux-gnueabihf-gcov-dump /usr/bin/arm-linux-gnueabihf-gcov-dump-10 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-gcov-tool arm-linux-gnueabihf-gcov-tool /usr/bin/arm-linux-gnueabihf-gcov-tool-10y

# kselftest
RUN dpkg --add-architecture armhf
RUN apt-get update && apt-get install --no-install-recommends -y \
   libc6-dev:armhf \
   libcap-dev:armhf \
   libcap-ng-dev:armhf \
   libelf-dev:armhf \
   libfuse-dev:armhf \
   libhugetlbfs-dev:armhf \
   libmnl-dev:armhf \
   libnuma-dev:armhf \
   libpopt-dev:armhf \
   libasound2-dev:armhf \
   libasound2-dev \
   pkg-config
