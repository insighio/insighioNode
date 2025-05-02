#!/bin/sh

cd ./webui

# get git commit hash and update package.json version
GIT_COMMIT=$(git rev-parse --short HEAD)
echo "Updating package.json with commit hash $GIT_COMMIT"
jq --arg GIT_COMMIT "$GIT_COMMIT" '.version = $GIT_COMMIT' package.json > tmp.json && mv tmp.json package.json
echo "Building webui"

npm run build
cd ./dist
FILES_TO_COPY=`find . | grep "gz$\|ico$\|png$"`
TARGET_PATH="../../insighioNode/www"

echo "cleaning up old files"
rm -rf $TARGET_PATH/*

echo "Preparing target folder"
mkdir -p $TARGET_PATH/assets

for FILE in $FILES_TO_COPY
do
    if [ -f $FILE ]; then
        echo "Copying $FILE"
        cp $FILE $TARGET_PATH/$FILE
    fi
done

cd ..
echo "Done"