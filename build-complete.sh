#!/bin/bash

rm -rf *


if [ $PUBLISH != true ]; then
  echo "Skipping publish step.  PUBLISH != true."
  exit 0
fi

if [[ -z $TREE_NAME ]]; then
  echo "TREE_NAME not set.  Not publishing."
  exit 1
fi

if [[ -z $GIT_DESCRIBE ]]; then
  echo "GIT_DESCRIBE not set. Not publishing."
  exit 1
fi

if [[ -z $ARCH_LIST ]]; then
  echo "ARCH_LIST not set.  Not publishing."
  exit 1
fi

if [[ -z $EMAIL_AUTH_TOKEN ]]; then
  echo "EMAIL_AUTH_TOKEN not set.  Not publishing."
  exit 1
fi

echo "ARCH=${ARCH_LIST},TREE_NAME=${TREE_NAME},GIT_DESCRIBE=${GIT_DESCRIBE},BUILD_NUMBER=${BUILD_NUMBER}" >> /home/buildslave/build-complete.log

# Sanity prevails, do the copy
for arch in ${ARCH_LIST}; do
    BASEDIR=/var/www/images/kernel-ci/$TREE_NAME/$GIT_DESCRIBE
    sudo touch ${BASEDIR}/$arch.done
    sudo find ${BASEDIR} -type f -path "*/$arch-*" -fprint ${BASEDIR}/$arch.filelist
done

# Check if all builds for all architectures have finished. The magic number here is 4 (arm, arm64, x86, mips64)
# This magic number will need to be changed if new architectures are added.
export BUILDS_FINISHED=$(ls /var/www/images/kernel-ci/$TREE_NAME/$GIT_DESCRIBE/ | grep .done | wc -l)
if [[ BUILDS_FINISHED -eq 4 ]]; then
    echo "All builds have now finished, triggering testing..."
    # Tell the dashboard the job has finished build.
    echo "Build has now finished, reporting result to dashboard."
    curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'"}' https://api.kernelci.org/job
    if [ $EMAIL != true ]; then
        echo "Not sending emails because EMAIL was false"
        exit 0
    fi
    if [ "$TREE_NAME" == "arm-soc" ] || [ "$TREE_NAME" == "mainline" ] || [ "$TREE_NAME" == "stable" ] || [ "$TREE_NAME" == "rmk" ] || [ "$TREE_NAME" == "tegra" ]; then
        # Public Mailing List
        echo "Sending results pubic mailing list"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "next" ]; then
        echo "Sending results to Linux Next"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["linux-next@vger.kernel.org"], "format": ["txt"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": [linux-next@vger.kernel.org"], "format": ["txt"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "alex" ]; then
        echo "Sending results to Alex Bennee"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["alex.bennee@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["alex.bennee@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "amitk" ]; then
        echo "Sending results to Amit Kucheria"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["amit.kucheria@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["amit.kucheria@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "anders" ]; then
        echo "Sending results to Anders Roxell"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["anders.roxell@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["anders.roxell@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "collabora" ]; then
        echo "Sending results to Collabora team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["sjoerd.simons@collabora.co.uk", "luis.araujo@collabora.co.uk", "daniels@collabora.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["sjoerd.simons@collabora.co.uk", "luis.araujo@collabora.co.uk", "daniels@collabora.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "dlezcano" ]; then
        echo "Sending results to Daniel Lezcano"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["daniel.lezcano@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["daniel.lezcano@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "omap" ]; then
        echo "Sending results to Tony Lindgren"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["tony@atomide.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["tony@atomide.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "lsk" ]; then
        echo "Sending results to LSK team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["lsk-team@linaro.org", "alex.shi@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["lsk-team@linaro.org", "alex.shi@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "qcom-lt" ]; then
        echo "Sending results to QCOM-LT team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["nicolas.dechesne@linaro.org", "srinivas.kandagatla@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["nicolas.dechesne@linaro.org", "srinivas.kandagatla@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "viresh" ]; then
        echo "Sending results to Viresh Kumar"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["viresh.kumar@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["viresh.kumar@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "krzysztof" ]; then
        echo "Sending results to Krzysztof Kozlowski"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["krzk@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["k.kozlowski@samsung.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "samsung" ]; then
        echo "Sending results to Samsung Team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["k.kozlowski@samsung.com", "kgene.kim@samsung.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["k.kozlowski@samsung.com", "kgene.kim@samsung.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "agross" ]; then
        echo "Sending results to Andy Gross"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["agross@codeaurora.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["agross@codeaurora.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "broonie-regmap" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "broonie-regulator" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "broonie-sound" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "broonie-spi" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "renesas" ]; then
        echo "Sending results to Simon Horman"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["horms@verge.net.au", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["horms@verge.net.au", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "ulfh" ]; then
        echo "Sending results to Ulf Hansson"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["ulf.hansson@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["ulf.hansson@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "ardb" ]; then
        echo "Sending results to Ard Biesheuvel"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["ard.biesheuvel@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["ard.biesheuvel@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "evalenti" ]; then
        echo "Sending results to Eduardo Valentin"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["edubezval@gmail.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["edubezval@gmail.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "tegra" ]; then
        echo "Sending results to Tegra maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["thierry.reding@gmail.com", "jonathanh@nvidia.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["thierry.reding@gmail.com", "jonathanh@nvidia.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "efi" ]; then
        echo "Sending results to Tegra maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["ard.biesheuvel@linaro.org", "fellows@kernelci.org", "matt@codeblueprint.co.uk"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["ard.biesheuvel@linaro.org", "fellows@kernelci.org", "matt@codeblueprint.co.uk"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "pmwg" ]; then
        echo "Sending results to PMWG maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["private-pmwg@lists.linaro.org"], "format": ["txt"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": [ "daniel.lezcano@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["private-pmwg@lists.linaro.org "], "format": ["txt"], "delay": 12600}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": [, "daniel.lezcano@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif [ "$TREE_NAME" == "leg" ]; then
        echo "Sending results to LEG maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["linaro-acpi@lists.linaro.org", "graeme.gregory@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["linaro-acpi@lists.linaro.org", "graeme.gregory@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    elif ["$TREE_NAME" == "drm-tip"]; then
        echo "Sending results to DRM-TIP maintainers"
        curl -XPOST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "drm-tip", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "format": ["txt"], "send_to": ["daniel@ffwll.ch", "fellows@kernelci.org"], "delay": 60}'
        curl -XPOST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "drm-tip", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "format": ["txt"], "send_to": ["daniel@ffwll.ch", "fellows@kernelci.org"], "delay": 12600}'
    elif ["$TREE_NAME" == "android"]; then
        echo "Sending results to Android maintainers"
        curl -XPOST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "android", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "format": ["txt"], "send_to": ["kernel-team+kernelci@android.com", "gregkh@google.com", "fellows@kernelci.org"], "delay": 60}'
        curl -XPOST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "android", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "format": ["txt"], "send_to": ["kernel-team+kernelci@android.com", "gregkh@google.com", "fellows@kernelci.org"], "delay": 12600}'
    else
        # Private Mailing List
        echo "Sending results to private mailing list"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' https://api.kernelci.org/send
    fi

    # Send stable* reports to stable list
    if [[ "$TREE_NAME" == "stable"* ]]; then
        echo "Sending stable results to stable pubic mailing list"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "build_report": 1, "send_to": ["stable@vger.kernel.org"], "format": ["txt"], "delay": 10}' https://api.kernelci.org/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "boot_report": 1, "send_to": ["stable@vger.kernel.org"], "format": ["txt"], "delay": 12600}' https://api.kernelci.org/send
    fi
fi
