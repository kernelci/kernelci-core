FROM debian:bullseye

RUN apt-get update && \
	apt-get install --yes --no-install-recommends \
	qemu-system \
	qemu-system-arm \
	qemu-system-mips \
	qemu-system-misc \
	qemu-system-ppc \
	qemu-system-s390x \
	qemu-system-sparc \
	qemu-system-x86 && \
	apt-get clean
