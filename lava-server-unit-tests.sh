#!/bin/bash
# Usage ./run.sh <pep8 ignore options>

# $WORKSPACE - Jenkins Workspace Variable
# $BUILD_URL - Jenkins Build URL
# $GERRIT_* - Gerrit Jenkins Plugin Variables
GIT_SERVER="http://staging.git.linaro.org/git"
GERRIT_SERVER="ssh://lava-bot@staging.review.linaro.org:29418"
LAVA_PROJECT=$(echo $GERRIT_PROJECT | cut -c 6-)

function add_gerrit_comment()
{
	ssh staging.review.linaro.org gerrit review --code-review $1 -m "\"$2"\" $3
}

function notify_committer ()
{
	echo "* Hello $GERRIT_CHANGE_OWNER_NAME" >> $WORKSPACE/message
        echo "* Your patch set $GERRIT_PATCHSET_REVISION has triggered unit testing." >> $WORKSPACE/message
        echo "* Please do not merge this commit until after I have reviewed the results with you." >> $WORKSPACE/message
	echo "* $BUILD_URL" >> $WORKSPACE/message
	GREETING_MESSAGE=$(cat $WORKSPACE/message)
	add_gerrit_comment 0 "$GREETING_MESSAGE" $GERRIT_PATCHSET_REVISION
	echo "* Test results for patch set: $GERRIT_PATCHSET_REVISION" >> $WORKSPACE/results
}

function check_step ()
{
	"$@"
	if [ $? -ne "0" ]
	then
		echo "* Step Failed: $@" >> $WORKSPACE/results
		publish_results
		exit 1
	else
		echo "* Step Passed: $@" >> $WORKSPACE/results
	fi
}

function lava_server_unit_tests ()
{
	cd $WORKSPACE/$LAVA_PROJECT

	./ci-run
}

function checkout_and_rebase ()
{
	cd $WORKSPACE
	git clone $GIT_SERVER/$GERRIT_PROJECT
	cd $LAVA_PROJECT
	git fetch $GERRIT_SERVER/$GERRIT_PROJECT $GERRIT_REFSPEC && git checkout FETCH_HEAD && git rebase master
}

function publish_results ()
{
	echo "* $BUILD_URL" >> $WORKSPACE/results
	RESULTS_MESSAGE=$(cat $WORKSPACE/results)
	echo "$RESULTS_MESSAGE"
	if grep 'Failed' $WORKSPACE/results
	then
		add_gerrit_comment -1 "$RESULTS_MESSAGE" $GERRIT_PATCHSET_REVISION
	else
		add_gerrit_comment +1 "$RESULTS_MESSAGE" $GERRIT_PATCHSET_REVISION
	fi
}

notify_committer
check_step checkout_and_rebase
check_step lava_server_unit_tests
publish_results
