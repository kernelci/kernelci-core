#!/bin/bash

# Important: This script is run under QEMU

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
	  software-properties-common
"

GST_DEPS="\
	  libglib2.0-dev \
	  libgudev-1.0-dev
"

CACHING_SERVICE="http://kernelci1.eastus.cloudapp.azure.com:8888/cache?uri="

export DEBIAN_FRONTEND=noninteractive

# Install dependencies
echo 'deb http://deb.debian.org/debian bookworm-backports main' >>/etc/apt/sources.list
apt-get update
apt-get install --no-install-recommends -y ${BUILD_DEPS} ${GST_DEPS} curl
apt-mark manual python3 libpython3-stdlib python3 libglib2.0-0 libgudev-1.0

# Get latest meson from pip
pip3 install meson --break-system-packages

if [ "$(uname -m)" == "x86_64" ]; then
  # Install non-free intel media-driver
  apt-add-repository -y non-free
  apt-get update
  apt-get install -y intel-media-va-driver-non-free
fi

# Verify if CACHING_SERVICE is reachable by curl, if not, unset it
if [ ! -z ${CACHING_SERVICE} ]; then
  # disable set -e
  set +e
  curl -s --head --request GET ${CACHING_SERVICE}
  # if exit code is not 0, unset CACHING_SERVICE
  if [ $? -ne 0 ]; then
	echo "CACHING_SERVICE is not reachable, unset it"
	unset CACHING_SERVICE
  fi
  set -e
fi

# Configure git
git config --global user.email "bot@kernelci.org"
git config --global user.name "KernelCI Bot"

########################################################################
# Build gstreamer                                                      #
########################################################################
GSTREAMER_URL=https://gitlab.freedesktop.org/gstreamer/gstreamer.git
mkdir -p /var/tests/gstreamer && cd /var/tests/gstreamer

git clone --depth 1 $GSTREAMER_URL .

meson setup build \
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

########################################################################
# Get fluster                                                          #
########################################################################
get_json_obj_field() {
	local json_obj=${1}
	local field=${2}

	echo "${json_obj}" | jq ".${field}" | tr -d '"'
}

extract_vector_from_archive() {
	local archive_filename
	archive_filename=$(readlink -e "${1}")

	local vector_filename=${2}

	case "${archive_filename}" in
	*.tar.gz | *.tgz | *.tar.bz2 | *.tbz2)
		tar -xf "${archive_filename}"
		;;
	*.zip)
		unzip -o "${archive_filename}" "${vector_filename}"
		;;
	*)
		return
		;;
	esac

	rm "${archive_filename}"
}

download_fluster_testsuite() {
	local fluster_testsuite="${1}"

	[ -z "${fluster_testsuite}" ] && {
		echo "No JSON test suite file provided"
		exit 1
	}

	# disable set -e (immediate exit) to allow error handling after readlink failure
	set +e
	json_file=$(readlink -e "${fluster_testsuite}")
	set -e

	if [ ! -f "${json_file}" ]; then
		echo "${fluster_testsuite} file not found!"
		exit 1
	fi

	suite_name=$(jq '.name' "${json_file}" | tr -d '"')

	# Create and enter suite directory
	mkdir --parents ./resources/"${suite_name}" && pushd "$_" || exit

	vector_count=$(jq '.test_vectors | length' "${json_file}")

	for i in $(seq 0 $((vector_count - 1))); do
		vector_json_obj=$(jq -c '.test_vectors['"${i}"']' "${json_file}")

		# Parse JSON to get vector information
		vector_name=$(get_json_obj_field "${vector_json_obj}" 'name')
		vector_url=$(get_json_obj_field "${vector_json_obj}" 'source')
		vector_md5=$(get_json_obj_field "${vector_json_obj}" 'source_checksum')
		vector_filename=$(get_json_obj_field "${vector_json_obj}" 'input_file')

		vector_archive=$(basename "${vector_url}")

		# Create and enter vector directory
		mkdir --parents "${vector_name}" && pushd "$_" || exit

		# Download the test vector
		if [ -z ${CACHING_SERVICE} ]; then
		  wget --no-verbose --inet4-only --no-clobber --tries 5 "${vector_url}" || exit
		else
		  echo "${CACHING_SERVICE}${vector_url}"
		  wget --no-verbose --inet4-only --no-clobber --tries 5 "${CACHING_SERVICE}${vector_url}" -O  "${vector_archive}" || exit
		fi

		# Verify checksum
		if [ "${vector_md5}" != "$(md5sum "${vector_archive}" | cut -d' ' -f1)" ]; then
			echo "MD5 mismatch, exiting"
			exit 1
		else
			# Unpack if necessary
			extract_vector_from_archive "${vector_archive}" "${vector_filename}"
		fi

		popd || exit

	done

	popd || exit

}

FLUSTER_URL=https://github.com/fluendo/fluster.git

mkdir -p /opt/fluster && cd /opt/fluster

git clone $FLUSTER_URL .

download_fluster_testsuite ./test_suites/av1/AV1-TEST-VECTORS.json
download_fluster_testsuite ./test_suites/av1/CHROMIUM-10bit-AV1-TEST-VECTORS.json
download_fluster_testsuite ./test_suites/h264/JVT-AVC_V1.json
download_fluster_testsuite ./test_suites/h264/JVT-FR-EXT.json
download_fluster_testsuite ./test_suites/h265/JCT-VC-HEVC_V1.json
download_fluster_testsuite ./test_suites/vp8/VP8-TEST-VECTORS.json
download_fluster_testsuite ./test_suites/vp9/VP9-TEST-VECTORS.json

# Get junitparser for parsing fluster results
pip3 install junitparser --break-system-packages

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /var/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean
