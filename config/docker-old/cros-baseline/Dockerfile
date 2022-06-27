FROM debian:bullseye-slim
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y \
    apt-transport-https \
    ca-certificates 

RUN apt-get update && apt-get install -y \
    git \
    inetutils-ping \
    ssh

RUN \
  mkdir -p /home/cros && \
  useradd cros -d /home/cros && \
  chown cros: -R /home/cros && \
  adduser cros sudo && \
  echo "cros ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER cros
ENV HOME=/home/cros
WORKDIR $HOME

# All this just to extract rsa key to access DUT
# Adding private key "as is" might trigger github audit alert
RUN mkdir -p $HOME/trunk
RUN git clone \
    https://chromium.googlesource.com/chromiumos/chromite \
    $HOME/trunk/chromite
ENV PATH=$PATH:$HOME/trunk/chromite/scripts

# This SSH key is only used with Chrome OS test images.
RUN mkdir "$HOME/.ssh"
RUN cp "$HOME/trunk/chromite/ssh_keys/testing_rsa" "$HOME/.ssh/id_rsa"
RUN chmod 0600 "$HOME/.ssh/id_rsa"

ADD https://raw.githubusercontent.com/kernelci/kernelci-core/chromeos.kernelci.org/config/rootfs/debos/overlays/baseline/opt/kernelci/dmesg.sh /home/cros/dmesg.sh

# Needed by LAVA to install the overlay
USER root
