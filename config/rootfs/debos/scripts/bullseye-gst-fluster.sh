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
	  unzip
"

GST_DEPS="\
	  libglib2.0-dev \
	  libgudev-1.0-dev
"

CACHING_SERVICE="http://kernelci7.westus2.cloudapp.azure.com:8888/cache?uri="

# Install dependencies
echo 'deb http://deb.debian.org/debian bullseye-backports main' >>/etc/apt/sources.list
apt-get update
apt-get install --no-install-recommends -y ${BUILD_DEPS} ${GST_DEPS}
apt-mark manual python3 libpython3-stdlib libpython3.9-stdlib python3.9 libglib2.0-0 libgudev-1.0

# Get latest meson from pip
pip3 install meson

# Configure git
git config --global user.email "bot@kernelci.org"
git config --global user.name "KernelCI Bot"

########################################################################
# Build gstreamer                                                      #
########################################################################
GSTREAMER_URL=https://gitlab.freedesktop.org/gstreamer/gstreamer.git
mkdir -p /var/tests/gstreamer && cd /var/tests/gstreamer

git clone --depth 1 $GSTREAMER_URL .

meson build \
	--wrap-mode=nofallback \
	-Dauto_features=disabled \
	-Dbad=enabled \
	-Dbase=enabled \
	-Dgood=enabled \
	-Dgst-plugins-bad:ivfparse=enabled \
	-Dgst-plugins-bad:v4l2codecs=enabled \
	-Dgst-plugins-bad:videoparsers=enabled \
	-Dgst-plugins-base:app=enabled \
	-Dgst-plugins-base:playback=enabled \
	-Dgst-plugins-base:tools=enabled \
	-Dgst-plugins-base:typefind=enabled \
	-Dgst-plugins-base:videoconvertscale=enabled \
	-Dgst-plugins-good:matroska=enabled \
	-Dtools=enabled

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
	json_file=$(readlink -e "${1}")

	[ -z "${json_file}" ] && {
		echo "No JSON test suite file provided"
		exit 1
	}

	if [ ! -f "${json_file}" ]; then
		echo "${json_file} file not found!"
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
download_fluster_testsuite ./test_suites/h264/JVT-AVC_V1.json
download_fluster_testsuite ./test_suites/h265/JCT-VC-HEVC-V1.json
download_fluster_testsuite ./test_suites/vp8/VP8-TEST-VECTORS.json
download_fluster_testsuite ./test_suites/vp9/VP9-TEST-VECTORS.json

# Get junitparser for parsing fluster results
pip3 install junitparser

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /var/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean
