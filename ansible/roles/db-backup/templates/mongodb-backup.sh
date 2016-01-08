#!/bin/bash

MONGODUMP_PATH=`which mongodump`
S3CMD=`which s3cmd`
TIMESTAMP=`date --utc +%FT%TZ`
S3_BUCKET_NAME="{{ bucket_name }}"
S3_BUCKET_PATH="{{ bucket_backup_dir }}"

echo "Dumping mongodb database..."
$MONGODUMP_PATH --quiet -d kernel-ci --dumpDbUsersAndRoles -o /tmp/mongodump > /dev/null

echo "Creating compressed archive..."
mv /tmp/mongodump /tmp/mongodump-$TIMESTAMP
tar cfP /tmp/mongodump-$TIMESTAMP.tar /tmp/mongodump-$TIMESTAMP/
xz -7 /tmp/mongodump-$TIMESTAMP.tar && rm -rf /tmp/mongodump-$TIMESTAMP/

# Upload to S3
# Need to configure s3cmd before.
$S3CMD put /tmp/mongodump-$TIMESTAMP.tar.xz s3://$S3_BUCKET_NAME/$S3_BUCKET_PATH/mongodump-$TIMESTAMP.tar.xz && rm -rf /tmp/mongodump-$TIMESTAMP.tar.xz
