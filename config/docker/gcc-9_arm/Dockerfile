ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-9-arm-linux-gnueabihf \
    gcc-9-plugin-dev-arm-linux-gnueabihf

RUN update-alternatives \
    --install /usr/bin/arm-linux-gnueabihf-gcc arm-linux-gnueabihf-gcc /usr/bin/arm-linux-gnueabihf-gcc-9 500 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-ar arm-linux-gnueabihf-gcc-ar /usr/bin/arm-linux-gnueabihf-gcc-ar-9 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-nm arm-linux-gnueabihf-gcc-nm /usr/bin/arm-linux-gnueabihf-gcc-nm-9 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-ranlib arm-linux-gnueabihf-gcc-ranlib /usr/bin/arm-linux-gnueabihf-gcc-ranlib-9 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-gcov arm-linux-gnueabihf-gcov /usr/bin/arm-linux-gnueabihf-gcov-8 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-gcov-dump arm-linux-gnueabihf-gcov-dump /usr/bin/arm-linux-gnueabihf-gcov-dump-9 \
    --slave /usr/bin/arm-linux-gnueabihf-gcc-gcov-tool arm-linux-gnueabihf-gcov-tool /usr/bin/arm-linux-gnueabihf-gcov-tool-9

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
   libpopt-dev:armhf
