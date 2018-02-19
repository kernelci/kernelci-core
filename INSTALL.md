# Install

All installation docs are now on the dedicated [kernelci-backend-config](https://github.com/kernelci/kernelci-backend-config/blob/master/INSTALL.md)

# Configuration/Administration

## Main configurations files
/etc/linaro/kernelci-frontend.cfg
/etc/linaro/kernelci-backend.cfg
/etc/linaro/kernelci-celery.cfg

They are filled with informations from secrets.yml.

## Troubleshooting/Main log file
Celery and kernelci-backend services logs via syslog.
Nginx logs in /var/log/nginx
Uwsgi logs via syslog on Centos (and in /var/log/uwsgi on debian)

## Network access
Only the nginx service needs to be accessible from the external network. All other components needs to be available only from localhost.

## Data / backups
Only mongodb stores data and need to be backuped.

# Run the server

From the 'app/' folder, run:

  python server.py

## The Celery worker

To run external tasks, Celery is used. It will start automatically at boot
time. In the ansible playbook, there is the upstart configuration file to be
used.

It is possible to pass an external configuration file (key=value) using an
environment variable: CELERY_CONFIG_MODULE.

To manually run it, from the 'app/' folder, run:

  celery worker --autoscale=10,0 --app=taskqueue --loglevel=INFO

At the moment the Celery worker is based on redis.io: it needs to be installed
as well to make it work.

There is support for MongoDB, but is still experimental and has not been
tested yet with this application.

# Basic interactions

All operations now need a token or they will not be valid: the server will
reply with a 403 error.

In order to create the first token, use the master key set in the application
and create an admin token. Admin tokens can perform all actions: GET, POST,
DELETE and create new token as well.

For other application usage, you should create a superuser token.

## Create Token

To create a token at the beginning:

  curl -X POST -H "Content-Type: application/json" -H "Authorization: $MASTER_KEY" -d "{"email": "you@example.net", "admin": 1}" localhost:8888/token

The command will return the token created. Use it to create new tokens.
The master key should be used only the first time.

## GET

  curl localhost:8888/job
  curl localhost:8888/build
  curl localhost:8888/boot
  curl localhost:8888/count

  curl localhost:8888/job/$JOB_ID
  curl localhost:8888/build/$DEFCONF_ID

  curl localhost:8888/job?limit=40
  curl localhost:8888/job?limit=40&skip=20

## POST

POST requests work for:

  /job
  /boot

This command will tell the application to parse the directory located at
'stable/v3.12.14' and import everything there:

  curl -X POST -H "Content-Type: application/json" -H "Authorization: foo" -d '{"job": "stable", "kernel": "v3.12.14"}' localhost:8888/job

The content of the `Authorization` is not important at the moment. All requests
without that header will be discarded though.

## DELETE

  curl -X DELETE -H "Authorization: foo" localhost:8888/job/job-id
