#!/usr/bin/python
# Usage ./lava-projectci.py <pep-ignore-options>
import sys
import os
import subprocess

jenkins_env = ['WORKSPACE', 'BUILD_URL', 'GERRIT_PROJECT', 'GERRIT_REFSPEC', 'GERRIT_PATCHSET_REVISION', 'GERRIT_CHANGE_OWNER_NAME']
git_server = 'http://git.linaro.org/git'
gerrit_server = 'review.linaro.org'
result_message_list = []
debug = False

def dummy_env():
    os.environ['WORKSPACE'] = '/home/lava-bot/workspace/lava-project-pep8-compliance'
    os.environ['BUILD_URL'] = 'https://ci.linaro.org/jenkins/job/lava-project-pep8-compliance/686/'
    os.environ['GERRIT_PROJECT'] = 'lava/lava-dispatcher'
    os.environ['GERRIT_REFSPEC'] = 'refs/changes/19/1419/4'
    os.environ['GERRIT_PATCHSET_REVISION'] = '9a8a1e81ada025d5601c11fc60db1f3bc6294414'
    os.environ['GERRIT_CHANGE_OWNER_NAME'] = 'Tyler Baker'

def check_enviroment():
    is_env_set = True
    for env_variable in jenkins_env:
        if env_variable in os.environ:
            print '%s is defined as %s' % (env_variable, os.environ[env_variable])
        else:
            print '%s is not defined' % env_variable
            is_env_set = False
    return is_env_set

def add_gerrit_comment(message, review):
    cmd = r'ssh %s gerrit review --code-review %s -m "\"%s"\" %s' % (gerrit_server, review, message, os.environ['GERRIT_PATCHSET_REVISION'])
    if debug:
        print cmd
    try:
        output = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        message = '* SETUP STEP: [FAILED]: %s' % cmd
        result_message_list.append(message)
        print e.output
        publish_result()
        exit(1)

def notify_committer():
    message_list= []
    message_list.append('* Hello %s' % os.environ['GERRIT_CHANGE_OWNER_NAME'])
    message_list.append('* Your patch set %s has triggered automated testing.' % os.environ['GERRIT_PATCHSET_REVISION'])
    message_list.append('* Please do not merge this commit until after I have reviewed the results with you.')
    message_list.append('* %s' % os.environ['BUILD_URL'])
    message = '\n'.join(message_list)
    if debug:
        print message
    add_gerrit_comment(message, 0)

def publish_result(result=None):
    test_results = os.environ['BUILD_URL'] + 'console'
    result_message_list.append('* TEST RESULTS: %s' % test_results)
    result_message = '\n'.join(result_message_list)
    if result is None:
        add_gerrit_comment(result_message, 0)
    elif result:
        add_gerrit_comment(result_message, +1)
    else:
        add_gerrit_comment(result_message, -1)


def checkout_and_rebase():
    os.chdir(os.environ['WORKSPACE'])
    cmd = 'git clone %s/%s' % (git_server, os.environ['GERRIT_PROJECT'])
    if debug:
        print cmd
    try:
        output = subprocess.check_output(cmd, shell=True)
        if debug:
            print output
        message = '* SETUP STEP: [PASSED]: %s' % cmd
        result_message_list.append(message)
    except subprocess.CalledProcessError as e:
        message = '* SETUP STEP: [FAILED]: %s' % cmd
        result_message_list.append(message)
        publish_result()
        exit(1)

    os.chdir(os.environ['GERRIT_PROJECT'].split('/')[1])
    cmd = 'git fetch ssh://%s/%s %s && git checkout FETCH_HEAD && git rebase master' % (gerrit_server, os.environ['GERRIT_PROJECT'], os.environ['GERRIT_REFSPEC'])
    if debug:
        print cmd
    try:
        output = subprocess.check_output(cmd, shell=True)
        message = '* SETUP STEP: [PASSED]: %s' % cmd
        result_message_list.append(message)
    except subprocess.CalledProcessError as e:
        message = '* SETUP STEP: [FAILED]: %s' % cmd
        result_message_list.append(message)
        print e.output
        publish_result()
        exit(1)

def pep8_check(ignore_options):
    os.chdir(os.environ['WORKSPACE'])
    os.chdir(os.environ['GERRIT_PROJECT'].split('/')[1])
    cmd = 'pep8 --ignore %s .' % ignore_options
    try:
        output = subprocess.check_output(cmd, shell=True)
        if debug:
            print output
        message = '* PEP8 CHECK: [PASSED]: %s' % cmd
        result_message_list.append(message)
    except subprocess.CalledProcessError as e:
        message_list = []
        message_list.append('* PEP8 CHECK: [FAILED]: %s' % cmd)
        message_list.append('* PEP8 CHECK: [OUTPUT]:')
        for line in e.output.splitlines():
            message_list.append('* ' + line)
        message = '\n'.join(message_list)
        result_message_list.append(message)
        cmd_verbose = 'pep8 --ignore %s --show-source --show-pep8 .' % ignore_options
        subprocess.call(cmd_verbose, shell=True)
        publish_result(False)
        exit(1)

def run_unit_tests():
    lava_project = os.environ['GERRIT_PROJECT'].split('/')[1]
    os.chdir(os.environ['WORKSPACE'])
    os.chdir(lava_project)
    if lava_project == 'lava-server':
        cmd = './ci-run'
    elif lava_project == 'lava-dispatcher':
        cmd = './ci-run'
    elif lava_project == 'lava-tool':
        cmd = './ci-build'
    else:
        cmd = './ci-run'
    try:
        output = subprocess.check_output(cmd, shell=True)
        if debug:
            print output
        message = '* UNIT TESTS: [PASSED]: %s' % cmd
        result_message_list.append(message)
    except subprocess.CalledProcessError as e:
        message = '* UNIT TEST: [FAILED]: %s' % cmd
        result_message_list.append(message)
        drop_test_db()
        print e.output
        publish_result(False)
        exit(1)

def drop_test_db():
    lava_project = os.environ['GERRIT_PROJECT'].split('/')[1]
    if lava_project == 'lava-server':
        cmd = "dropdb 'test_lava-lavabot'"
        try:
            output = subprocess.check_output(cmd, shell=True)
            if debug:
                print output
            message = '* TEAR DOWN STEP: [PASSED]: %s' % cmd
            result_message_list.append(message)
        except subprocess.CalledProcessError as e:
            message = '* TEAR DOWN STEP: [FAILED]: %s' % cmd
            result_message_list.append(message)
            print e.output
            publish_result(False)
            exit(1)

def init():
    result_message_list.append('* LAVABOT: [RESULTS]: Automated test results for patch set: %s' % os.environ['GERRIT_PATCHSET_REVISION'])

def main(ignore_options):
    # Uncomment the following to run locally
    #debug = True
    #dummy_env()
    if check_enviroment():
        print 'All required environment variables have been set...continuing'
    else:
        print 'All required environment variables have not been set...exiting'
        exit(1)
    notify_committer()
    init()
    checkout_and_rebase()
    pep8_check(ignore_options)
    run_unit_tests()
    publish_result(True)
    exit(0)

if __name__ == '__main__':
    main(sys.argv[1])