FROM debian:bullseye

RUN echo deb http://deb.debian.org/debian bullseye-backports main \
	> /etc/apt/sources.list.d/backports.list

RUN apt-get update && \
    apt-get install -t bullseye-backports --yes --no-install-recommends \
	qemu-system \
	qemu-system-arm \
	qemu-system-mips \
	qemu-system-misc \
	qemu-system-ppc \
	qemu-system-s390x \
	qemu-system-sparc \
	qemu-system-x86 \
	qemu-utils && \
	apt-get clean

RUN mkdir -p /etc/qemu && echo allow all > /etc/qemu/bridge.conf
