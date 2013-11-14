#!/bin/bash
# Usage ./run.sh

# $WORKSPACE - Jenkins Workspace Variable
# $BUILD_URL - Jenkins Build URL
# $GERRIT_* - Gerrit Jenkins Plugin Variables
LAVA_SERVER="127.0.0.1"
LAVA_SERVER_EXTERNAL="lavabot.validation.linaro.org"
LAVA_USER="lava-bot"
LDT_PATH="/home/instance-manager/lava-deployment-tool"
INSTANCE_PATH="/srv/lava/instances"
INSTANCE_NAME="lavabot"
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
        echo "* Your patch set $GERRIT_PATCHSET_REVISION has triggered automated functional testing." >> $WORKSPACE/message
        echo "* Please do not merge this commit until after I have reviewed the results with you." >> $WORKSPACE/message
	echo "* $BUILD_URL" >> $WORKSPACE/message
	echo "* http://$LAVA_SERVER_EXTERNAL" >> $WORKSPACE/message
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

function submit_test ()
{
	JOB_ID=$(lava-tool submit-job http://$LAVA_USER@$LAVA_SERVER/RPC2/ $1 | grep -o '[0-9]*' | head -1)
}

function get_test_result ()
{
	while lava-tool job-status http://$LAVA_USER@$LAVA_SERVER/RPC2/ $JOB_ID | grep -e 'Running' -e 'Submitted'
	do
		sleep 120
	done

	if lava-tool job-status http://$LAVA_USER@$LAVA_SERVER/RPC2/ $JOB_ID | grep Complete
	then
		echo "* $1 Test Passed: http://$LAVA_SERVER_EXTERNAL/scheduler/job/$JOB_ID" >> $WORKSPACE/results
	else
		echo "* $1 Test Failed: http://$LAVA_SERVER_EXTERNAL/scheduler/job/$JOB_ID" >> $WORKSPACE/results
	fi
}

function boot_and_test_master_device ()
{
	submit_test $WORKSPACE/lava-ci/jobs/master-smoke.json
	get_test_result "Master Device"
}

function boot_and_test_bootloader_device ()
{
	submit_test $WORKSPACE/lava-ci/jobs/bootloader-smoke.json
	get_test_result "Bootloader Device"
}

function boot_and_test_kvm_device ()
{
	submit_test $WORKSPACE/lava-ci/jobs/kvm-smoke.json
	get_test_result "KVM Device"
}

function boot_and_test_fastmodel_device ()
{
	submit_test $WORKSPACE/lava-ci/jobs/fastmodel-smoke.json
	get_test_result "Fastmodel Device"
}

function upgrade_lava ()
{
	cd $LDT_PATH
	sudo git pull
	sudo SKIP_ROOT_CHECK=yes ./lava-deployment-tool setup -n
	sudo SKIP_ROOT_CHECK=yes ./lava-deployment-tool upgrade $INSTANCE_NAME
}

function is_server_running ()
{
	curl http://127.0.0.1 | grep lava
}

function checkout_and_rebase ()
{
	cd $WORKSPACE
	git clone $GIT_SERVER/$GERRIT_PROJECT
	cd $LAVA_PROJECT
	git fetch $GERRIT_SERVER/$GERRIT_PROJECT $GERRIT_REFSPEC && git checkout FETCH_HEAD && git rebase master
}

function install_local_project ()
{
	cd $INSTANCE_PATH/$INSTANCE_NAME/code/current
	sudo ln -s $WORKSPACE/$LAVA_PROJECT local/
	sudo ./bin/buildout
}

function restart_server ()
{
	sudo stop lava-instance LAVA_INSTANCE=$INSTANCE_NAME
	sudo service apache2 restart
	sudo start lava-instance LAVA_INSTANCE=$INSTANCE_NAME
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

function clean_up ()
{
	cd $INSTANCE_PATH/$INSTANCE_NAME/code/current/local
	if ls | grep $LAVA_PROJECT
	then
		sudo rm $LAVA_PROJECT
	fi
}

notify_committer
check_step clean_up
check_step upgrade_lava
check_step is_server_running
check_step checkout_and_rebase
check_step install_local_project
check_step restart_server
check_step is_server_running
check_step boot_and_test_master_device
check_step boot_and_test_bootloader_device
check_step boot_and_test_kvm_device
check_step boot_and_test_fastmodel_device
check_step clean_up
publish_results
