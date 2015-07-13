Configuration using $HOME/.lavarc

```
$ cat $HOME/.lavarc
[linaro]
server: http://lava-server/RPC2
username: <user>
token: <auth-token>
```

Usage instructions for lava-stream-job:
The only required option is "--job", everything else can be configured through either $HOME/.lavarc or the environment.
```
./lava-stream-log.py --username <lava username> --token <lava token> --server <http://lava-server/RPC2> --job <lava job id>
./lava-stream-log.py --section linaro --job <lava job id>

# Override config settings on the command line
./lava-stream-log.py --section linaro --token <lava token> --job <lava job id>
```
