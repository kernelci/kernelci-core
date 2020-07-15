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

if [[ -z $EMAIL_AUTH_TOKEN ]]; then
  echo "EMAIL_AUTH_TOKEN not set.  Not publishing."
  exit 1
fi

if [[ -z $API ]]; then
  echo "API not set.  Not publishing."
  exit 1
fi

    echo "Build has now finished, reporting result to dashboard."
    curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'"}' ${API}/job

    if [ "$EMAIL" != "true" ]; then
        echo "Not sending emails because EMAIL was false"
        exit 0
    elif [ "$TREE_NAME" == "agross" ]; then
        echo "Sending results to Andy Gross"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["agross@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["agross@kernel.org", "fellows@kernelci.org"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "alex" ]; then
        echo "Sending results to Alex Bennee"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["alex.bennee@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["alex.bennee@linaro.org", "fellows@kernelci.org"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "amlogic" ]; then
        echo "Sending results to Kevin Hilman"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["khilman@kernel.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
    elif [ "$TREE_NAME" == "android" ]; then
        echo "Sending results to Android maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["tom.gall@linaro.org", "sumit.semwal@linaro.org", "amit.pundir@linaro.org", "arnd.bergmann@linaro.org", "anmar.oueja@linaro.org", "kernel-team+kernelci@android.com", "gregkh@google.com", "fellows@kernelci.org"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["tom.gall@linaro.org", "sumit.semwal@linaro.org", "amit.pundir@linaro.org", "arnd.bergmann@linaro.org", "anmar.oueja@linaro.org", "kernel-team+kernelci@android.com", "gregkh@google.com", "fellows@kernelci.org"], "format": ["txt"], "delay": 12600}' ${API}/send
	if [ "$BRANCH" == "android-3.18" ]; then
            curl -XPOST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["lee.jones@linaro.org"], "delay": 60}' ${API}/send
	fi
    elif [ "$TREE_NAME" == "ardb" ]; then
        echo "Sending results to Ard Biesheuvel"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["ardb@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["ardb@kernel.org", "fellows@kernelci.org"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "arm64" ]; then
        echo "Sending results for the arm64 tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["will@kernel.org", "catalin.marinas@arm.com", "linux-arm-kernel@lists.infradead.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["will@kernel.org", "catalin.marinas@arm.com", "linux-arm-kernel@lists.infradead.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "arnd" ]; then
        echo "Sending results to Arnd Bergmann"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["arnd@arndb.de", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
    elif [ "$TREE_NAME" == "broonie-regmap" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["broonie@kernel.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["broonie@kernel.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "broonie-regulator" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["broonie@kernel.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["broonie@kernel.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "broonie-sound" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["broonie@kernel.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["broonie@kernel.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "broonie-spi" ]; then
        echo "Sending results to Mark Brown"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["broonie@kernel.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["broonie@kernel.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "chrome-platform" ]; then
        echo "Sending results for Chrome Platform tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io", "enric.balletbo@collabora.com", "bleung@chromium.org", "groeck@chromium.org", "fabien.lahoudere@collabora.com"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io", "enric.balletbo@collabora.com", "bleung@chromium.org", "groeck@chromium.org", "fabien.lahoudere@collabora.com"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "cros-ec", "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io", "enric.balletbo@collabora.com", "bleung@chromium.org", "groeck@chromium.org", "fabien.lahoudere@collabora.com"], "format": ["txt"], "delay": 5400}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "sleep", "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io", "enric.balletbo@collabora.com", "bleung@chromium.org", "groeck@chromium.org", "fabien.lahoudere@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
    elif [ "$TREE_NAME" == "clk" ]; then
        echo "Sending results for CLK tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["sboyd+clkci@kernel.org", "mturquette+clkci@baylibre.com", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["sboyd+clkci@kernel.org", "mturquette+clkci@baylibre.com", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 1800}' ${API}/send
    elif [ "$TREE_NAME" == "efi" ]; then
        echo "Sending results to EFI maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["ardb@kernel.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["ardb@kernel.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "evalenti" ]; then
        echo "Sending results to Eduardo Valentin"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["edubezval@gmail.com", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["edubezval@gmail.com", "fellows@kernelci.org"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "gtucker" ]; then
        echo "Sending results to Guillaume"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["guillaume.tucker@collabora.com"], "delay": 0}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-vivid", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-uvc", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-kms-exynos", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-kms-rockchip", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-kms-tegra", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-gpu-panfrost", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "cros-ec", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "sleep", "send_to": ["guillaume.tucker@collabora.com"], "format": ["txt"], "delay": 3600}' ${API}/send
    elif [ "$TREE_NAME" == "kernelci" ]; then
        echo "Sending results to kernelci folks"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["kernelci-results-staging@groups.io"], "delay": 0}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline-nfs", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline-fastboot", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 1800}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-vivid", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-uvc", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-kms-exynos", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-kms-rockchip", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-kms-tegra", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "igt-gpu-panfrost", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "cros-ec", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "sleep", "send_to": ["kernelci-results-staging@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "khilman" ]; then
        echo "Sending results to Kevin Hilman"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["khilman@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
    elif [ "$TREE_NAME" == "krzysztof" ]; then
        echo "Sending results to Krzysztof Kozlowski"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["krzk@kernel.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["krzk@kernel.org", "fellows@kernelci.org"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "lee" ]; then
        echo "Sending results for Lee's tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["lee.jones@linaro.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["lee.jones@linaro.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "linusw" ]; then
        echo "Sending results to linux-gpio"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["linux-gpio@vger.kernel.org", "fellows@kernelci.org"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["linux-gpio@vger.kernel.org", "fellows@kernelci.org"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "mainline" ]; then
        echo "Sending results for mainline"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "media" ]; then
        echo "Sending results for media tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-vivid", "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 5400}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "v4l2-compliance-uvc", "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 5400}' ${API}/send
    elif [ "$TREE_NAME" == "net-next" ]; then
        echo "Sending results for net-next tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
    elif [ "$TREE_NAME" == "next" ]; then
        echo "Sending results to Linux Next"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["linux-next@vger.kernel.org"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["linux-next@vger.kernel.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
        echo "Sending build results to clang-built-linux for master only"
        if [ "$BRANCH" == "master" ]; then
          curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["clang-built-linux@googlegroups.com"], "format": ["txt"], "delay": 10}' ${API}/send
        fi
    elif [ "$TREE_NAME" == "omap" ]; then
        echo "Sending results to Tony Lindgren"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["tony@atomide.com", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["tony@atomide.com", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "pm" ]; then
        echo "Sending results for the pm tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["rafael@kernel.org", "linux-pm@vger.kernel.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["rafael@kernel.org", "linux-pm@vger.kernel.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "sleep", "send_to": ["rafael@kernel.org", "linux-pm@vger.kernel.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 3600}' ${API}/send
    elif [ "$TREE_NAME" == "pmwg" ]; then
        echo "Sending results to PMWG maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["private-pmwg@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["daniel.lezcano@linaro.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["private-pmwg@lists.linaro.org", "daniel.lezcano@linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "qcom-lt" ]; then
        echo "Sending results to QCOM-LT team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["qcomlt-patches@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["qcomlt-patches@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "renesas" ]; then
        echo "Sending results to Simon Horman"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["horms@verge.net.au", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["horms@verge.net.au", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "rmk" ]; then
        echo "Sending results for SoC tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 1800}' ${API}/send
    elif [ "$TREE_NAME" == "rt-stable" ]; then
        echo "Sending results for net-next tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
    elif [ "$TREE_NAME" == "samsung" ]; then
        echo "Sending results to Samsung Team"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["krzk@kernel.org", "kgene.kim@samsung.com", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["krzk@kernel.org", "kgene.kim@samsung.com", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "sashal" ]; then
        echo "Sending results for sashal's tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["sashal@kernel.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["sashal@kernel.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "soc" ]; then
        echo "Sending results for SoC tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 1800}' ${API}/send
    elif [[ "$TREE_NAME" == "stable"* ]]; then
        echo "Sending stable results to stable pubic mailing list"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["stable@vger.kernel.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["stable@vger.kernel.org", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
        if [ "$BRANCH" == "linux-4.4.y" ] || [ "$BRANCH" == "linux-4.9.y" ]; then
            curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["tom.gall@linaro.org", "sumit.semwal@linaro.org", "amit.pundir@linaro.org", "arnd.bergmann@linaro.org", "anmar.oueja@linaro.org"], "format": ["txt"], "delay": 10}' ${API}/send
            curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["tom.gall@linaro.org", "sumit.semwal@linaro.org", "amit.pundir@linaro.org", "arnd.bergmann@linaro.org", "anmar.oueja@linaro.org"], "format": ["txt"], "delay": 12600}' ${API}/send
        fi
    elif [ "$TREE_NAME" == "tegra" ]; then
        echo "Sending results to Tegra maintainers"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["thierry.reding@gmail.com", "jonathanh@nvidia.com", "kernelci-results@groups.io"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["thierry.reding@gmail.com", "jonathanh@nvidia.com", "kernelci-results@groups.io"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "thermal" ]; then
        echo "Sending results for the thermal tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["daniel.lezcano@linaro.org", "rui.zhang@intel.com", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["daniel.lezcano@linaro.org", "rui.zhang@intel.com", "kernel-build-reports@lists.linaro.org", "kernelci-results@groups.io"], "format": ["txt"], "delay": 2700}' ${API}/send
    elif [ "$TREE_NAME" == "ulfh" ]; then
        echo "Sending results to Ulf Hansson"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["ulf.hansson@linaro.org", "fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["ulf.hansson@linaro.org", "fellows@kernelci.org"], "format": ["txt"], "delay": 12600}' ${API}/send
    elif [ "$TREE_NAME" == "vireshk" ]; then
        echo "Sending results for vireshk's tree"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "format": ["txt"], "send_to": ["vireshk@kernel.org"], "delay": 60}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["vireshk@kernel.org"], "format": ["txt"], "delay": 2700}' ${API}/send

    else
        # Private Mailing List
        echo "Sending results to private mailing list"
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'", "build_report": 1, "send_to": ["fellows@kernelci.org"], "format": ["txt", "html"], "delay": 10}' ${API}/send
        curl -X POST -H "Authorization: $EMAIL_AUTH_TOKEN" -H "Content-Type: application/json" -d '{"job": "'$TREE_NAME'", "kernel": "'$GIT_DESCRIBE'", "git_branch": "'$BRANCH'",  "report_type": "test", "plan": "baseline", "send_to": ["fellows@kernelci.org"], "format": ["txt"], "delay": 12600}' ${API}/send
    fi
