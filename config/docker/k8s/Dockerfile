#
# Container to drive Kubernetes cluster from KernelCI
#
ARG PREFIX=kernelci/
FROM ${PREFIX}build-base
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

#
# Install gcloud-sdk
# From: https://cloud.google.com/sdk/docs/downloads-apt-get
#
RUN apt-get update && apt-get install -y apt-transport-https ca-certificates gnupg curl
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update && apt-get install -y google-cloud-sdk kubectl

#
# Azure CLI
# From: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-apt?view=azure-cli-latest
#
RUN curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor |  tee /etc/apt/trusted.gpg.d/microsoft.asc.gpg > /dev/null
RUN AZ_REPO=bullseye && echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | tee /etc/apt/sources.list.d/azure-cli.list
RUN apt-get update && apt-get install -y azure-cli

#
# Kubernetes python lib (need latest from pip)
# - remove existing deps (urllib3, requests) to be sure
#   latest are installed from pip
#
RUN apt-get update && apt-get install -y python3-pip python3-setuptools
RUN apt-get remove -y python3-urllib3 python3-requests && apt-get autoremove -y
RUN python3 -m pip install --upgrade kubernetes

#
# pygit2
# - Could use Debian package python3-pygit2 but follow the Kubernetes 
#   library to avoid confusion with multiple package managers.
#
RUN apt-get install -y libgit2-dev
RUN python3 -m pip install --upgrade pygit2
