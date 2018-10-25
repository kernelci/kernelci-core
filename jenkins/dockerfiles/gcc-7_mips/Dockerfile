FROM kernelci/build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-7-mips-linux-gnu

RUN update-alternatives \
    --install /usr/bin/mips-linux-gnu-gcc mips-linux-gnu-gcc /usr/bin/mips-linux-gnu-gcc-7 500 \
    --slave /usr/bin/mips-linux-gnu-gcc-ar mips-linux-gnu-ar /usr/bin/mips-linux-gnu-gcc-ar-7 \
    --slave /usr/bin/mips-linux-gnu-gcc-nm mips-linux-gnu-nm /usr/bin/mips-linux-gnu-gcc-nm-7 \
    --slave /usr/bin/mips-linux-gnu-gcc-ranlib mips-linux-gnu-ranlib /usr/bin/mips-linux-gnu-gcc-ranlib-7 \
    --slave /usr/bin/mips-linux-gnu-gcc-gcov mips-linux-gnu-gcov /usr/bin/mips-linux-gnu-gcov-7 \
    --slave /usr/bin/mips-linux-gnu-gcc-gcov-dump mips-linux-gnu-gcov-dump /usr/bin/mips-linux-gnu-gcov-dump-7 \
    --slave /usr/bin/mips-linux-gnu-gcc-gcov-tool mips-linux-gnu-gcov-tool /usr/bin/mips-linux-gnu-gcov-tool-7
