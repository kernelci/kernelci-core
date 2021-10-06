ARG PREFIX=kernelci/
FROM ${PREFIX}build-base

#
# pre-built toolchains for ARC available here:
#    https://github.com/foss-for-synopsys-dwc-arc-processors/toolchain/releases/
#
ENV CROSS_TARBALL arc_gnu_2021.03_prebuilt_elf32_le_linux_install.tar.gz
ENV CROSS_URL https://github.com/foss-for-synopsys-dwc-arc-processors/toolchain/releases/download/arc-2021.03-release/${CROSS_TARBALL}
RUN cd /tmp; wget -q ${CROSS_URL}; tar -C /usr --strip-components=1 -xaf ${CROSS_TARBALL}; rm -f ${CROSS_TARBALL}
