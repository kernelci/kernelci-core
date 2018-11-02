FROM kernelci/build-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc-7-riscv64-linux-gnu

RUN update-alternatives \
    --install /usr/bin/riscv64-linux-gnu-gcc riscv64-linux-gnu-gcc /usr/bin/riscv64-linux-gnu-gcc-7 500 \
    --slave /usr/bin/riscv64-linux-gnu-gcc-ar riscv64-linux-gnu-ar /usr/bin/riscv64-linux-gnu-gcc-ar-7 \
    --slave /usr/bin/riscv64-linux-gnu-gcc-nm riscv64-linux-gnu-nm /usr/bin/riscv64-linux-gnu-gcc-nm-7 \
    --slave /usr/bin/riscv64-linux-gnu-gcc-ranlib riscv64-linux-gnu-ranlib /usr/bin/riscv64-linux-gnu-gcc-ranlib-7 \
    --slave /usr/bin/riscv64-linux-gnu-gcc-gcov riscv64-linux-gnu-gcov /usr/bin/riscv64-linux-gnu-gcov-7 \
    --slave /usr/bin/riscv64-linux-gnu-gcov-gcc-dump riscv64-linux-gnu-gcov-dump /usr/bin/riscv64-linux-gnu-gcov-dump-7 \
    --slave /usr/bin/riscv64-linux-gnu-gcov-gcc-tool riscv64-linux-gnu-gcov-tool /usr/bin/riscv64-linux-gnu-gcov-tool-7
    
