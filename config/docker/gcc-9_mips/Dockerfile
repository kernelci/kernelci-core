ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-9-mips-linux-gnu

RUN update-alternatives \
    --install /usr/bin/mips-linux-gnu-gcc mips-linux-gnu-gcc /usr/bin/mips-linux-gnu-gcc-9 500 \
    --slave /usr/bin/mips-linux-gnu-gcc-ar mips-linux-gnu-ar /usr/bin/mips-linux-gnu-gcc-ar-9 \
    --slave /usr/bin/mips-linux-gnu-gcc-nm mips-linux-gnu-nm /usr/bin/mips-linux-gnu-gcc-nm-9 \
    --slave /usr/bin/mips-linux-gnu-gcc-ranlib mips-linux-gnu-ranlib /usr/bin/mips-linux-gnu-gcc-ranlib-9 \
    --slave /usr/bin/mips-linux-gnu-gcc-gcov mips-linux-gnu-gcov /usr/bin/mips-linux-gnu-gcov-9 \
    --slave /usr/bin/mips-linux-gnu-gcc-gcov-dump mips-linux-gnu-gcov-dump /usr/bin/mips-linux-gnu-gcov-dump-9 \
    --slave /usr/bin/mips-linux-gnu-gcc-gcov-tool mips-linux-gnu-gcov-tool /usr/bin/mips-linux-gnu-gcov-tool-9
