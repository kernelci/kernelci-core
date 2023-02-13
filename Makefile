# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019, 2023 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2020, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

test:
	python3 -m pytest tests

pylint:
	pylint --reports=y \
		kci \
		kernelci.cli \
		kernelci.config.api \
		kernelci.storage \
		tests
