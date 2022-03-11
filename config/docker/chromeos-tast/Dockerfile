FROM debian:bullseye-slim
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y \
    apt-transport-https \
    bzip2 \
    ca-certificates strace \
    ssh

RUN apt-get update && apt-get install -y \
    curl \
    git \
    inetutils-ping \
    python3 \
    python-pkg-resources \
    vim \
    xz-utils

RUN \
  mkdir -p /home/cros-tast && \
  useradd cros-tast -d /home/cros-tast && \
  chown cros-tast: -R /home/cros-tast && \
  adduser cros-tast sudo && \
  echo "cros-tast ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER cros-tast
ENV HOME=/home/cros-tast
WORKDIR $HOME

RUN mkdir -p $HOME/trunk
RUN git clone \
    https://chromium.googlesource.com/chromiumos/chromite \
    $HOME/trunk/chromite
ENV PATH=$PATH:$HOME/trunk/chromite/scripts
RUN yes | gsutil update

# This SSH key is only used with Chrome OS test images.
RUN mkdir "$HOME/.ssh"
RUN cp "$HOME/trunk/chromite/ssh_keys/testing_rsa" "$HOME/.ssh/id_rsa"
RUN chmod 0600 "$HOME/.ssh/id_rsa"

ADD tast-parser.py /home/cros-tast/tast-parser.py

# Needed by LAVA to install the overlay
USER root
