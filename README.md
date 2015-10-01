# LAVA-CI
## Configuration using $HOME/.lavarc

```
$ cat $HOME/.lavarc
[linaro]
server: http://lava-server/RPC2
username: <user>
token: <auth-token>
```

## Usage instructions for lava-stream-job:
The only required option is "--job", everything else can be configured through either $HOME/.lavarc or the environment.
```
./lava-stream-log.py [-h] [--username <lava username>] [--token <lava token>] [--server <http://lava-server/RPC2>] --job <lava job id>
```
Examples:
```
./lava-stream-log.py --username <lava username> --token <lava token> --server <http://lava-server/RPC2> --job <lava job id>
./lava-stream-log.py --section linaro --job <lava job id>

# Override config settings on the command line
./lava-stream-log.py --section linaro --token <lava token> --job <lava job id>
```

## Usage instructions for lava-kernel-ci-job-creator.py:
This command line tool will create LAVA boot test jobs for various architectures, and platforms.
```
./lava-kernel-ci-job-creator.py [-h] --plans PLANS [PLANS ...] [--arch ARCH] [--targets TARGETS [TARGETS ...]] url
```
Examples:
```
# Create all LAVA boot test jobs for a specific build.
./lava-kernel-ci-job-creator.py http://storage.kernelci.org/next/next-20150114/ --plans boot

# Create only LAVA boot test jobs for a specific build and architecture.
./lava-kernel-ci-job-creator.py http://storage.kernelci.org/next/next-20150114/ --plans boot --arch arm

# Create only LAVA boot test jobs for a specific build and targets.
./lava-kernel-ci-job-creator.py http://storage.kernelci.org/next/next-20150114/ --plans boot --targets mustang odroid-xu3
```
The generated jobs can be found in the jobs directory.


## Usage instructions for lava-job-runner.py:
This command line tool will submit all LAVA jobs in the current working directory.
```
./lava-job-runner.py [-h] [--stream STREAM] [--repo REPO] [--poll POLL]
```
Examples:

```
# Submit all LAVA jobs in the current working directory to a specific server, and bundle stream.
./lava-job-runner.py --username <lava username> --token <lava token> --server <http://lava-server/RPC2> --stream /anonymous/mybundle/

# Submit and poll all LAVA jobs in the current working directory to a specific server, bundle stream.
./lava-job-runner.py --username <lava username> --token <lava token> --server <http://lava-server/RPC2> --stream /anonymous/mybundle/ --boot results/kernel-ci.json

# Submit and poll all LAVA jobs in the current working directory to a specific server, bundle stream. Once the results have been obtained, store the results in a JSON encoded file for use later with the dashboard reporting tool.
./lava-job-runner.py <username> <lava token> http://my.lavaserver.com/RPC2/ --stream /anonymous/mybundle/ --boot results/kernel-ci.json --lab <lab-id> --api http://api.kernelci.org --token <dashboard token>
```

## Usage instructions for lava-report.py:
This command line tool will report the results of LAVA jobs given a JSON results file.
```
./lava-report.py [-h] [--boot BOOT] [--lab LAB] [--api API] [--token TOKEN] [--email EMAIL]
```
Examples:

```
# Report all results from a given JSON result file.
./lava-report.py --boot results/kernel-ci.json --lab <lab-id> --api http://api.kernelci.org --token <dashboard token>
```
The generated results can be found in the results directory.
