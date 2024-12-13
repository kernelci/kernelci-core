#!/bin/bash
set -e

BUILD_DEPS="\
	  g++ \
	  flex \
	  bison \
	  ninja-build \
	  git \
	  python3-pip \
	  pkg-config \
	  openssl \
	  ca-certificates \
	  jq \
	  wget \
	  unzip \
	  software-properties-common \
	  libclang-dev
"

GST_DEPS="\
	  libglib2.0-dev \
	  libgudev-1.0-dev
"

export DEBIAN_FRONTEND=noninteractive

# Install dependencies
echo 'deb http://deb.debian.org/debian bookworm-backports main' >>/etc/apt/sources.list
apt-get update
apt-get install --no-install-recommends -y ${BUILD_DEPS} ${GST_DEPS} curl
apt-mark manual python3 libpython3-stdlib python3 libglib2.0-0 libgudev-1.0
apt-get remove -y libgstreamer1.0-0

# Get latest meson from pip
pip3 install meson --break-system-packages

# Get latest stable rustc and cargo
curl https://sh.rustup.rs -sSf | sh -s -- -y
# add cargo path
. "$HOME/.cargo/env"

H26FORGE_URL=https://github.com/h26forge/h26forge.git
H26FORGE=target/release/h26forge
output_dir="test_videos"
tool_args="--mp4 --mp4-rand-size --safestart"
generation_args="--small --ignore-edge-intra-pred --ignore-ipcm --config config/default.json"

# Configure git
git config --global user.email "bot@kernelci.org"
git config --global user.name "KernelCI Bot"

GSTREAMER_URL=https://gitlab.freedesktop.org/gstreamer/gstreamer.git

mkdir -p /var/tests/gstreamer && cd /var/tests/gstreamer

git clone --depth 1 $GSTREAMER_URL .

meson setup build \
	--prefix=/usr \
	--wrap-mode=nofallback \
	-Dauto_features=disabled \
	-Dbad=enabled \
	-Dbase=enabled \
	-Dgood=enabled \
	-Dugly=disabled \
	-Dgst-plugins-bad:ivfparse=enabled \
	-Dgst-plugins-bad:debugutils=enabled \
	-Dgst-plugins-bad:v4l2codecs=enabled \
	-Dgst-plugins-bad:videoparsers=enabled \
	-Dgst-plugins-base:app=enabled \
	-Dgst-plugins-base:playback=enabled \
	-Dgst-plugins-base:tools=enabled \
	-Dgst-plugins-base:typefind=enabled \
	-Dgst-plugins-base:videoconvertscale=enabled \
	-Dgst-plugins-good:matroska=enabled \
	-Dgst-plugins-good:v4l2=enabled \
	-Dtools=enabled \
	-Ddevtools=disabled \
	-Dges=disabled \
	-Dlibav=disabled \
	-Drtsp_server=disabled

ninja -C build
ninja -C build install

mkdir -p /opt/h26forge && cd /opt/h26forge

git clone --depth 1 $H26FORGE_URL .

cargo update -vv
cargo build --release

if [ ! -f $H26FORGE ]; then
	echo "h26forge not found"
	exit 1
fi

mkdir -p $output_dir
for i in $(seq -f "%04g" 0 99); do
  $H26FORGE $tool_args generate $generation_args -o $output_dir/video$i.264
  gst-launch-1.0 filesrc location=$output_dir/video$i.264.mp4 ! parsebin ! fakesink
done

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /var/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean
