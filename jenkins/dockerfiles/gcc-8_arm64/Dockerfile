FROM kernelci/build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-8-aarch64-linux-gnu \
    gcc-8-plugin-dev-aarch64-linux-gnu

RUN update-alternatives \
    --install /usr/bin/aarch64-linux-gnu-gcc aarch64-linux-gnu-gcc /usr/bin/aarch64-linux-gnu-gcc-8 500 \
    --slave /usr/bin/aarch64-linux-gnu-gcc-ar aarch64-linux-gnu-ar /usr/bin/aarch64-linux-gnu-gcc-ar-8 \
    --slave /usr/bin/aarch64-linux-gnu-gcc-nm aarch64-linux-gnu-nm /usr/bin/aarch64-linux-gnu-gcc-nm-8 \
    --slave /usr/bin/aarch64-linux-gnu-gcc-ranlib aarch64-linux-gnu-ranlib /usr/bin/aarch64-linux-gnu-gcc-ranlib-8 \
    --slave /usr/bin/aarch64-linux-gnu-gcc-gcov aarch64-linux-gnu-gcov /usr/bin/aarch64-linux-gnu-gcov-8 \
    --slave /usr/bin/aarch64-linux-gnu-gcov-gcc-dump aarch64-linux-gnu-gcov-dump /usr/bin/aarch64-linux-gnu-gcov-dump-8 \
    --slave /usr/bin/aarch64-linux-gnu-gcov-gcc-tool aarch64-linux-gnu-gcov-tool /usr/bin/aarch64-linux-gnu-gcov-tool-8
