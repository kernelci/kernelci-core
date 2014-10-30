#!/bin/bash

MONGODUMP_PATH=`which mongodump`
TIMESTAMP=`date +%F-%H%M`
S3_BUCKET_NAME="bucketname"
S3_BUCKET_PATH="mongodb-backups"

$MONGODUMP_PATH --host $HOST -o /tmp/mongodump

mv /tmp/mongodump /tmp/mongodump-$TIMESTAMP
tar cf /tmp/mongodump-$TIMESTAMP.tar /tmp/mongodump-$TIMESTAMP

# Upload to S3
# Need to configure s3cmd before.
s3cmd put /tmp/mongodump-$TIMESTAMP.tar s3://$S3_BUCKET_NAME/$S3_BUCKET_PATH/mongodump-$TIMESTAMP.tar
