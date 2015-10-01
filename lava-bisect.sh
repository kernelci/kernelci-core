#!/bin/bash

cd $WORKSPACE/$TREE_NAME
rm -rf _install_ build/
git clean -df
make distclean
export GIT_DESCRIBE=$(git describe)
build.py -i -p production -c $1
if [ $? -ne 0 ]; then
	echo "Failed to build, skipping..."
	exit 125
fi

cd $WORKSPACE/local/lava-ci/
python lava-kernel-ci-job-creator.py http://storage.kernelci.org/$TREE_NAME/$GIT_DESCRIBE/$ARCH-$2/ --plans $3 --targets $4
python lava-job-runner.py --username $5 --token $6 --server $7 --stream /anonymous/kernel-ci/ --poll kernel-ci.json --bisect
if [ $? -ne 0 ]; then
	echo "Boot failed, git bisect bad"
	exit 1
else
	echo "Boot passed, git bisect good"
	exit 0
fi
