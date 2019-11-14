#!/bin/bash

set -x

if [ "$PUBLISH" != "true" ]; then
  echo "Skipping publish step.  PUBLISH != true."
  exit 0
fi

if [[ -z $TREE_NAME ]]; then
  echo "TREE_NAME not set.  Not publishing."
  exit 1
fi

if [[ -z $BRANCH ]]; then
  echo "BRANCH not set.  Not publishing."
  exit 1
fi

if [[ -z $GIT_DESCRIBE ]]; then
  echo "GIT_DESCRIBE not set. Not publishing."
  exit 1
fi

if [[ -z $ARCH ]]; then
  echo "ARCH not set.  Not publishing."
  exit 1
fi

if [[ -z $EMAIL_AUTH_TOKEN ]]; then
  echo "EMAIL_AUTH_TOKEN not set.  Not publishing."
  exit 1
fi

if [[ -z $API ]]; then
  echo "API not set.  Not publishing."
  exit 1
fi

echo "ARCH=${ARCH},TREE_NAME=${TREE_NAME},BRANCH=${BRANCH},GIT_DESCRIBE=${GIT_DESCRIBE},BUILD_NUMBER=${BUILD_NUMBER}" >> /tmp/build-complete.log
BASEDIR=/var/www/images/kernel-ci/$TREE_NAME/$BRANCH/$GIT_DESCRIBE

sudo touch ${BASEDIR}/${ARCH}.done

# Check if all builds for all architectures have finished. The magic number here is 4 (arm, arm64, x86, mips64)
# This magic number will need to be changed if new architectures are added.
export BUILDS_FINISHED=$(ls ${BASEDIR}/ | grep .done | wc -l)
if [[ BUILDS_FINISHED -eq 1 ]]; then
    echo "All builds have now finished, triggering testing..."
    # Tell the dashboard the job has finished build.
    echo "Build has now finished, reporting result to dashboard."
    curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'"}' ${API}/job
    if [ "$EMAIL" != "true" ]; then
        echo "Not sending emails because EMAIL was false"
        exit 0
    fi
    if [ "$TREE_NAME" == "soc" ] || [ "$TREE_NAME" == "mainline" ] || [ "$TREE_NAME" == "stable" ] || [ "$TREE_NAME" == "stable-rc" ] || [ "$TREE_NAME" == "rmk" ] || [ "$TREE_NAME" == "tegra" ]; then
        # Public Mailing List
        echo "Sending results pubic mailing list"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "next" ]; then
        echo "Sending results to Linux Next"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["linux-next@vger.kernel.org"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["linux-next@vger.kernel.org"], "format": ["txt"], "delay": 12600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt"], "delay": 12600}' ${API}/send
        echo "Sending build results to clang-built-linux for master only"
        if [ "$BRANCH" == "master" ]; then
          curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["clang-built-linux@googlegroups.com"], "format": ["txt"], "delay": 10}' ${API}/send
        fi
    elif [ "$TREE_NAME" == "alex" ]; then
        echo "Sending results to Alex Bennee"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["alex.bennee@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["alex.bennee@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "amitk" ]; then
        echo "Sending results to Amit Kucheria"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["amit.kucheria@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["amit.kucheria@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "anders" ]; then
        echo "Sending results to Anders Roxell"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["anders.roxell@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["anders.roxell@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "collabora" ]; then
        echo "Sending results to Collabora team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["sjoerd.simons@collabora.co.uk", "luis.araujo@collabora.co.uk", "daniels@collabora.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["sjoerd.simons@collabora.co.uk", "luis.araujo@collabora.co.uk", "daniels@collabora.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "dlezcano" ]; then
        echo "Sending results to Daniel Lezcano"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["daniel.lezcano@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["daniel.lezcano@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "omap" ]; then
        echo "Sending results to Tony Lindgren"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["tony@atomide.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["tony@atomide.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "linusw" ]; then
        echo "Sending results to linux-gpio"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["linux-gpio@vger.kernel.org", "fellows@kernelci.org"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["linux-gpio@vger.kernel.org", "fellows@kernelci.org"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "lsk" ]; then
        echo "Sending results to LSK team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["lsk-team@linaro.org", "alex.shi@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["lsk-team@linaro.org", "alex.shi@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "qcom-lt" ]; then
        echo "Sending results to QCOM-LT team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["qcomlt-patches@lists.linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["qcomlt-patches@lists.linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "viresh" ]; then
        echo "Sending results to Viresh Kumar"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["viresh.kumar@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["viresh.kumar@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "krzysztof" ]; then
        echo "Sending results to Krzysztof Kozlowski"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["krzk@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["krzk@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "samsung" ]; then
        echo "Sending results to Samsung Team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["krzk@kernel.org", "kgene.kim@samsung.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["krzk@kernel.org", "kgene.kim@samsung.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "agross" ]; then
        echo "Sending results to Andy Gross"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["agross@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["agross@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "broonie-regmap" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "broonie-regulator" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "broonie-sound" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "broonie-spi" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["broonie@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "renesas" ]; then
        echo "Sending results to Simon Horman"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["horms@verge.net.au", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["horms@verge.net.au", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "ulfh" ]; then
        echo "Sending results to Ulf Hansson"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["ulf.hansson@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["ulf.hansson@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "ardb" ]; then
        echo "Sending results to Ard Biesheuvel"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["ard.biesheuvel@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["ard.biesheuvel@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "report_type": "test", "plan: "baseline-uefi", "send_to": ["ard.biesheuvel@linaro.org", "anders.roxell@linaro.org", "fellows@kernelci.org"], "format": ["txt""], "delay": 10}' ${API}/send
    elif [ "$TREE_NAME" == "evalenti" ]; then
        echo "Sending results to Eduardo Valentin"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["edubezval@gmail.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["edubezval@gmail.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "tegra" ]; then
        echo "Sending results to Tegra maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["thierry.reding@gmail.com", "jonathanh@nvidia.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["thierry.reding@gmail.com", "jonathanh@nvidia.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "efi" ]; then
        echo "Sending results to Tegra maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["ard.biesheuvel@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["ard.biesheuvel@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "pmwg" ]; then
        echo "Sending results to PMWG maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["private-pmwg@lists.linaro.org"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["daniel.lezcano@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["private-pmwg@lists.linaro.org "], "format": ["txt"], "delay": 12600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["daniel.lezcano@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "leg" ]; then
        echo "Sending results to LEG maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["linaro-acpi@lists.linaro.org", "graeme.gregory@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["linaro-acpi@lists.linaro.org", "graeme.gregory@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "android" ]; then
        echo "Sending results to Android maintainers"
        curl -XPOST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["kernel-team+kernelci@android.com", "gregkh@google.com", "fellows@kernelci.org"], "delay": 60}' ${API}/send
        curl -XPOST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["kernel-team+kernelci@android.com", "gregkh@google.com", "fellows@kernelci.org"], "delay": 12600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["tom.gall@linaro.org", "sumit.semwal@linaro.org", "amit.pundir@linaro.org", "arnd.bergmann@linaro.org", "anmar.oueja@linaro.org"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["tom.gall@linaro.org", "sumit.semwal@linaro.org", "amit.pundir@linaro.org", "arnd.bergmann@linaro.org", "anmar.oueja@linaro.org"], "format": ["txt"], "delay": 12600}' ${API}/send
	if [ "$BRANCH" == "android-3.18" ]; then
            curl -XPOST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["lee.jones@linaro.org"], "delay": 60}' ${API}/send
	fi
    elif [ "$TREE_NAME" == "mattface" ]; then
        echo "Sending results to Matt"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["matt@mattface.org"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["matt@mattface.org"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "gtucker" ]; then
        echo "Sending results to Guillaume"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["guillaume.tucker@collabora.com"], "delay": 0}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["guillaume.tucker@collabora.com"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-vivid", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-uvc", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-drm-kms", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "cros-ec", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "sleep", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
    elif [ "$TREE_NAME" == "tomeu" ]; then
        echo "Sending results to Tomeu"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["tomeu.vizoso@collabora.com"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["tomeu.vizoso@collabora.com"], "delay": 1800}' ${API}/send
    elif [ "$TREE_NAME" == "osf" ]; then
        echo "Sending results to Open Source Foundries"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["tyler@opensourcefoundries.com", "ricardo@opensourcefoundries.com", "michael@opensourcefoundries.com", "marti@opensourcefoundries.com", "alan@opensourcefoundries.com"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["tyler@opensourcefoundries.com", "ricardo@opensourcefoundries.com", "michael@opensourcefoundries.com", "marti@opensourcefoundries.com", "alan@opensourcefoundries.com"], "delay": 1800}' ${API}/send
    elif [ "$TREE_NAME" == "clk" ]; then
        echo "Sending results for CLK tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["sboyd+clkci@kernel.org", "mturquette+clkci@baylibre.com", "kernel-build-reports@lists.linaro.org"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["sboyd+clkci@kernel.org", "mturquette+clkci@baylibre.com", "kernel-build-reports@lists.linaro.org"], "delay": 1800}' ${API}/send
    elif [ "$TREE_NAME" == "chrome-platform" ]; then
        echo "Sending results for Chrome Platform tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["kernel-build-reports@lists.linaro.org", "enric.balletbo@collabora.com", "bleung@chromium.org", "groeck@chromium.org"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["kernel-build-reports@lists.linaro.org", "enric.balletbo@collabora.com", "bleung@chromium.org", "groeck@chromium.org"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "cros-ec", "send_to": ["kernel-build-reports@lists.linaro.org", "enric.balletbo@collabora.com", "bleung@chromium.org", "groeck@chromium.org"], "format": ["txt"], "delay": 5400}' ${API}/send
    elif [ "$TREE_NAME" == "media" ]; then
        echo "Sending results for media tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-vivid", "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt"], "delay": 5400}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-uvc", "send_to": ["kernel-build-reports@lists.linaro.org"], "format": ["txt"], "delay": 5400}' ${API}/send
    elif [ "$TREE_NAME" == "vireshk" ]; then
        echo "Sending results for vireshk's tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["vireshk@kernel.org"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["vireshk@kernel.org"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "sashal" ]; then
        echo "Sending results for sashal's tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["sashal@kernel.org", "kernel-build-reports@lists.linaro.org"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["sashal@kernel.org", "kernel-build-reports@lists.linaro.org"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["sashal@kernel.org", "kernel-build-reports@lists.linaro.org"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "thermal" ]; then
        echo "Sending results for the thermal tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["daniel.lezcano@linaro.org", "kernel-build-reports@lists.linaro.org"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["daniel.lezcano@linaro.org", "kernel-build-reports@lists.linaro.org"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["daniel.lezcano@linaro.org", "kernel-build-reports@lists.linaro.org"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "arm64" ]; then
        echo "Sending results for the arm64 tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["will@kernel.org", "catalin.marinas@arm.com", "linux-arm-kernel@lists.infradead.org", "kernel-build-reports@lists.linaro.org"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["will@kernel.org", "catalin.marinas@arm.com", "linux-arm-kernel@lists.infradead.org", "kernel-build-reports@lists.linaro.org"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["will@kernel.org", "catalin.marinas@arm.com", "linux-arm-kernel@lists.infradead.org", "kernel-build-reports@lists.linaro.org"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "lee" ]; then
        echo "Sending results for lee's tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["lee.jones@linaro org", "kernel-build-reports@lists.linaro.org"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["lee.jones@linaro org", "kernel-build-reports@lists.linaro.org"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["lee.jones@linaro org", "kernel-build-reports@lists.linaro.org"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "kernelci" ]; then
        echo "Sending results to kernelci folks"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "delay": 0}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "format": ["txt"], "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "format": ["txt"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline-uefi", "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "format": ["txt"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline-fastboot", "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "format": ["txt"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-vivid", "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-uvc", "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-drm-kms", "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "cros-ec", "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "sleep", "send_to": ["gtucker@collabora.com", "mgalka@collabora.com", "alexandra.pereira@collabora.com", "dan.rue@linaro.org", "matthew.hart@linaro.org", "broonie@kernel.org", "kernelci@baylibre.com", "anders.roxell@linaro.org"], "format": ["txt"], "delay": 2700}' ${API}/send
    else
        # Private Mailing List
        echo "Sending results to private mailing list"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["fellows@kernelci.org"], "format": ["txt", "html"], "delay": 12600}' ${API}/send
    fi
    # Send stable* reports to stable list
    if [[ "$TREE_NAME" == "stable"* ]]; then
        echo "Sending stable results to stable pubic mailing list"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["stable@vger.kernel.org"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["stable@vger.kernel.org"], "format": ["txt"], "delay": 12600}' ${API}/send
        if [ "$BRANCH" == "linux-4.4.y" ] || [ "$BRANCH" == "linux-4.9.y" ]; then
            curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["tom.gall@linaro.org", "sumit.semwal@linaro.org", "amit.pundir@linaro.org", "arnd.bergmann@linaro.org", "anmar.oueja@linaro.org"], "format": ["txt"], "delay": 10}' ${API}/send
            curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "boot_report": 1, "send_to": ["tom.gall@linaro.org", "sumit.semwal@linaro.org", "amit.pundir@linaro.org", "arnd.bergmann@linaro.org", "anmar.oueja@linaro.org"], "format": ["txt"], "delay": 12600}' ${API}/send
        fi
    fi
fi
