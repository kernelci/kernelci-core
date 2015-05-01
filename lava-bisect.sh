#!/bin/bash

cd $WORKSPACE/$TREE_NAME
rm -rf _install_ build/
git clean -df
make distclean
build.py -i -p production -c $1
if [ $? -ne 0 ]; then
	echo "Failed to build, skipping..."
	exit 125
fi

cd $WORKSPACE/local/lava-ci/
python lava-kernel-ci-job-creator.py http://storage.kernelci.org/$TREE_NAME/$GIT_DESCRIBE/$ARCH-$1/ --plans boot --targets $2
python lava-job-runner.py $3 $4 $5 --stream /anonymous/kernel-ci/ --poll kernel-ci.json --bisect
if [ $? -ne 0 ]; then
	echo "Boot failed, git bisect bad"
	exit 1
else
	echo "Boot passed, git bisect good"
	exit 0
fi
